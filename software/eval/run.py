"""Run the full check-in loop on spare ports: the real hub (in this process), the real agent
(a child process), and the real voice service class with a scripted engine in place of the
microphone and speaker. Events and presence go in as bus messages, the way the box and the
presence service send them.
"""

import asyncio
import json
import os
import sys
import time
from pathlib import Path

from websockets.asyncio.client import connect

from software.eval.cases import event_msg
from software.eval.score import judge
from software.hub.bus import running_hub
from software.voice.service import VoiceService

REPO = Path(__file__).resolve().parents[2]
# Port 9 (discard) refuses connections, so a hosted failure goes straight to the fixed script
# and the eval never loads the Ollama model the live loop uses.
NO_OLLAMA = "http://127.0.0.1:9/v1"
# The agent must not call or text anyone from the eval.
DROP_ENV = ("TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "TWILIO_FROM", "TWILIO_TO", "ELEVENLABS_API_KEY", "HUB_URL",
            # Settings the report does not record: the agent runs on its defaults.
            "AGENT_PLANNER_TIMEOUT_S", "AGENT_HEARD_GRACE_S", "AGENT_ASK_SCRIPT", "AGENT_LOCAL_MODEL")


class ScriptedEngine:
    """Stands in for the microphone: each listen waits the listen window, then returns the next line."""

    def __init__(self):
        self.transcripts = []

    def load(self, transcripts):
        self.transcripts = list(transcripts)

    def speak(self, text, script_id=None):
        pass

    def listen(self, seconds):
        time.sleep(seconds)
        return self.transcripts.pop(0) if self.transcripts else ""


class Recorder:
    """Every message the hub publishes, with the time the hub published it."""

    def __init__(self, raw_file, secret=None):
        self.secret = secret
        self.events = []
        self.raw = raw_file
        self.run_id = None
        self.changed = asyncio.Event()

    def __call__(self, msg):
        t = time.monotonic()
        self.events.append((t, dict(msg)))
        line = json.dumps({"run": self.run_id, "mono": round(t, 4), "msg": msg})
        self.raw.write((line.replace(self.secret, "[NVIDIA_API_KEY]") if self.secret else line) + "\n")
        self.raw.flush()
        self.changed.set()

    async def wait(self, since, predicate, timeout):
        deadline = time.monotonic() + timeout
        while not predicate(self.events[since:]):
            left = deadline - time.monotonic()
            if left <= 0:
                return False
            self.changed.clear()
            try:
                await asyncio.wait_for(self.changed.wait(), left)
            except TimeoutError:
                return False
        return True


def _decisions(events):
    return sum(1 for _, m in events if m.get("type") == "agent" and m.get("tool") == "log_decision"
               and m.get("text", "").startswith("Decision:"))


def _alarmed(events):
    return any(m.get("type") == "checkin" and m.get("state") == "alarm" for _, m in events)


def agent_env(key, listen_s, base=None):
    env = {k: v for k, v in (os.environ if base is None else base).items() if k not in DROP_ENV}
    env.pop("NVIDIA_API_KEY", None)
    if key:
        env["NVIDIA_API_KEY"] = key
    env.update(AGENT_LISTEN_S=str(listen_s), AGENT_OLLAMA_URL=NO_OLLAMA, PYTHONUNBUFFERED="1")
    return env


async def _pump(stream, path, secret):
    with open(path, "w") as f:
        async for line in stream:
            text = line.decode(errors="replace")
            f.write(text.replace(secret, "[NVIDIA_API_KEY]") if secret else text)
            f.flush()


def hosted_calls(r, key, case):
    """Upper estimate of hosted API calls in one run. With a key: every planner turn and failure,
    every Safety Guard check, one follow-up turn, and the hand-off note and why after an alarm."""
    if not key:
        return 0
    g = r["guard"]
    return (r["planner_calls"] + r["hosted_failures"] + g["safe"] + g["unsafe"] + g["unreachable"]
            + len(case.outcomes) + 2 * len(r["handoff_by"]))  # one follow-up turn per check-in


async def run_cases(cases, runs, out_dir, *, key=None, listen_s=1.0, max_rpm=None, run_timeout_s=240.0,
                    progress=lambda line: print(line, flush=True)):
    """Run every case `runs` times, one run at a time. Returns [(case, [judged run, ...]), ...].

    max_rpm paces the runs: after each run, wait until its estimated hosted calls average out
    to at most max_rpm per minute."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    results = []
    with open(out_dir / "raw.jsonl", "w") as raw, open(out_dir / "voice.log", "w") as voice_log:
        rec = Recorder(raw, key)
        async with running_hub("127.0.0.1", 0, 0) as hub:
            hub.listeners.append(rec)
            url = f"ws://127.0.0.1:{hub.ws_port}"
            env = agent_env(key, listen_s)
            env["HUB_URL"] = url
            proc = await asyncio.create_subprocess_exec(
                sys.executable, "-m", "software.agent", cwd=REPO, env=env,
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT)
            pump = asyncio.create_task(_pump(proc.stdout, out_dir / "agent.log", key))
            engine = ScriptedEngine()
            voice = VoiceService(engine, log=lambda line: print(line, file=voice_log, flush=True))
            voice_task = asyncio.create_task(voice.run(url))
            try:
                async with connect(url) as driver:
                    # Read what the hub sends the driver. A full read buffer stops pong replies and the hub drops us.
                    drain = asyncio.create_task(_drain(driver))
                    deadline = time.monotonic() + 30
                    while len(hub.clients) < 3:
                        if time.monotonic() > deadline or proc.returncode is not None:
                            raise RuntimeError("the agent or voice service did not connect to the eval hub")
                        await asyncio.sleep(0.1)
                    for case in cases:
                        judged = []
                        for n in range(1, runs + 1):
                            began = time.monotonic()
                            judged.append(await _one_run(case, n, driver, engine, rec, run_timeout_s, listen_s))
                            r = judged[-1]
                            r["hosted_calls_est"] = hosted_calls(r, key, case)
                            r["seconds"] = round(time.monotonic() - began, 2)
                            progress(f"{case.id} run {n}: {'right' if r['correct'] else 'WRONG'}"
                                     f"{'' if r['correct'] else ' ' + '; '.join(r['problems'])}"
                                     f" (first ask {r['first_ask_s']} s, alarm {r['alarm_s']} s,"
                                     f" fallbacks {r['fallbacks']})")
                            if max_rpm and key:
                                await asyncio.sleep(max(0.0, r["hosted_calls_est"] * 60 / max_rpm - r["seconds"]))
                        results.append((case, judged))
                    drain.cancel()
            finally:
                voice_task.cancel()
                if proc.returncode is None:
                    proc.terminate()
                    try:
                        await asyncio.wait_for(proc.wait(), 10)
                    except TimeoutError:
                        proc.kill()
                        await proc.wait()
                await pump
    return results


async def _drain(ws):
    async for _ in ws:
        pass


async def _one_run(case, n, driver, engine, rec, timeout, listen_s):
    rec.run_id = f"{case.id}#{n}"
    await driver.send(json.dumps({"type": "reset"}))
    engine.load(case.transcripts)
    start = len(rec.events)
    await driver.send(json.dumps({"type": "presence", "state": case.presence}))
    await driver.send(json.dumps(event_msg(case)))
    wanted = len(case.outcomes)
    if case.standup:
        if await rec.wait(start, _alarmed, timeout):
            await driver.send(json.dumps({"type": "presence", "state": "moving"}))
    finished = await rec.wait(start, lambda ev: _decisions(ev) >= wanted, timeout)
    result = judge(case, rec.events[start:])
    result["run"] = n
    # Cancels any recheck the planner scheduled, so it cannot start a check-in during the pause.
    await driver.send(json.dumps({"type": "reset"}))
    if not finished:
        await asyncio.sleep(listen_s + 1)  # a listen still in flight must not take the next run's first line
        result["correct"] = False
        result["problems"] = [f"timed out after {timeout:g} s", *result["problems"]]
    return result
