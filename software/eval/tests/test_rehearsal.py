import asyncio
import re
from pathlib import Path

import numpy as np
import pytest

from software.eval.cases import CASES
from software.eval.rehearsal import ZOOM_S, SoundDevice, main, report, step_times, rehearse, summarize
from software.voice import engines
from software.voice.classify import classify

CASE = {c.id: c for c in CASES}


def test_step_times_read_the_demo_steps_from_the_bus_and_the_device():
    events = [
        (10.0, {"type": "fall_hint"}),
        (11.0, {"type": "checkin", "state": "asking", "try": 1}),
        (30.0, {"type": "checkin", "state": "no_answer", "try": 3}),
        (31.0, {"type": "checkin", "state": "alarm"}),
        (45.0, {"type": "checkin", "state": "ok", "try": 1}),
        (45.5, {"type": "checkin", "state": "clear", "try": 1}),
    ]
    spoken = [(11.5, 14.0), (46.0, 49.25)]
    t = step_times(events, spoken)
    assert t == {"first_ask_s": 1.0, "first_word_s": 1.5, "zoom_landed_s": 21.0 + ZOOM_S, "alarm_s": 21.0,
                 "standdown_s": 35.5, "last_word_s": 39.25, "lines_s": [[1.5, 4.0], [36.0, 39.25]]}


def test_the_dashboard_zooms_on_a_help_answer_before_the_alarm():
    events = [
        (0.0, {"type": "help_gesture"}),
        (1.0, {"type": "checkin", "state": "asking", "try": 1}),
        (9.0, {"type": "heard", "answer": "help", "transcript": "Help"}),
        (10.0, {"type": "checkin", "state": "help", "try": 1}),
        (14.0, {"type": "checkin", "state": "alarm"}),
    ]
    t = step_times(events, [(2.0, 4.0), (10.5, 15.0)])
    assert t["zoom_landed_s"] == 9.0 + ZOOM_S
    assert t["alarm_s"] == 14.0
    assert t["standdown_s"] is None
    assert t["last_word_s"] == 15.0


@pytest.fixture(scope="module")
def stt():
    from software.voice.engines import MoonshineSTT

    try:
        return MoonshineSTT()
    except Exception as e:
        pytest.skip(f"Moonshine model not cached: {e}")


def test_the_device_hands_each_reply_to_the_real_speech_to_text(stt):
    device = SoundDevice(sleep=lambda s: None)
    device.load(["I'm okay", "Help", ""])
    heard = [classify(stt.transcribe(device.record(3.0, print))) for _ in range(3)]
    assert heard == ["ok", "help", "no_answer"]


def test_the_device_times_each_line_instead_of_playing_it():
    slept = []
    device = SoundDevice(sleep=slept.append)
    device.play(np.zeros(8000, dtype=np.float32), 16000)
    assert slept == [0.5]
    assert len(device.spoken) == 1


def test_a_listen_left_over_from_the_last_run_does_not_take_the_next_runs_reply():
    device = SoundDevice(sleep=lambda s: None)
    device.load(["Help"])
    device.begin()  # a listen starts, then the run times out
    device.load(["Help"])  # the next run starts while that listen is still in flight
    stale = device.record(1.0, print)
    device.play(np.zeros(8000, dtype=np.float32), 16000)
    assert list(device.replies) == ["Help"]
    assert device.spoken == []
    assert np.allclose(stale, np.resize(device.noise, len(stale)))


def test_the_zoom_time_matches_the_dashboard_flight():
    camera = (Path(__file__).resolve().parents[2] / "web" / "dashboard" / "camera.js").read_text()
    assert int(re.search(r"NEAR_FLIGHT_MS = (\d+)", camera).group(1)) == ZOOM_S * 1000


def test_an_internet_cut_report_does_not_say_nemotron_or_elevenlabs_planned_or_spoke():
    runs = [{"run": 1, "correct": True, "problems": [], "planner_calls": 0, "hosted_failures": 2, "to_script": 2,
             "voice_fallbacks": 6, "last_word_s": 40.0, "alarm_s": 30.0}]
    text = report([summarize(CASE["standup"], runs)], command="x", key="nvapi-set", voice="online",
                  cut_internet=True, listen_s=6.0, wall_s=60.0)
    header = text.splitlines()[2]
    assert header.startswith("Planner: fixed script.")
    assert "unreachable" in header
    assert "Voice: Kokoro text-to-speech and Moonshine speech-to-text." in header


def test_times_leave_out_runs_that_did_not_speak_every_line():
    runs = [{"run": 1, "correct": True, "problems": [], "planner_calls": 1, "hosted_failures": 0, "to_script": 0,
             "last_word_s": 40.0},
            {"run": 2, "correct": True, "problems": [], "planner_calls": 1, "hosted_failures": 0, "to_script": 0,
             "last_word_s": 20.0, "voice_problem": "1 lines not spoken after 60 s"}]
    s = summarize(CASE["standup"], runs)
    assert s["last_word_s"] == (40.0, 40.0)
    assert s["timed"] == 1
    assert s["failed"] == [(2, "1 lines not spoken after 60 s")]


def test_a_case_with_a_reply_that_has_no_recorded_clip_is_refused(tmp_path):
    with pytest.raises(SystemExit):
        main(["--out", str(tmp_path), "--cases", "hedge"])


def test_internet_cut_demo_and_help_run_on_the_fixed_script_and_the_offline_voice(tmp_path, monkeypatch):
    """Fake keys with the network cut for this process only: hosted Nemotron and ElevenLabs both fail,
    so the fixed script plans and Kokoro and Moonshine take every line. Nothing leaves the machine.
    The agent waits 60 s, not 15 s, past the listen for each answer: on a loaded laptop the voice took
    more than 15 s to finish the alarm line, then ask "Are you okay?", and the stand-up answer was lost."""
    if missing := [f for f in engines.KOKORO_FILES if not (engines.MODEL_DIR / "kokoro" / f).exists()]:
        pytest.skip(f"Kokoro model not downloaded: {missing}")
    monkeypatch.setenv("NVIDIA_API_KEY", "nvapi-fake-for-test")
    results = asyncio.run(rehearse([CASE["standup"], CASE["help"]], 1, tmp_path, voice="online",
                                   eleven_key="fake-for-test", cut_internet=True, listen_s=2.0, max_rpm=None,
                                   progress=lambda _: None, agent_settings={"AGENT_HEARD_GRACE_S": "60"}))
    for case, runs in results:
        r = runs[0]
        assert r["correct"], (case.id, r["problems"])
        assert r["hosted_failures"] >= 1, case.id
        assert r["to_script"] >= 1, case.id
        assert r["planner_calls"] == 0, case.id
        assert r["voice_fallbacks"] >= r["lines"] > 0, case.id
        assert r["last_word_s"] > r["alarm_s"] > r["first_ask_s"] > 0, case.id
    demo = dict(results)[CASE["standup"]][0]
    assert demo["standdown_s"] > demo["zoom_landed_s"]
    # The cut, not the fake keys, made them fail: a 401 would mean a request left the machine.
    engine_log = (tmp_path / "engine.log").read_text()
    agent_log = (tmp_path / "agent.log").read_text()
    assert "ProxyError" in engine_log and "401 Client Error" not in engine_log
    assert "APIConnectionError" in agent_log and "AuthenticationError" not in agent_log
