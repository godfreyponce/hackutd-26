"""Audio file -> sox -> multimon-ng -> same_to_alert -> a real hub, through listen.sh --file."""

import asyncio
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from websockets.asyncio.client import connect

from software.hub.bus import running_hub
from software.same.make_same import main as make_same

PKG = Path(__file__).resolve().parent.parent
LISTEN = PKG / "listen.sh"
DEMO_WAV = PKG / "demo_eqw.wav"
REHEARSAL_WAV = PKG / "rehearsal_eqw.wav"

missing = [tool for tool in ("multimon-ng", "sox") if shutil.which(tool) is None]
pytestmark = pytest.mark.skipif(
    bool(missing), reason=f"end-to-end SAME tests need {' and '.join(missing)} on PATH (see software/same/README.md)")


def alerts_on_hub_from(*args: str, env: dict | None = None, stdin: bytes | None = None) -> list[dict]:
    async def scenario():
        async with running_hub("127.0.0.1", 0, 0) as hub:
            url = f"ws://127.0.0.1:{hub.ws_port}"
            async with connect(url) as tap:
                proc = await asyncio.create_subprocess_exec(
                    "bash", str(LISTEN), *args,
                    env={**os.environ, "HUB_URL": url, "PYTHON": sys.executable, **(env or {})},
                    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                out, err = await asyncio.wait_for(proc.communicate(stdin), timeout=60)
                assert proc.returncode == 0, err.decode()
                got = []
                try:
                    while True:
                        got.append(json.loads(await asyncio.wait_for(tap.recv(), timeout=1)))
                except TimeoutError:
                    return got

    return [m for m in asyncio.run(scenario()) if m["type"] == "alert"]


def assert_one_demo_eqw(got):
    assert len(got) == 1, got
    a = got[0]
    assert (a["code"], a["station"], a["demo"]) == ("EQW", "HACKDEMO", True)


def test_committed_demo_wav_gives_exactly_one_alert():
    assert_one_demo_eqw(alerts_on_hub_from("--file", str(DEMO_WAV)))


def test_rehearsal_then_stage_play_in_one_run_gives_two_alerts(tmp_path):
    both = tmp_path / "both.wav"
    subprocess.run(["sox", str(REHEARSAL_WAV), str(DEMO_WAV), str(both)], check=True)
    assert len(alerts_on_hub_from("--file", str(both))) == 2


def test_fresh_file_played_at_48k_still_gives_one_alert(tmp_path):
    made = tmp_path / "made.wav"
    assert make_same([str(made)]) == 0
    phone = tmp_path / "phone48k.wav"
    subprocess.run(["sox", str(made), "-r", "48000", str(phone)], check=True)
    assert_one_demo_eqw(alerts_on_hub_from("--file", str(phone)))


def test_pi_mode_records_from_the_usb_card_and_gives_one_alert(tmp_path):
    raw = tmp_path / "demo.raw"
    subprocess.run(["sox", str(DEMO_WAV), "-t", "raw", str(raw)], check=True)
    calls = tmp_path / "arecord.calls"
    fake = tmp_path / "bin" / "arecord"
    fake.parent.mkdir()
    fake.write_text(f"""#!/bin/bash
echo "$*" >> {calls}
if [ "$1" = "-l" ]; then
  echo "**** List of CAPTURE Hardware Devices ****"
  echo "card 2: Device [USB Audio Device], device 0: USB Audio [USB Audio]"
  exit 0
fi
cat {raw}
""")
    fake.chmod(0o755)
    got = alerts_on_hub_from(env={"PATH": f"{fake.parent}:{os.environ['PATH']}"})
    assert_one_demo_eqw(got)
    assert "-D plughw:2,0 -f S16_LE -r 22050 -c 1" in calls.read_text()


def test_stdin_mode_takes_multimon_lines_from_the_radio():
    lines = b"Enabled demodulators: EAS\nEAS: ZCZC-WXR-TOR-048113+0045-3112310-KFWD/NWS-\nEAS: NNNN\n"
    got = alerts_on_hub_from("--stdin", stdin=lines)
    assert [(a["code"], a["demo"]) for a in got] == [("TOR", False)]


def test_listen_stops_at_once_when_the_python_side_cannot_start():
    out = subprocess.run(["bash", str(LISTEN), "--file", str(DEMO_WAV)], capture_output=True, text=True,
                         timeout=20, env={**os.environ, "PYTHON": "/nonexistent/python"})
    assert out.returncode != 0
    assert "cannot run same_to_alert" in out.stderr
