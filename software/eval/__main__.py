"""Decision-layer eval: python -m software.eval --out DIR [--runs N] [--cases a,b] [--listen-s S] [--max-rpm R]

Reads NVIDIA_API_KEY from the environment and passes it only to the agent child process.
Without it the agent runs in mock mode and the fixed script plans every run.
"""

import argparse
import asyncio
import json
import os
import shlex
import signal
import sys
import time
from pathlib import Path

from software.eval.cases import CASES
from software.eval.run import run_cases
from software.eval.score import summarize, table


def headline(summaries, key, listen_s):
    by_id = {s["case"]: s for s in summaries}
    runs = sum(s["runs"] for s in summaries)
    right = sum(s["correct"] for s in summaries)
    clean = sum(s["clean"] for s in summaries)
    who = (f"{clean} of {runs} were planned by hosted Nemotron end to end (no fallback, no code override)."
           if key else "MOCK: no NVIDIA_API_KEY, the fixed script planned every run.")
    lines = [f"{right} of {runs} runs made the right call. {who}",
             f"Times below are from the event on the bus, with a {listen_s:g} s listen window per question and "
             "no speaking time."]
    if (s := by_id.get("help")) and s["alarm_median_s"] is not None:
        lines.append(f"After \"Help\": alarm on screen {s['alarm_median_s']:g} s median from the event "
                     f"(worst {s['alarm_worst_s']:g} s).")
    if (s := by_id.get("silence")) and s["alarm_median_s"] is not None:
        lines.append(f"No answer 3 times: alarm on the 3rd miss, {s['alarm_median_s']:g} s median from the event "
                     f"(worst {s['alarm_worst_s']:g} s).")
    gaps = [s["heard_to_rule_median_s"] for s in summaries if s["heard_to_rule_median_s"] is not None]
    if gaps:
        lines.append(f"A spoken reply reaches the rule {min(gaps):g} to {max(gaps):g} s after the voice service sends it "
                     "(per-case medians). That wait includes the Safety Guard check, which runs before the rule.")
    asks = [s["first_ask_median_s"] for s in summaries if s["first_ask_median_s"] is not None]
    if asks:
        lines.append(f"First question sent {min(asks):g} to {max(asks):g} s after the event (per-case medians).")
    return lines


def report(summaries, *, command, key, listen_s, max_rpm, wall_s, calls_est):
    s_runs = sum(s["runs"] for s in summaries)
    fallbacks = sum(s["fallbacks"] for s in summaries)
    to_script = sum(s["to_script"] for s in summaries)
    overrides = sum(s["overrides"] for s in summaries)
    plans = sum(s["planner_calls"] for s in summaries)
    wrong_lines = sum(s["wrong_lines"] for s in summaries)
    out = ["# Decision-layer eval", "", *headline(summaries, key, listen_s), "", table(summaries), "",
           f"Planner: {'hosted Nemotron (real key)' if key else 'MOCK, no NVIDIA_API_KEY: the fixed script planned'}. "
           f"{plans} Nemotron planner turns, {fallbacks} fallback rows, {to_script} hand-overs to the fixed script "
           "(the eval skips the local 4B model, so one hosted failure writes two fallback rows), "
           f"{overrides} code overrides (code did or replaced a step the planner got wrong), {wrong_lines} asks with a different line "
           f"than the try's retry line (counted, not a wrong call) in {s_runs} runs.",
           f"Timing: the agent's AGENT_LISTEN_S={listen_s:g} (demo default 6). The scripted voice engine waits that "
           "long per listen and does not simulate speaking time, so real demo times are longer by the spoken lines.",
           f"Pacing: one run at a time; estimated hosted calls {calls_est} in {wall_s / 60:.1f} min"
           + (f", paced to at most {max_rpm:g} per minute." if max_rpm and key else "."),
           "", "Rerun:", "", "```bash", command, "```", ""]
    problems = [(s["case"], p) for s in summaries for p in s["problems"]]
    if problems:
        out += ["Wrong calls seen (each distinct problem once):", ""]
        out += [f"- {case}: {p}" for case, p in problems]
        out.append("")
    out += ["Expected outcome per case (from the code):", ""]
    out += [f"- {c.id}: {c.why}" for c in CASES if c.id in {s['case'] for s in summaries}]
    return "\n".join(out) + "\n"


def _interrupt(signum, frame):
    raise KeyboardInterrupt


def main(argv=None):
    p = argparse.ArgumentParser(prog="python -m software.eval", description=__doc__.splitlines()[0])
    p.add_argument("--out", required=True, help="folder for results.md, results.json, raw.jsonl and logs")
    p.add_argument("--runs", type=int, default=1, help="runs per case")
    p.add_argument("--cases", help="comma-separated case ids (default: all)")
    p.add_argument("--listen-s", type=float, default=1.0, help="AGENT_LISTEN_S for the agent (demo default 6)")
    p.add_argument("--max-rpm", type=float, default=15.0, help="pace runs to this many hosted calls per minute")
    p.add_argument("--run-timeout-s", type=float, default=240.0)
    args = p.parse_args(argv)

    cases = CASES
    if args.cases:
        wanted = args.cases.split(",")
        unknown = set(wanted) - {c.id for c in CASES}
        if unknown:
            p.error(f"unknown case ids {sorted(unknown)}; known: {[c.id for c in CASES]}")
        cases = tuple(c for c in CASES if c.id in wanted)
    key = os.environ.get("NVIDIA_API_KEY") or None
    if not key:
        print("MOCK: no NVIDIA_API_KEY. The fixed script plans every run.", file=sys.stderr)

    signal.signal(signal.SIGTERM, _interrupt)  # a kill by PID still stops the agent child in run_cases' finally
    began = time.monotonic()
    results = asyncio.run(run_cases(cases, args.runs, args.out, key=key, listen_s=args.listen_s,
                                    max_rpm=args.max_rpm, run_timeout_s=args.run_timeout_s))
    wall_s = time.monotonic() - began
    summaries = [summarize(case, runs) for case, runs in results]
    calls_est = sum(r["hosted_calls_est"] for _, runs in results for r in runs)
    command = "NVIDIA_API_KEY=... .venv/bin/python -m software.eval " + shlex.join(sys.argv[1:] if argv is None else argv)
    text = report(summaries, command=command, key=key, listen_s=args.listen_s, max_rpm=args.max_rpm,
                  wall_s=wall_s, calls_est=calls_est)
    out = Path(args.out)
    (out / "results.md").write_text(text)
    (out / "results.json").write_text(json.dumps(
        {"summaries": summaries, "runs": [r for _, runs in results for r in runs]}, indent=1))
    print(text)
    return 0 if all(s["correct"] == s["runs"] for s in summaries) else 1


if __name__ == "__main__":
    sys.exit(main())
