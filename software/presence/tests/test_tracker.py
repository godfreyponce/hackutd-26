from software.presence.tracker import FALL_HINT_COOLDOWN_S, Tracker

# 8 frames per second keeps every frame time exact in binary floats.
FPS = 8


def box(cx=0.5, cy=0.5, w=0.2, h=0.4, score=0.9):
    return [cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2, score]


def run(tracker, t0, seconds, frame):
    """Feed FPS frames per second from t0. frame(t) gives the box list. Returns [(t, event)]."""
    out = []
    for i in range(int(seconds * FPS)):
        t = t0 + i / FPS
        out += [(t, e) for e in tracker.update(t, frame(t))]
    return out


def walking(t0):
    """Walks 10% of the frame width per second."""
    return lambda t: [box(cx=0.1 + 0.1 * (t - t0))]


def jitter(t):
    """A still person: the detector box wobbles by 1%."""
    k = int(t * FPS) % 3 - 1
    return [box(cx=0.5 + 0.01 * k, cy=0.5 - 0.01 * k, w=0.2 + 0.005 * k)]


def empty(t):
    return []


def drop_frames_3_and_4_of_8(frame):
    return lambda t: [] if int(t * FPS) % 8 in (3, 4) else frame(t)


def states(events):
    return [(t, e["state"]) for t, e in events if e["type"] == "presence"]


def hints(events):
    return [t for t, e in events if e["type"] == "fall_hint"]


def test_nothing_sent_before_the_first_state_is_known():
    assert run(Tracker(), 0, 2, jitter) == []


def test_walking_gives_moving():
    assert states(run(Tracker(), 0, 2, walking(0))) == [(0.5, "moving")]


def test_small_jitter_gives_still_after_3_s():
    events = run(Tracker(), 0, 4, jitter)
    assert states(events) == [(3.0, "still")]
    assert hints(events) == []


def test_a_low_score_box_is_not_a_person():
    assert states(run(Tracker(), 0, 6, lambda t: [box(score=0.3)])) == [(5.0, "none")]


def test_the_largest_box_is_tracked():
    big_still_and_small_walking = lambda t: [box(w=0.3, h=0.6), box(cx=0.1 + 0.1 * t, w=0.05, h=0.1)]
    assert states(run(Tracker(), 0, 4, big_still_and_small_walking)) == [(3.0, "still")]


def test_empty_frames_give_none_5_s_after_moving():
    tr = Tracker()
    run(tr, 0, 2, walking(0))  # moving at 0.5, last person frame at 1.875
    assert states(run(tr, 2, 6, empty)) == [(5.5, "moving"), (6.875, "none")]


def test_empty_frames_give_none_20_s_after_still():
    tr = Tracker()
    run(tr, 0, 4, jitter)  # still at 3.0, last person frame at 3.875
    events = run(tr, 4, 21, empty)
    assert states(events) == [(8.0, "still"), (13.0, "still"), (18.0, "still"), (23.0, "still"), (23.875, "none")]


def test_two_missed_frames_change_nothing_while_still():
    tr = Tracker()
    run(tr, 0, 4, jitter)  # still at 3.0
    assert states(run(tr, 4, 5, drop_frames_3_and_4_of_8(jitter))) == [(8.0, "still")]


def test_two_missed_frames_change_nothing_while_moving():
    tr = Tracker()
    run(tr, 0, 1, walking(0))  # moving at 0.5
    assert states(run(tr, 1, 5, drop_frames_3_and_4_of_8(walking(0)))) == [(5.5, "moving")]


def test_a_person_who_stops_is_still_3_s_after_the_last_motion():
    tr = Tracker()
    run(tr, 0, 2, walking(0))
    # The walking samples stay in the 1 s window until 2.875, so the last motion is at 2.875.
    assert states(run(tr, 2, 5, jitter)) == [(5.5, "moving"), (5.875, "still")]


def test_moving_then_still_sends_still_then_one_fall_hint():
    tr = Tracker()
    run(tr, 0, 2, walking(0))
    events = run(tr, 2, 5, jitter)
    assert [(t, e["type"], e.get("state")) for t, e in events] == [
        (5.5, "presence", "moving"),
        (5.875, "presence", "still"),
        (5.875, "fall_hint", None),
    ]


def test_fall_hint_respects_its_cooldown():
    tr = Tracker()
    sent = []
    for t0 in (0, 6, 12):
        sent += hints(run(tr, t0, 2, walking(t0)))
        sent += hints(run(tr, t0 + 2, 4, jitter))
    assert sent == [5.875]
    t0 = FALL_HINT_COOLDOWN_S
    sent += hints(run(tr, t0, 2, walking(t0)))
    sent += hints(run(tr, t0 + 2, 4, jitter))
    assert sent == [5.875, 5.875 + FALL_HINT_COOLDOWN_S]


def test_no_fall_hint_when_switched_off():
    tr = Tracker(fall_hint=False)
    run(tr, 0, 2, walking(0))
    events = run(tr, 2, 5, jitter)
    assert states(events) == [(5.5, "moving"), (5.875, "still")]
    assert hints(events) == []


def test_no_fall_hint_for_a_person_who_was_still_from_the_start():
    assert hints(run(Tracker(), 0, 10, jitter)) == []


def test_current_state_repeats_every_5_s():
    assert states(run(Tracker(), 0, 18.5, jitter)) == [(3.0, "still"), (8.0, "still"), (13.0, "still"), (18.0, "still")]


def test_a_person_back_after_a_gap_is_not_still_at_once():
    tr = Tracker()
    run(tr, 0, 2, walking(0))
    run(tr, 2, 4, empty)
    events = run(tr, 6, 2, walking(6))
    assert states(events) == []
    assert hints(events) == []


def test_frames_stopping_for_a_while_do_not_make_a_walker_still():
    tr = Tracker()
    run(tr, 0, 2, walking(0))
    events = run(tr, 5.5, 2, walking(0))
    assert states(events) == [(5.5, "moving")]
    assert hints(events) == []
