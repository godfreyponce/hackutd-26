"""Map an official alert to the level the screens and the agent act on (issue #35)."""

LEVELS = ("info", "watch", "warning", "emergency")

TEST_CODES = {"RWT", "RMT", "NPT", "DMO"}
EMERGENCY_CODES = {"EQW", "TOR", "CEM", "CAE", "EVI", "SPW"}
WARNING_CODES_NOT_ENDING_IN_W = {"SVR"}
SEVERITY_LEVELS = {"Extreme": "emergency", "Severe": "warning", "Moderate": "watch"}
FAR_MI = 25


def code_level(code: str) -> str | None:
    if code in TEST_CODES:
        return "info"
    if code in EMERGENCY_CODES:
        return "emergency"
    if code.endswith("A"):
        return "watch"
    if code.endswith("W") or code in WARNING_CODES_NOT_ENDING_IN_W:
        return "warning"
    return None


def alert_level(alert: dict) -> str:
    """Pure. SAME code first, CAP severity when the code is missing or unknown, one step lower when far away."""
    code = alert.get("code")
    code = code.strip().upper() if isinstance(code, str) else ""
    level = code_level(code) if code else None
    if level is None:
        severity = alert.get("severity")
        level = SEVERITY_LEVELS.get(severity, "info") if isinstance(severity, str) else "info"
    distance = alert.get("distance_mi")
    if isinstance(distance, (int, float)) and not isinstance(distance, bool) and distance > FAR_MI:
        level = LEVELS[max(0, LEVELS.index(level) - 1)]
    return level
