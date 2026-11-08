"""The case table must agree with the code it claims to follow."""

from software.agent import rule
from software.eval.cases import CASES
from software.voice.classify import classify


def test_expected_answers_are_what_the_voice_classifier_says():
    for case in CASES:
        heard = tuple(classify(t) for t in case.transcripts[:len(case.answers)])
        assert heard == case.answers, case.id


def test_expected_alarm_follows_rule_decide():
    for case in CASES:
        someone = rule.someone_detected(case.presence)
        alarm_after = None
        for n, answer in enumerate(case.answers[:rule.MAX_TRIES], 1):
            verdict = rule.decide(someone, answer)
            if verdict == rule.ALARM and (answer == "help" or n == rule.MAX_TRIES):
                alarm_after = n
                break
            if verdict != rule.ALARM:
                break
        assert alarm_after == case.alarm_after, case.id
