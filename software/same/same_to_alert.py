"""Read multimon-ng EAS lines on stdin and send one hub `alert` per SAME message.

    multimon-ng -t raw -a EAS - | python -m software.same.same_to_alert [--dry-run]

Run from the repo root with the hub venv. Reads HUB_URL. --dry-run prints
the JSON and sends nothing. Keeps Dallas (048113) and Collin (048085)
counties and national alerts; drops the rest.
"""

import argparse
import asyncio
import json
import re
import sys
from dataclasses import dataclass
from typing import Iterable, Iterator

from websockets.exceptions import WebSocketException

from software.hub import hub_url
from software.hub.send import send

# Our CAP defaults by SAME significance. SAME has no severity, urgency or
# certainty; these copy what NWS CAP used for the same kinds of message on
# 2026-11-07 (docs/research/HackUTD-SDR-Alerts.md, section 3).
CAP_BY_SIGNIFICANCE = {
    "W": ("Severe", "Immediate", "Likely"),    # warning
    "E": ("Severe", "Immediate", "Likely"),    # emergency
    "A": ("Severe", "Future", "Possible"),     # watch
    "S": ("Moderate", "Expected", "Likely"),   # statement
    "T": ("Unknown", "Unknown", "Unknown"),    # test
}

# SAME event code: (readable name, significance). From the NWS NWR event
# code list and 47 CFR 11.31 Table 2.
EVENTS = {
    "BZW": ("Blizzard Warning", "W"),
    "CFA": ("Coastal Flood Watch", "A"),
    "CFW": ("Coastal Flood Warning", "W"),
    "DSW": ("Dust Storm Warning", "W"),
    "EWW": ("Extreme Wind Warning", "W"),
    "FFA": ("Flash Flood Watch", "A"),
    "FFW": ("Flash Flood Warning", "W"),
    "FFS": ("Flash Flood Statement", "S"),
    "FLA": ("Flood Watch", "A"),
    "FLW": ("Flood Warning", "W"),
    "FLS": ("Flood Statement", "S"),
    "HWA": ("High Wind Watch", "A"),
    "HWW": ("High Wind Warning", "W"),
    "HUA": ("Hurricane Watch", "A"),
    "HUW": ("Hurricane Warning", "W"),
    "HLS": ("Hurricane Statement", "S"),
    "SVA": ("Severe Thunderstorm Watch", "A"),
    "SVR": ("Severe Thunderstorm Warning", "W"),
    "SVS": ("Severe Weather Statement", "S"),
    "SQW": ("Snow Squall Warning", "W"),
    "SMW": ("Special Marine Warning", "W"),
    "SPS": ("Special Weather Statement", "S"),
    "SSA": ("Storm Surge Watch", "A"),
    "SSW": ("Storm Surge Warning", "W"),
    "TOA": ("Tornado Watch", "A"),
    "TOR": ("Tornado Warning", "W"),
    "TRA": ("Tropical Storm Watch", "A"),
    "TRW": ("Tropical Storm Warning", "W"),
    "TSA": ("Tsunami Watch", "A"),
    "TSW": ("Tsunami Warning", "W"),
    "WSA": ("Winter Storm Watch", "A"),
    "WSW": ("Winter Storm Warning", "W"),
    "AVA": ("Avalanche Watch", "A"),
    "AVW": ("Avalanche Warning", "W"),
    "BLU": ("Blue Alert", "W"),
    "CAE": ("Child Abduction Emergency", "E"),
    "CDW": ("Civil Danger Warning", "W"),
    "CEM": ("Civil Emergency Message", "W"),
    "EQW": ("Earthquake Warning", "W"),
    "EVI": ("Evacuation Immediate", "W"),
    "FRW": ("Fire Warning", "W"),
    "HMW": ("Hazardous Materials Warning", "W"),
    "LAE": ("Local Area Emergency", "E"),
    "LEW": ("Law Enforcement Warning", "W"),
    "NUW": ("Nuclear Power Plant Warning", "W"),
    "RHW": ("Radiological Hazard Warning", "W"),
    "SPW": ("Shelter in Place Warning", "W"),
    "TOE": ("911 Telephone Outage Emergency", "E"),
    "VOW": ("Volcano Warning", "W"),
    "EAN": ("Emergency Action Notification", "W"),
    "NIC": ("National Information Center", "S"),
    "NPT": ("National Periodic Test", "T"),
    "RMT": ("Required Monthly Test", "T"),
    "RWT": ("Required Weekly Test", "T"),
    "ADR": ("Administrative Message", "S"),
    "DMO": ("Practice/Demo Warning", "W"),
    "NMN": ("Network Message Notification", "S"),
}

COUNTIES = {"48113": "Dallas County, TX", "48085": "Collin County, TX"}
NATIONAL = "000000"
DEMO_STATION = "HACKDEMO"

LINE_RE = re.compile(
    r"EAS: (?:(?P<eom>NNNN)|(?P<header>ZCZC-(?P<org>[A-Z]{3})-(?P<code>[A-Z]{3})-(?P<locs>\d{6}(?:-\d{6}){0,30})"
    r"\+(?P<duration>\d{4})-(?P<issued>\d{7})-(?P<station>.{1,8})-))\s*$")


@dataclass(frozen=True)
class Header:
    org: str
    code: str
    locations: tuple[str, ...]
    duration: str
    issued: str
    station: str
    text: str


def parse_line(line: str) -> tuple[str, Header | None] | None:
    m = LINE_RE.search(line)
    if not m:
        return None
    if m["eom"]:
        return "eom", None
    return "header", Header(
        org=m["org"], code=m["code"], locations=tuple(m["locs"].split("-")), duration=m["duration"],
        issued=m["issued"], station=m["station"].strip(), text=m["header"])


def area_of(h: Header) -> str | None:
    """Readable area if the alert covers this home, else None."""
    if NATIONAL in h.locations:
        return "United States"
    ours = list(dict.fromkeys(COUNTIES[loc[1:]] for loc in h.locations if loc[1:] in COUNTIES))
    if not ours:
        return None
    others = sum(1 for loc in h.locations if loc[1:] not in COUNTIES)
    area = "; ".join(ours)
    return f"{area} and {others} other area{'s' if others > 1 else ''}" if others else area


def to_alert(h: Header, area: str) -> dict:
    event, significance = EVENTS.get(h.code, (f"Unknown alert ({h.code})", ""))
    severity, urgency, certainty = CAP_BY_SIGNIFICANCE.get(significance, ("Unknown",) * 3)
    return {
        "type": "alert",
        "source": "noaa",
        "event": event,
        "code": h.code,
        "station": h.station,
        "severity": severity,
        "urgency": urgency,
        "certainty": certainty,
        "area": area,
        "headline": f"{event} for {area}",
        "demo": h.station == DEMO_STATION or h.code == "DMO",
    }


def alerts(lines: Iterable[str]) -> Iterator[dict]:
    """One alert per message: repeats of a header are dropped until its NNNN."""
    seen: set[str] = set()
    for line in lines:
        parsed = parse_line(line)
        if parsed is None:
            if "EAS: ZCZC" in line:
                print(f"could not read header: {line.strip()}", file=sys.stderr, flush=True)
            continue
        kind, h = parsed
        if kind == "eom":
            seen.clear()
            continue
        if h.text in seen:
            continue
        seen.add(h.text)
        area = area_of(h)
        if area is None:
            print(f"skipped, not our area: {h.text}", file=sys.stderr, flush=True)
            continue
        yield to_alert(h, area)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dry-run", action="store_true", help="print the JSON, send nothing")
    args = parser.parse_args(argv)
    try:
        for msg in alerts(sys.stdin):
            print(json.dumps(msg), flush=True)
            if args.dry_run:
                continue
            try:
                asyncio.run(send(hub_url(), msg))
            except (OSError, WebSocketException) as e:
                print(f"could not send to {hub_url()}: {e}", file=sys.stderr, flush=True)
    except KeyboardInterrupt:
        return 130
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
