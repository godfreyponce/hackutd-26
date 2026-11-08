import asyncio
import json
import logging

import pytest
from websockets.asyncio.client import connect
from websockets.exceptions import InvalidURI

from software.hub.bus import running_hub
from software.presence.__main__ import run
from software.presence.sources import parse_frame, person_boxes, replay_frames
from software.presence.tracker import Tracker


def write_replay(path):
    """Walk for 2 s, then lie still for 5 s, at 8 frames per second."""
    lines = []
    for i in range(56):
        t = i / 8
        cx = 0.1 + 0.1 * t if t < 2 else 0.5
        lines.append(json.dumps({"t": t, "boxes": [[cx - 0.1, 0.3, cx + 0.1, 0.7, 0.9]]}))
    path.write_text("\n".join(lines) + "\n")


async def no_sleep(_):
    pass


def test_replay_reaches_the_hub_as_presence_messages(tmp_path):
    replay = tmp_path / "walk_then_still.jsonl"
    write_replay(replay)

    async def scenario():
        async with running_hub("127.0.0.1", 0, 0) as hub:
            url = f"ws://127.0.0.1:{hub.ws_port}"
            async with connect(url) as tap:
                await run(url, replay_frames(replay, sleep=no_sleep), Tracker())
                got = []
                while len(got) < 4:
                    got.append(json.loads(await asyncio.wait_for(tap.recv(), timeout=2)))
                return got

    got = asyncio.run(scenario())
    assert [(m["type"], m.get("state")) for m in got] == [
        ("presence", "moving"),
        ("presence", "moving"),
        ("presence", "still"),
        ("fall_hint", None),
    ]
    assert all(isinstance(m["t"], int) for m in got)


def test_parse_frame_accepts_the_stdin_format_and_skips_bad_lines():
    assert parse_frame('{"t": 1.5, "boxes": [[0.1, 0.2, 0.3, 0.4, 0.9]]}') == (1.5, [[0.1, 0.2, 0.3, 0.4, 0.9]])
    assert parse_frame('{"t": 2, "boxes": []}') == (2.0, [])
    assert parse_frame("not json") is None
    assert parse_frame('{"t": 1}') is None
    assert parse_frame('{"t": 1, "boxes": [[0.1, 0.2, 0.9]]}') is None


def test_parse_frame_skips_posture_event_lines_without_a_warning(caplog):
    with caplog.at_level(logging.WARNING, logger="presence.sources"):
        assert parse_frame('EVENT {"type": "presence", "state": "still"}') is None
    assert caplog.records == []


def test_person_boxes_reorders_hailo_output_and_keeps_only_people():
    hailo_output = [[[0.2, 0.1, 0.8, 0.4, 0.9]], [[0.0, 0.0, 1.0, 1.0, 0.99]]]
    assert person_boxes(hailo_output) == [[0.1, 0.2, 0.4, 0.8, 0.9]]


def test_a_hub_reset_gets_the_current_state_back_at_once():
    stop = asyncio.Event()

    async def still_then_no_more_frames():
        for i in range(32):  # still from 3.0 s; then no frames, so no 5 s repeat
            yield i / 8, [[0.4, 0.3, 0.6, 0.7, 0.9]]
            await asyncio.sleep(0.005)
        await stop.wait()

    async def scenario():
        async with running_hub("127.0.0.1", 0, 0) as hub:
            url = f"ws://127.0.0.1:{hub.ws_port}"
            async with connect(url) as tap:
                sender = asyncio.create_task(run(url, still_then_no_more_frames(), Tracker()))
                first = json.loads(await asyncio.wait_for(tap.recv(), timeout=2))
                await tap.send('{"type":"reset"}')
                got = [json.loads(await asyncio.wait_for(tap.recv(), timeout=2)) for _ in range(2)]
                sender.cancel()
                return first, got

    first, got = asyncio.run(scenario())
    assert first["state"] == "still"
    assert [(m["type"], m.get("state")) for m in got] == [("reset", None), ("presence", "still")]


def test_a_hub_reset_lets_the_next_still_send_fall_hint_again():
    after_reset = asyncio.Event()

    def walk_then_still(t0):
        for i in range(48):  # walk for 2 s, then still for 4 s
            t = t0 + i / 8
            cx = 0.1 + 0.1 * (t - t0) if t - t0 < 2 else 0.3
            yield t, [[cx - 0.1, 0.3, cx + 0.1, 0.7, 0.9]]

    async def frames():
        for frame in walk_then_still(0):
            yield frame
        await after_reset.wait()
        for frame in walk_then_still(6):  # well inside the 60 s cooldown
            yield frame

    async def until_fall_hint(tap):
        while json.loads(await asyncio.wait_for(tap.recv(), timeout=2))["type"] != "fall_hint":
            pass

    async def scenario():
        async with running_hub("127.0.0.1", 0, 0) as hub:
            url = f"ws://127.0.0.1:{hub.ws_port}"
            async with connect(url) as tap:
                sender = asyncio.create_task(run(url, frames(), Tracker()))
                await until_fall_hint(tap)
                await tap.send('{"type":"reset"}')
                # The service resends its state after it has handled the reset, so the cooldown is clear by then.
                while json.loads(await asyncio.wait_for(tap.recv(), timeout=2)).get("state") != "still":
                    pass
                after_reset.set()
                await until_fall_hint(tap)
                sender.cancel()

    asyncio.run(scenario())


def test_a_bad_hub_url_fails_instead_of_hanging():
    async def no_frames():
        return
        yield

    with pytest.raises(InvalidURI):
        asyncio.run(asyncio.wait_for(run("localhost:8765", no_frames(), Tracker()), timeout=2))
