import concurrent.futures
import json
import os
import subprocess
import sys

from software.same.same_to_alert import alerts, parse_line

DEMO_EQW = "EAS: ZCZC-WXR-EQW-048113-048085+0030-3112300-HACKDEMO-"
REAL_TOR = "EAS: ZCZC-WXR-TOR-048113+0045-3112310-KFWD/NWS-"
EOM = "EAS: NNNN"


def one(*lines):
    got = list(alerts(lines))
    assert len(got) == 1, got
    return got[0]


def test_header_line_is_parsed_into_its_fields():
    kind, h = parse_line(REAL_TOR)
    assert kind == "header"
    assert (h.org, h.code, h.locations, h.duration, h.issued, h.station) == (
        "WXR", "TOR", ("048113",), "0045", "3112310", "KFWD/NWS")


def test_eom_and_noise_lines():
    assert parse_line(EOM) == ("eom", None)
    assert parse_line("Enabled demodulators: EAS") is None
    assert parse_line("EAS (part): ZCZC-WXR-TOR-048113+0045-3112310-KFWD/NWS-") is None
    assert parse_line("EAS: ZCZC-garbage") is None
    assert parse_line("") is None


def test_timestamp_prefix_from_multimon_t_flag_is_accepted():
    kind, h = parse_line("2026-11-07 22:10:00: " + REAL_TOR)
    assert kind == "header" and h.code == "TOR"


def test_demo_header_maps_to_the_shared_alert_contract():
    alert = one(DEMO_EQW)
    assert alert.items() >= {
        "type": "alert",
        "source": "noaa",
        "event": "Earthquake Warning",
        "code": "EQW",
        "station": "HACKDEMO",
        "severity": "Severe",
        "urgency": "Immediate",
        "certainty": "Likely",
        "area": "Dallas County, TX; Collin County, TX",
        "headline": "Earthquake Warning for Dallas County, TX; Collin County, TX",
        "demo": True,
    }.items()
    # added for "when / who" questions to the box: sender, local issue time, minutes valid, expiry
    assert alert["sender"] == "National Weather Service" and alert["valid_minutes"] > 0
    assert {"issued", "expires"} <= alert.keys()


def test_three_repeats_send_one_alert():
    assert len(list(alerts([DEMO_EQW, DEMO_EQW, DEMO_EQW, EOM, EOM, EOM]))) == 1


def test_same_header_after_end_of_message_alerts_again():
    lines = [DEMO_EQW, EOM, DEMO_EQW, EOM]
    assert len(list(alerts(lines))) == 2


def test_different_headers_each_alert():
    got = list(alerts([DEMO_EQW, REAL_TOR]))
    assert [a["code"] for a in got] == ["EQW", "TOR"]


def test_other_county_is_dropped():
    assert list(alerts(["EAS: ZCZC-WXR-TOR-048439+0045-3112310-KFWD/NWS-"])) == []


def test_our_county_among_others_alerts_and_counts_the_others():
    a = one("EAS: ZCZC-WXR-TOR-048439-048113-048121+0045-3112310-KFWD/NWS-")
    assert a["area"] == "Dallas County, TX and 2 other areas"
    assert a["headline"] == "Tornado Warning for Dallas County, TX and 2 other areas"


def test_part_of_our_county_counts_as_ours():
    assert one("EAS: ZCZC-WXR-TOR-148113+0045-3112310-KFWD/NWS-")["area"] == "Dallas County, TX"


def test_whole_state_without_our_county_is_dropped():
    assert list(alerts(["EAS: ZCZC-CIV-CEM-048000+0100-3112310-TXDPS   -"])) == []


def test_national_alert_is_kept():
    a = one("EAS: ZCZC-PEP-NPT-000000+0030-3112310-WHITEHSE-")
    assert a["area"] == "United States"
    assert a["event"] == "National Periodic Test"
    assert (a["severity"], a["urgency"], a["certainty"]) == ("Unknown",) * 3
    assert a["demo"] is False


def test_real_warning_is_not_demo():
    a = one(REAL_TOR)
    assert a["demo"] is False and a["station"] == "KFWD/NWS"


def test_dmo_code_is_demo_from_any_station():
    assert one("EAS: ZCZC-WXR-DMO-048113+0030-3112310-KFWD/NWS-")["demo"] is True


def test_headline_stays_plain_for_demo_and_test_messages():
    for code, station in [("EQW", "HACKDEMO"), ("DMO", "KFWD/NWS"), ("RWT", "KFWD/NWS")]:
        a = one(f"EAS: ZCZC-WXR-{code}-048113+0030-3112310-{station}-")
        assert a["headline"] == f"{a['event']} for Dallas County, TX"


def test_cap_defaults_by_significance():
    def cap(code):
        a = one(f"EAS: ZCZC-WXR-{code}-048113+0030-3112310-KFWD/NWS-")
        return a["severity"], a["urgency"], a["certainty"]

    assert cap("TOA") == ("Severe", "Future", "Possible")
    assert cap("SVS") == ("Moderate", "Expected", "Likely")
    assert cap("CAE") == ("Severe", "Immediate", "Likely")
    assert cap("RWT") == ("Unknown", "Unknown", "Unknown")


def test_unknown_code_keeps_the_code_and_unknown_cap_fields():
    a = one("EAS: ZCZC-WXR-XYZ-048113+0030-3112310-KFWD/NWS-")
    assert a["event"] == "Unknown alert (XYZ)" and a["code"] == "XYZ"
    assert (a["severity"], a["urgency"], a["certainty"]) == ("Unknown",) * 3


def run_cli(lines, *args, env=None):
    return subprocess.run(
        [sys.executable, "-m", "software.same.same_to_alert", *args],
        input="\n".join(lines) + "\n", capture_output=True, text=True, timeout=20, env=env)


def test_dry_run_prints_one_json_line_per_alert():
    out = run_cli(["Enabled demodulators: EAS", DEMO_EQW, EOM, EOM, EOM], "--dry-run")
    assert out.returncode == 0, out.stderr
    lines = out.stdout.splitlines()
    assert len(lines) == 1 and json.loads(lines[0])["code"] == "EQW"


def test_stderr_names_skipped_and_unreadable_headers():
    out = run_cli(["EAS: ZCZC-WXR-TOR-048439+0045-3112310-KFWD/NWS-", "EAS: ZCZC-WXR-EQW-048113-"], "--dry-run")
    assert out.stdout == ""
    assert out.stderr.splitlines() == [
        "skipped, not our area: ZCZC-WXR-TOR-048439+0045-3112310-KFWD/NWS-",
        "could not read header: EAS: ZCZC-WXR-EQW-048113-",
    ]


def test_hub_down_prints_the_alert_reports_the_error_and_keeps_going(unused_url):
    env = {**os.environ, "HUB_URL": unused_url}
    out = run_cli([DEMO_EQW, REAL_TOR], env=env)
    assert out.returncode == 0
    assert [json.loads(l)["code"] for l in out.stdout.splitlines()] == ["EQW", "TOR"]
    assert out.stderr.count("could not send") == 2


def test_alert_comes_out_while_stdin_stays_open():
    proc = subprocess.Popen(
        [sys.executable, "-m", "software.same.same_to_alert", "--dry-run"],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
    try:
        proc.stdin.write(DEMO_EQW + "\n")
        proc.stdin.flush()
        line = run_with_timeout(proc.stdout.readline, 10)
        assert json.loads(line)["code"] == "EQW"
    finally:
        proc.kill()
        proc.wait()


def run_with_timeout(fn, seconds):
    with concurrent.futures.ThreadPoolExecutor(1) as pool:
        return pool.submit(fn).result(timeout=seconds)
