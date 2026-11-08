import asyncio
import json
import logging
import os
import sys

log = logging.getLogger("hub.sim")

START_STATE = {"presence": "none", "power": "mains", "battery_pct": 100}

HEARTBEAT_S = 5

DEMO_ALERT = {
    "type": "alert",
    "source": "usgs",
    "event": "Earthquake",
    "severity": "Severe",
    "urgency": "Immediate",
    "certainty": "Observed",
    "area": "Richardson, TX",
    "headline": "M5.1 earthquake near Richardson, TX",
    "code": "EQW",
    "station": "HACKDEMO",
    "distance_mi": 3,
    "demo": True,
}

KEY_HELP = """keys:
  q quake          m presence moving   s presence still (fall_hint after moving)
  n presence none  p toggle power      a fake official alert (DEMO)
  r reset          Ctrl-C quit"""


def key_events(key: str, state: dict) -> tuple[list[dict], dict]:
    """Map one key to the events it sends and the next simulator state. Pure."""
    state = dict(state)
    if key == "q":
        return [{"type": "quake", "peak_g": 0.82}], state
    if key in ("m", "s", "n"):
        new = {"m": "moving", "s": "still", "n": "none"}[key]
        events = [{"type": "presence", "state": new}]
        if new == "still" and state["presence"] == "moving":
            events.append({"type": "fall_hint"})
        state["presence"] = new
        return events, state
    if key == "p":
        state["power"] = "battery" if state["power"] == "mains" else "mains"
        return [{"type": "power", "state": state["power"]}], state
    if key == "a":
        return [dict(DEMO_ALERT)], state
    if key == "r":
        return [{"type": "reset"}], dict(START_STATE)
    return [], state


def heartbeat(state: dict) -> tuple[dict, dict]:
    """The heartbeat event for this state, and the state after it. Battery drains 1% per beat on battery power."""
    event = {"type": "heartbeat", "battery_pct": state["battery_pct"]}
    state = dict(state)
    if state["power"] == "battery":
        state["battery_pct"] = max(0, state["battery_pct"] - 1)
    return event, state


class Simulator:
    def __init__(self, hub):
        self.hub = hub
        self.state = dict(START_STATE)
        hub.listeners.append(self.on_bus_message)

    def on_bus_message(self, msg: dict):
        if msg.get("type") == "reset":
            self.state = dict(START_STATE)

    def send(self, event: dict):
        print("-> " + json.dumps(self.hub.publish(event)), flush=True)

    def on_key(self, key: str):
        events, self.state = key_events(key, self.state)
        for event in events:
            self.send(event)

    async def heartbeats(self):
        while True:
            event, self.state = heartbeat(self.state)
            self.send(event)
            await asyncio.sleep(HEARTBEAT_S)


async def run_sim(hub):
    sim = Simulator(hub)
    if not sys.stdin.isatty():
        log.warning("no TTY on stdin: keyboard off, heartbeat on. Inject events with python -m software.hub.send")
        await sim.heartbeats()
        return

    import termios
    import tty

    fd = sys.stdin.fileno()
    saved = termios.tcgetattr(fd)
    tty.setcbreak(fd)
    loop = asyncio.get_running_loop()

    def on_stdin():
        for key in os.read(fd, 64).decode(errors="ignore").lower():
            sim.on_key(key)

    loop.add_reader(fd, on_stdin)
    print(KEY_HELP, flush=True)
    try:
        await sim.heartbeats()
    finally:
        loop.remove_reader(fd)
        termios.tcsetattr(fd, termios.TCSADRAIN, saved)
