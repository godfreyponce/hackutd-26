import pytest

from software.voice.classify import classify

TABLE = [
    # help wins over everything
    ("help", "help"),
    ("Help me.", "help"),
    ("help me please", "help"),
    ("I'm hurt", "help"),
    ("it hurts", "help"),
    ("this is an emergency", "help"),
    ("I can't get up", "help"),
    ("I can’t get up", "help"),  # curly apostrophe from a transcriber
    ("I'm okay but I need help", "help"),
    ("yes help", "help"),
    # a negated answer must never become ok
    ("I'm not okay", "help"),
    ("not okay", "help"),
    ("I'm not ok.", "help"),
    ("I'm not fine", "help"),
    ("I'm not alright", "help"),
    ("no", "help"),
    ("No.", "help"),
    ("nope", "help"),
    ("I don't feel okay", "help"),
    # ok
    ("yes", "ok"),
    ("Yeah, I'm okay.", "ok"),
    ("yeah I'm okay", "ok"),
    ("okay", "ok"),
    ("ok", "ok"),
    ("I'm ok.", "ok"),
    ("I'm fine", "ok"),
    ("I'm alright", "ok"),
    ("I'm all right", "ok"),
    ("yep I'm good", "ok"),
    # silence or unrelated speech
    ("", "no_answer"),
    ("   ", "no_answer"),
    ("the weather is nice today", "no_answer"),
    ("I know", "no_answer"),  # "know" is not "no"
    ("token", "no_answer"),  # "token" is not "ok"
    ("Good boy", "no_answer"),  # a real mishearing of room chatter; "good" is not an answer
    ("I'm good", "no_answer"),
]


@pytest.mark.parametrize("transcript,expected", TABLE)
def test_classify(transcript, expected):
    assert classify(transcript) == expected


def test_none_is_no_answer():
    assert classify(None) == "no_answer"
