"""Judge-table rehearsal timing (issue #60): python -m software.eval.rehearsal --out DIR [--runs N]

The demo run (event, 3 asks with no answer, alarm, dashboard zoom, stand-up, "I'm okay") and the
"Help" fast path, end to end on spare ports: the real hub, the real agent process, and the real voice
service with the real voice engines (ElevenLabs or Kokoro speaks, Scribe or Moonshine listens).
Only the speaker and the microphone are stand-ins, so the rehearsal makes no sound during filming:
a line waits its audio's real length instead of playing, and a listen waits the listen window and
returns a recorded reply clip over real room noise.

Reads NVIDIA_API_KEY and ELEVENLABS_API_KEY from the environment. --cut-internet points every
outbound HTTP request of this process and the agent child at a closed local port. Nothing global changes.
"""

import argparse
import asyncio
import json
import os
import shlex
import signal
import sys
import threading
import time
import wave
from collections import deque
from contextlib import contextmanager
from pathlib import Path
from statistics import median

import numpy as np

from software.eval.cases import CASES
from software.eval.run import NO_OLLAMA, run_cases
from software.voice import engines

FIXTURES = Path(__file__).resolve().parents[1] / "voice" / "tests" / "fixtures"
# Reply clips: macOS `say` recordings from the voice tests. "" is silence: room noise only.
REPLY_CLIPS = {"I'm okay": "im_okay.wav", "Help": "help.wav"}
ROOM_NOISE = "room_noise_real_mic.wav"  # a real recording on the MacBook mic
REPLY_AT_S = 0.5  # a guess: the person starts answering half a second into the listen window
# software/web/dashboard/camera.js NEAR_FLIGHT_MS: the city -> home flight on an alarm or a help answer,
# from the city view a fresh dashboard shows after the event. From the world view the flight is longer.
ZOOM_S = 1.6
# The same closed port the eval uses for Ollama: every request through it is refused at once.
DEAD_PROXY = NO_OLLAMA.removesuffix("/v1")
CUT_ENV = {k: DEAD_PROXY for k in ("HTTPS_PROXY", "HTTP_PROXY", "ALL_PROXY", "https_proxy", "http_proxy", "all_proxy")}
CUT_ENV.update(NO_PROXY="127.0.0.1,localhost", no_proxy="127.0.0.1,localhost")  # the spare-port hub stays reachable
# A guess: well over one line's synthesis (ElevenLabs times out at 10 s, then Kokoro) plus its playback.
SETTLE_S = 60.0
FIT_S = 45.0  # the owner's target for the whole demo run
DEMO_CASES = ("standup", "help")


def load_wav(name):
    with wave.open(str(FIXTURES / name)) as w:
        return np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768


class SoundDevice:
    """Stands in for engines.play, engines.record and engines.stop_audio.

    Each load() starts a new run. A line or a listen of a `say` from an earlier run (the voice worker
    can still be busy after a timed-out run) does not count its time or take the new run's reply."""

    def __init__(self, sleep=time.sleep):
        self.sleep = sleep
        self.gen = 0
        self.say_gen = None  # the run of the `say` being handled; None: no voice worker (unit tests)
        self.lock = threading.Lock()
        self.noise = load_wav(ROOM_NOISE)
        self.clips = {text: load_wav(name) for text, name in REPLY_CLIPS.items()}
        self.replies = deque()
        self.spoken = []  # (start, end) monotonic time of each line
        self.fallbacks = 0
        self.sink = None  # the voice engines' log file
        self.secret = None

    def load(self, transcripts):
        with self.lock:
            self.gen += 1
            self.replies = deque(transcripts)
            self.spoken = []
            self.fallbacks = 0

    def begin(self):
        """Called as the voice worker starts a `say`. It handles one at a time: the line, then its listen."""
        self.say_gen = self.gen

    def _this_run(self):
        return self.say_gen in (None, self.gen)

    def play(self, audio, rate):
        start = time.monotonic()
        self.sleep(len(audio) / rate)
        with self.lock:
            if self._this_run():
                self.spoken.append((start, time.monotonic()))

    def record(self, seconds, log):
        self.sleep(seconds)
        n = int(seconds * engines.SAMPLE_RATE)
        window = np.resize(self.noise, n).copy()
        with self.lock:
            text = self.replies.popleft() if self.replies and self._this_run() else ""
        if text:
            clip = self.clips[text]
            at = int(REPLY_AT_S * engines.SAMPLE_RATE)
            window[at:at + len(clip)] += clip[: max(0, n - at)]
        return window

    def stop(self):
        pass

    def log(self, line):
        with self.lock:
            if line.startswith("FALLBACK") and self._this_run():
                self.fallbacks += 1
        if self.sink:
            self.sink.write((line.replace(self.secret, "[ELEVENLABS_API_KEY]") if self.secret else line) + "\n")
            self.sink.flush()


@contextmanager
def installed(device):
    saved = engines.play, engines.record, engines.stop_audio
    engines.play, engines.record, engines.stop_audio = device.play, device.record, device.stop
    try:
        yield
    finally:
        engines.play, engines.record, engines.stop_audio = saved


@contextmanager
def internet_cut(on):
    saved = {k: os.environ.get(k) for k in CUT_ENV}
    if on:
        os.environ.update(CUT_ENV)
    try:
        yield
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


class TableEngine:
    """The real voice engine with the stand-in device; load() takes the case's replies."""

    def __init__(self, voice, device):
        self.voice = voice
        self.device = device

    def load(self, transcripts):
        self.device.load(transcripts)

    def speak(self, text, script_id=None):
        self.device.begin()
        self.voice.speak(text, script_id)

    def listen(self, seconds):
        return self.voice.listen(seconds)


def _first(events, pred):
    return next((t for t, m in events if pred(m)), None)


def _checkin(state):
    return lambda m: m.get("type") == "checkin" and m.get("state") == state


def step_times(events, spoken):
    """Seconds from the event on the bus to each demo step. Bus times are the hub's publish times;
    first and last word come from the device, since speaking time is not on the bus."""
    t0 = _first(events, lambda m: m.get("type") in ("quake", "fall_hint", "help_gesture"))
    zoom = _first(events, lambda m: (m.get("type") in ("heard", "checkin") and m.get("answer", m.get("state")) == "help")
                  or _checkin("alarm")(m))
    lines = [(a, b) for a, b in spoken if t0 is not None and a >= t0]

    def since(t):
        return None if t is None or t0 is None else round(t - t0, 3)

    return {
        "first_ask_s": since(_first(events, _checkin("asking"))),
        "first_word_s": since(lines[0][0] if lines else None),
        "alarm_s": since(_first(events, _checkin("alarm"))),
        "zoom_landed_s": None if zoom is None else round(since(zoom) + ZOOM_S, 3),
        "standdown_s": since(_first(events, _checkin("clear"))),
        "last_word_s": since(lines[-1][1] if lines else None),
        "lines_s": [[since(a), since(b)] for a, b in lines],
    }


def _says(events):
    return sum(1 for _, m in events if m.get("type") == "say")


def make_settle(device):
    async def settle(run_events):
        deadline = time.monotonic() + SETTLE_S
        while len(device.spoken) < _says(run_events()) and time.monotonic() < deadline:
            await asyncio.sleep(0.1)
        events = run_events()
        out = step_times(events, device.spoken)
        out.update(lines=len(device.spoken), voice_fallbacks=device.fallbacks,
                   voice_problem=None if len(device.spoken) >= _says(events)
                   else f"{_says(events) - len(device.spoken)} lines not spoken after {SETTLE_S:g} s")
        return out
    return settle


def build_voice(voice, eleven_key, device):
    offline = engines.OfflineEngine(device.log)
    return engines.ElevenLabsEngine(eleven_key, offline, device.log) if voice == "online" else offline


async def rehearse(cases, runs, out_dir, *, voice, eleven_key=None, cut_internet=False, listen_s=6.0, max_rpm=15.0,
                   run_timeout_s=240.0, progress=lambda line: print(line, flush=True), agent_settings=None):
    """agent_settings: env overrides for the agent child, on top of the eval's (tests only: the
    rehearsal times the agent on its defaults)."""
    if voice == "online" and not eleven_key:
        raise ValueError("online voice needs an ElevenLabs key")
    device = SoundDevice()
    device.secret = eleven_key
    key = os.environ.get("NVIDIA_API_KEY") or None
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    with open(Path(out_dir) / "engine.log", "w") as sink, internet_cut(cut_internet), installed(device):
        device.sink = sink
        engine = TableEngine(build_voice(voice, eleven_key, device), device)
        return await run_cases(cases, runs, out_dir, key=key, listen_s=listen_s,
                               max_rpm=None if cut_internet else max_rpm, run_timeout_s=run_timeout_s,
                               progress=progress, engine=engine, settle=make_settle(device),
                               agent_settings=agent_settings)


STEPS = (("first_ask_s", "First ask sent"), ("first_word_s", "First word spoken"), ("alarm_s", "Alarm on the bus"),
         ("zoom_landed_s", "Dashboard zoom landed"), ("standdown_s", "Stand-down (clear)"),
         ("last_word_s", "Last word spoken"))


def _stat(values, fn):
    values = [v for v in values if v is not None]
    return round(fn(values), 2) if values else None


def _s(v):
    return "-" if v is None else f"{v:g} s"


def _timed(r):
    """A run that finished and spoke every line. The others have no times, or times cut short."""
    return r.get("last_word_s") is not None and not r.get("voice_problem")


def summarize(case, runs):
    timed = [r for r in runs if _timed(r)]
    out = {"case": case.id, "title": case.title, "runs": len(runs), "timed": len(timed),
           "right": sum(r["correct"] for r in runs),
           "planner_calls": sum(r["planner_calls"] for r in runs),
           "hosted_failures": sum(r["hosted_failures"] for r in runs),
           "to_script": sum(r["to_script"] for r in runs),
           "voice_fallbacks": sum(r.get("voice_fallbacks", 0) for r in runs),
           "failed": [(r["run"], "; ".join(r["problems"] + ([r["voice_problem"]] if r.get("voice_problem") else [])))
                      for r in runs if not r["correct"] or r.get("voice_problem")]}
    for key, _ in STEPS:
        out[key] = (_stat([r.get(key) for r in timed], median), _stat([r.get(key) for r in timed], max))
    return out


def report(summaries, *, command, key, voice, cut_internet, listen_s, wall_s):
    rows = ["| Step (seconds from the event) | " + " | ".join(f"{s['case']} median / worst" for s in summaries) + " |",
            "|---|" + "---|" * len(summaries)]
    for k, label in STEPS:
        rows.append(f"| {label} | " + " | ".join(f"{_s(s[k][0])} / {_s(s[k][1])}" for s in summaries) + " |")
    rows.append("| Right call | " + " | ".join(f"{s['right']} of {s['runs']}" for s in summaries) + " |")
    rows.append("| Nemotron plans / hosted failures / hand-overs to the fixed script | "
                + " | ".join(f"{s['planner_calls']} / {s['hosted_failures']} / {s['to_script']}" for s in summaries) + " |")
    rows.append("| Voice fallbacks to Kokoro or Moonshine (speaking + listening) | "
                + " | ".join(str(s["voice_fallbacks"]) for s in summaries) + " |")
    if cut_internet:
        planner = ("fixed script. The NVIDIA key was set, but hosted Nemotron was unreachable (internet cut)"
                   if key else "fixed script (no NVIDIA_API_KEY)")
        voice_line = ("Kokoro text-to-speech and Moonshine speech-to-text. The ElevenLabs key was set, but "
                      "ElevenLabs was unreachable (internet cut)" if voice == "online"
                      else "offline: Kokoro text-to-speech and Moonshine speech-to-text")
    else:
        planner = "hosted Nemotron (real key)" if key else "MOCK, no NVIDIA_API_KEY: the fixed script planned"
        voice_line = ("ElevenLabs text-to-speech and Scribe speech-to-text, Kokoro and Moonshine as the per-line "
                      "fallback" if voice == "online" else "offline: Kokoro text-to-speech and Moonshine speech-to-text")
    out = ["# Judge-table rehearsal timing", "",
           f"Planner: {planner}. Voice: {voice_line}. AGENT_LISTEN_S={listen_s:g}."
           + (" INTERNET CUT for this process and the agent child only: every outbound request went to a closed "
              "local port. A refused connection fails at once, so these times are the best case. A network that "
              "hangs instead waits out the ElevenLabs timeout on each line and the planner timeout on each turn."
              if cut_internet else ""), ""]
    by = {s["case"]: s for s in summaries}
    if (demo := by.get("standup")) and demo["last_word_s"][0] is not None:
        med, worst = demo["last_word_s"]
        fits = "fits" if worst <= FIT_S else "fits at the median only" if med <= FIT_S else "does not fit"
        out += [f"Demo run, event to last word: {med:g} s median, {worst:g} s worst. It {fits} the {FIT_S:g} s target.", ""]
    out += rows + [""]
    out += [f"- {s['case']}: times are from {s['timed']} of {s['runs']} runs. The others did not finish or did not "
            "speak every line, see Failed runs." for s in summaries if s["timed"] < s["runs"]]
    out += [""] if any(s["timed"] < s["runs"] for s in summaries) else []
    failed = [f"- {s['case']} run {n}: {why}" for s in summaries for n, why in s["failed"]]
    out += (["Failed runs:", ""] + failed if failed else ["Failed runs: none."]) + [""]
    out += ["What was real and what was simulated:", "",
            "- Real: the hub, the agent process and its planner chain, the voice service, the text-to-speech "
            "synthesis of every line, the speech-to-text of every reply, and the classifier.",
            "- Simulated: the speaker and the microphone. A line waits its synthesized audio's real length instead "
            "of playing. A listen waits the listen window, then hands the speech-to-text a recorded clip "
            f"(macOS `say` voice, from the voice test fixtures) {REPLY_AT_S:g} s into real room noise.",
            "- Not run: the local Nemotron 4B tier. It shares the live loop's Ollama, so the agent's Ollama URL "
            "points at a closed port and a hosted failure goes straight to the fixed script.",
            f"- Dashboard zoom: it starts at the alarm or help message on the bus and lands {ZOOM_S:g} s later "
            "(camera.js NEAR_FLIGHT_MS, the flight from the city view). No browser was driven.",
            "- The voice service and its engines ran in the hub's process, not a process of their own as in the "
            "live loop.",
            "- The person stands up as soon as the alarm reaches the bus.", "",
            f"Wall time {wall_s / 60:.1f} min.", "", "Rerun:", "", "```bash", command, "```", ""]
    return "\n".join(out)


def _interrupt(signum, frame):
    raise KeyboardInterrupt


def main(argv=None):
    p = argparse.ArgumentParser(prog="python -m software.eval.rehearsal", description=__doc__.splitlines()[0])
    p.add_argument("--out", required=True)
    p.add_argument("--runs", type=int, default=10, help="runs per case")
    p.add_argument("--cases", default=",".join(DEMO_CASES), help="case ids (default: the demo run and Help)")
    p.add_argument("--voice", choices=("online", "offline"),
                   help="online needs ELEVENLABS_API_KEY (default: online when it is set)")
    p.add_argument("--cut-internet", action="store_true", help="refuse every outbound request of this run's processes")
    p.add_argument("--listen-s", type=float, default=6.0, help="AGENT_LISTEN_S (demo default 6)")
    p.add_argument("--max-rpm", type=float, default=15.0, help="pace hosted Nemotron calls to this many per minute")
    p.add_argument("--run-timeout-s", type=float, default=240.0)
    args = p.parse_args(argv)
    by_id = {c.id: c for c in CASES}
    wanted = args.cases.split(",")
    if unknown := set(wanted) - set(by_id):
        p.error(f"unknown case ids {sorted(unknown)}")
    if no_clip := [c for c in wanted if set(by_id[c].transcripts) - set(REPLY_CLIPS) - {""}]:
        p.error(f"cases {no_clip} have replies with no recorded clip (clips: {sorted(REPLY_CLIPS)})")
    eleven_key = os.environ.get("ELEVENLABS_API_KEY") or None
    voice = args.voice or ("online" if eleven_key else "offline")
    key = os.environ.get("NVIDIA_API_KEY") or None
    signal.signal(signal.SIGTERM, _interrupt)
    began = time.monotonic()
    results = asyncio.run(rehearse([by_id[c] for c in wanted], args.runs, args.out, voice=voice, eleven_key=eleven_key,
                                   cut_internet=args.cut_internet, listen_s=args.listen_s, max_rpm=args.max_rpm,
                                   run_timeout_s=args.run_timeout_s))
    summaries = [summarize(case, runs) for case, runs in results]
    command = ("NVIDIA_API_KEY=... ELEVENLABS_API_KEY=... .venv/bin/python -m software.eval.rehearsal "
               + shlex.join(sys.argv[1:] if argv is None else argv))
    text = report(summaries, command=command, key=key, voice=voice, cut_internet=args.cut_internet,
                  listen_s=args.listen_s, wall_s=time.monotonic() - began)
    out = Path(args.out)
    (out / "rehearsal.md").write_text(text)
    (out / "rehearsal.json").write_text(json.dumps(
        {"summaries": summaries, "runs": [r for _, runs in results for r in runs]}, indent=1))
    print(text)
    return 0 if all(s["right"] == s["runs"] and not s["failed"] for s in summaries) else 1


if __name__ == "__main__":
    sys.exit(main())
