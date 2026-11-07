from software.voice.__main__ import pick_mode


def test_online_without_key_falls_back_to_offline():
    assert pick_mode("online", {}) == ("offline", "MOCK/OFFLINE: no ELEVENLABS_API_KEY")
    assert pick_mode(None, {"ELEVENLABS_API_KEY": ""}) == ("offline", "MOCK/OFFLINE: no ELEVENLABS_API_KEY")


def test_online_with_key():
    assert pick_mode(None, {"ELEVENLABS_API_KEY": "k"}) == ("online", None)


def test_offline_and_text_ignore_the_key():
    assert pick_mode("offline", {"ELEVENLABS_API_KEY": "k"}) == ("offline", None)
    assert pick_mode("text", {}) == ("text", None)
