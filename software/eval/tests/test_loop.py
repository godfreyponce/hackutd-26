"""End to end in mock mode: the real hub, the real agent process and the real voice service class.
With no key the fixed script plans, so every case must come out right."""

import asyncio

from software.eval.cases import CASES
from software.eval.run import run_cases


def test_every_case_is_right_with_the_fixed_script(tmp_path, monkeypatch):
    monkeypatch.delenv("NVIDIA_API_KEY", raising=False)
    results = asyncio.run(run_cases(CASES, 1, tmp_path, listen_s=0.2, run_timeout_s=60, progress=lambda _: None))
    wrong = {case.id: runs[0]["problems"] for case, runs in results if not runs[0]["correct"]}
    assert wrong == {}
    for case, runs in results:
        r = runs[0]
        # Each check-in: MOCK hosted -> refused local -> fixed script. The stand-up case runs two check-ins.
        assert r["fallbacks"] == 2 * len(case.outcomes), case.id
        assert r["to_script"] >= 1, case.id
        assert r["planner_calls"] == 0, case.id
        assert (r["alarm_s"] is not None) == (case.alarm_after is not None), case.id
    assert (tmp_path / "raw.jsonl").stat().st_size > 0
    assert "connected to" in (tmp_path / "agent.log").read_text()
