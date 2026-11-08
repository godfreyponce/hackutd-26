from software.hub.sim import START_STATE, heartbeat, key_events


def types(events):
    return [e["type"] for e in events]


def test_q_sends_quake_near_0_8_g():
    events, _ = key_events("q", START_STATE)
    assert types(events) == ["quake"]
    assert 0.7 <= events[0]["peak_g"] <= 0.9


def test_m_n_send_presence():
    assert key_events("m", START_STATE)[0] == [{"type": "presence", "state": "moving"}]
    assert key_events("n", START_STATE)[0] == [{"type": "presence", "state": "none"}]


def test_s_after_m_sends_still_then_fall_hint():
    _, state = key_events("m", START_STATE)
    events, state = key_events("s", state)
    assert events == [{"type": "presence", "state": "still"}, {"type": "fall_hint"}]
    assert state["presence"] == "still"


def test_s_without_moving_first_sends_no_fall_hint():
    events, _ = key_events("s", START_STATE)
    assert events == [{"type": "presence", "state": "still"}]
    _, state = key_events("n", START_STATE)
    assert key_events("s", state)[0] == [{"type": "presence", "state": "still"}]


def test_p_toggles_power():
    events, state = key_events("p", START_STATE)
    assert events == [{"type": "power", "state": "battery"}]
    events, state = key_events("p", state)
    assert events == [{"type": "power", "state": "mains"}]


def test_a_sends_cap_shaped_demo_alert():
    (alert,), _ = key_events("a", START_STATE)
    assert alert["type"] == "alert"
    for field in ("source", "event", "severity", "urgency", "certainty", "area", "headline"):
        assert alert[field]
    assert alert["code"] == "EQW" and alert["station"] == "HACKDEMO"
    assert alert["demo"] is True
    assert alert["distance_mi"] <= 25
    assert "DEMO" not in alert["headline"]


def test_a_alert_reaches_the_bus_as_emergency():
    from software.hub.alert_level import alert_level

    (alert,), _ = key_events("a", START_STATE)
    assert alert_level(alert) == "emergency"


def test_r_sends_reset_and_restores_start_state():
    _, state = key_events("m", START_STATE)
    _, state = key_events("p", state)
    events, state = key_events("r", state)
    assert events == [{"type": "reset"}]
    assert state == START_STATE


def test_unknown_key_sends_nothing():
    assert key_events("x", START_STATE) == ([], START_STATE)


def test_key_events_does_not_mutate_input_state():
    before = dict(START_STATE)
    key_events("m", START_STATE)
    key_events("p", START_STATE)
    assert START_STATE == before


def test_heartbeat_drains_battery_only_on_battery_power():
    event, state = heartbeat(START_STATE)
    assert event == {"type": "heartbeat", "battery_pct": 100}
    assert state == START_STATE
    _, on_battery = key_events("p", START_STATE)
    event, drained = heartbeat(on_battery)
    assert event["battery_pct"] == on_battery["battery_pct"]
    assert drained["battery_pct"] == on_battery["battery_pct"] - 1


def test_reset_from_any_bus_client_resets_simulator_state():
    from software.hub.bus import Hub
    from software.hub.sim import Simulator

    hub = Hub()
    sim = Simulator(hub)
    sim.on_key("m")
    sim.on_key("p")
    hub.publish({"type": "reset"})
    assert sim.state == START_STATE
