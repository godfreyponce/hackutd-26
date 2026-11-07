import pytest

from software.agent.rule import ALARM, LOG_OK, NO_ALARM, decide


@pytest.mark.parametrize(
    "someone, answer, expected",
    [
        (False, "no_answer", NO_ALARM),
        (True, "no_answer", ALARM),
        (False, "help", ALARM),
        (True, "help", ALARM),
        (False, "ok", LOG_OK),
        (True, "ok", LOG_OK),
    ],
)
def test_alarm_rule_table(someone, answer, expected):
    assert decide(someone, answer) == expected


def test_unknown_answer_is_rejected():
    with pytest.raises(ValueError):
        decide(True, "maybe")
