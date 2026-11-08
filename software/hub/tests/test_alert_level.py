import asyncio
import json

import pytest
from websockets.asyncio.client import connect

from software.hub.alert_level import alert_level
from software.hub.bus import running_hub


@pytest.mark.parametrize(
    "code, level",
    [
        ("RWT", "info"),
        ("RMT", "info"),
        ("NPT", "info"),
        ("DMO", "info"),
        ("TOA", "watch"),
        ("SVA", "watch"),
        ("FFA", "watch"),
        ("SVR", "warning"),
        ("FFW", "warning"),
        ("WSW", "warning"),
        ("EQW", "emergency"),
        ("TOR", "emergency"),
        ("CEM", "emergency"),
        ("CAE", "emergency"),
        ("EVI", "emergency"),
        ("SPW", "emergency"),
    ],
)
def test_code_table(code, level):
    assert alert_level({"type": "alert", "code": code, "severity": "Minor"}) == level


def test_code_is_read_without_regard_to_case_or_spaces():
    assert alert_level({"code": " eqw "}) == "emergency"


@pytest.mark.parametrize(
    "code, near, far",
    [
        ("EQW", "emergency", "warning"),
        ("SVR", "warning", "watch"),
        ("TOA", "watch", "info"),
        ("RWT", "info", "info"),
    ],
)
def test_more_than_25_miles_drops_one_step_but_not_below_info(code, near, far):
    assert alert_level({"code": code, "distance_mi": 25}) == near
    assert alert_level({"code": code, "distance_mi": 25.5}) == far


def test_distance_that_is_not_a_number_is_ignored():
    assert alert_level({"code": "EQW", "distance_mi": "40"}) == "emergency"
    assert alert_level({"code": "EQW", "distance_mi": True}) == "emergency"


@pytest.mark.parametrize(
    "severity, level",
    [("Extreme", "emergency"), ("Severe", "warning"), ("Moderate", "watch"), ("Minor", "info"), ("Unknown", "info"), (None, "info")],
)
def test_missing_code_falls_back_to_cap_severity(severity, level):
    assert alert_level({"type": "alert", "severity": severity}) == level


def test_unknown_code_falls_back_to_cap_severity():
    assert alert_level({"code": "SPS", "severity": "Severe"}) == "warning"
    assert alert_level({"code": "", "severity": "Extreme"}) == "emergency"
    assert alert_level({"code": 7, "severity": "Moderate"}) == "watch"
    assert alert_level({"severity": ["Extreme"]}) == "info"


def test_severity_fallback_also_drops_one_step_when_far():
    assert alert_level({"severity": "Extreme", "distance_mi": 100}) == "warning"


async def recv_json(ws):
    return json.loads(await asyncio.wait_for(ws.recv(), timeout=2))


def test_hub_adds_level_to_an_alert_from_a_client_before_broadcast():
    async def scenario():
        async with running_hub("127.0.0.1", 0, 0) as hub:
            url = f"ws://127.0.0.1:{hub.ws_port}"
            async with connect(url) as a, connect(url) as b:
                await a.send(json.dumps({"type": "alert", "code": "TOR", "severity": "Extreme", "headline": "x"}))
                return await recv_json(a), await recv_json(b)

    got_a, got_b = asyncio.run(scenario())
    assert got_a == got_b
    assert got_a["level"] == "emergency"


def test_hub_overwrites_a_level_the_sender_set():
    async def scenario():
        async with running_hub("127.0.0.1", 0, 0) as hub:
            async with connect(f"ws://127.0.0.1:{hub.ws_port}") as a:
                await a.send(json.dumps({"type": "alert", "code": "RWT", "level": "emergency"}))
                return await recv_json(a)

    assert asyncio.run(scenario())["level"] == "info"


def test_hub_adds_level_to_an_alert_published_inside_the_hub():
    async def scenario():
        async with running_hub("127.0.0.1", 0, 0) as hub:
            async with connect(f"ws://127.0.0.1:{hub.ws_port}") as a:
                hub.publish({"type": "alert", "severity": "Moderate"})
                return await recv_json(a)

    assert asyncio.run(scenario())["level"] == "watch"


def test_hub_leaves_other_messages_without_level():
    async def scenario():
        async with running_hub("127.0.0.1", 0, 0) as hub:
            async with connect(f"ws://127.0.0.1:{hub.ws_port}") as a:
                await a.send('{"type":"quake","peak_g":0.82,"severity":"Extreme"}')
                return await recv_json(a)

    assert "level" not in asyncio.run(scenario())
