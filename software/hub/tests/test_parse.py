import pytest

from software.hub.bus import BadMessage, parse_message


def test_adds_t_when_missing():
    assert parse_message('{"type":"fall_hint"}', now_ms=42) == {"type": "fall_hint", "t": 42}


def test_keeps_existing_t():
    assert parse_message('{"type":"quake","peak_g":0.8,"t":7}', now_ms=42)["t"] == 7


def test_accepts_bytes():
    assert parse_message(b'{"type":"reset"}', now_ms=1) == {"type": "reset", "t": 1}


@pytest.mark.parametrize("raw", ["not json", "{bad", ""])
def test_rejects_bad_json(raw):
    with pytest.raises(BadMessage, match="not JSON"):
        parse_message(raw, now_ms=1)


@pytest.mark.parametrize("raw", ["[1,2]", '"quake"', "3", "null"])
def test_rejects_non_object(raw):
    with pytest.raises(BadMessage, match="not a JSON object"):
        parse_message(raw, now_ms=1)
