"""The alarm rule (Rafael's v2, issue #13). Code decides, never the LLM."""

ALARM = "alarm"
NO_ALARM = "no_alarm"
LOG_OK = "log_ok"

ANSWERS = ("ok", "help", "no_answer")
MAX_TRIES = 3


def decide(someone_detected: bool, answer: str) -> str:
    if answer not in ANSWERS:
        raise ValueError(f"unknown answer {answer!r}")
    if answer == "help":
        return ALARM
    if answer == "ok":
        return LOG_OK
    return ALARM if someone_detected else NO_ALARM


def someone_detected(presence: str) -> bool:
    return presence in ("moving", "still")
