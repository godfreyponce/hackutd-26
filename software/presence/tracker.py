"""Person boxes in, presence events out. Pure code: no clock, no I/O.

Boxes are frame fractions (x0, y0, x1, y1 in 0..1) plus a score, so the lens
(wide or fisheye) does not matter. Every number below is a guess for the demo,
not a measured value. Tune them on the Pi.
"""

import math
from collections import deque

MIN_SCORE = 0.4  # a box below this score is not a person
MOVE_WINDOW_S = 1.0  # motion is judged against the boxes of the last second
MOVE_CENTER = 0.04  # center moves more than 4% of the frame: moving
MOVE_AREA = 0.15  # box area changes more than 15%: moving
MOVE_MIN_FRAMES = 2  # motion must show in this many frames in a row, so one bad box is not moving
STILL_AFTER_S = 3.0  # no motion for this long: still
NONE_AFTER_MOVING_S = 5.0  # no person for this long after moving (or at start): none
NONE_AFTER_STILL_S = 60.0  # longer after still, so a person lying down does not flip to none during a check-in
REPEAT_S = 5.0  # resend the current state this often (restores presence after a hub reset)
FALL_HINT_COOLDOWN_S = 60.0  # at most one fall_hint per this many seconds


def largest_person(boxes, min_score=MIN_SCORE):
    people = [b for b in boxes if b[4] >= min_score]
    if not people:
        return None
    x0, y0, x1, y1, _ = max(people, key=lambda b: (b[2] - b[0]) * (b[3] - b[1]))
    return ((x0 + x1) / 2, (y0 + y1) / 2), (x1 - x0) * (y1 - y0)


def _moved(a, b):
    (ca, area_a), (cb, area_b) = a, b
    return math.dist(ca, cb) > MOVE_CENTER or abs(area_b - area_a) > MOVE_AREA * area_a


class Tracker:
    """Feed one update(t, boxes) per camera frame, also frames with no boxes.

    State starts unknown and nothing is sent until it is moving, still or none.
    """

    def __init__(self, fall_hint=True, fall_hint_cooldown_s=FALL_HINT_COOLDOWN_S):
        self.fall_hint = fall_hint
        self.fall_hint_cooldown_s = fall_hint_cooldown_s
        self.state = None
        self.started = None
        self.last_seen = None
        self.quiet_since = None
        self.window = deque()  # (t, (center, area)) of the last MOVE_WINDOW_S
        self.moved_frames = 0
        self.last_sent = None
        self.last_hint = None

    def update(self, t, boxes):
        if self.started is None:
            self.started = t
        person = largest_person(boxes)
        new = self._next_state(t, person) if person else self._state_without_person(t)
        events = []
        if new != self.state:
            events.append({"type": "presence", "state": new})
            if self._hint_due(t, self.state, new):
                events.append({"type": "fall_hint"})
                self.last_hint = t
            self.state, self.last_sent = new, t
        elif new is not None and t - self.last_sent >= REPEAT_S:
            events.append({"type": "presence", "state": new})
            self.last_sent = t
        return events

    def _next_state(self, t, person):
        if self.last_seen is None or t - self.last_seen > MOVE_WINDOW_S:
            # Back after a gap: the 3 s for still count only time the person was seen.
            self.quiet_since = t
        self.last_seen = t
        while self.window and self.window[0][0] < t - MOVE_WINDOW_S:
            self.window.popleft()
        moved = any(_moved(old, person) for _, old in self.window)
        self.moved_frames = self.moved_frames + 1 if moved else 0
        if 0 < self.moved_frames < MOVE_MIN_FRAMES:
            # Kept out of the window: if it is a bad box, the next frames must not be judged against it.
            return self.state
        self.window.append((t, person))
        if moved:
            self.quiet_since = t
            return "moving"
        if t - self.quiet_since >= STILL_AFTER_S:
            return "still"
        return self.state

    def _state_without_person(self, t):
        if self.state == "none":
            return "none"
        since = self.started if self.last_seen is None else self.last_seen
        limit = NONE_AFTER_STILL_S if self.state == "still" else NONE_AFTER_MOVING_S
        if t - since < limit:
            return self.state
        self.last_seen = None
        self.window.clear()
        return "none"

    def hub_reset(self):
        self.last_hint = None

    def _hint_due(self, t, old, new):
        return (
            self.fall_hint
            and old == "moving"
            and new == "still"
            and (self.last_hint is None or t - self.last_hint >= self.fall_hint_cooldown_s)
        )
