"""The scripted cases. Every expected outcome comes from the code, not from the issue text.

software/voice/classify.py turns a transcript into ok, help or no_answer.
software/agent/rule.py: help -> alarm, ok -> log only, no_answer -> alarm if someone is
detected (presence moving or still), else no alarm.
software/agent/checkin.py: a no_answer with someone detected asks again until
rule.MAX_TRIES (3) tries; the alarm is raised after the 3rd. A no_answer with nobody
detected ends the check-in at once with outcome no_alarm (one ask only).
A still -> moving presence change after the alarm asks "Are you okay?" once; ok clears it.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Case:
    id: str
    title: str
    trigger: str  # quake | fall_hint | help_gesture
    presence: str  # moving | still | none, sent before the event
    transcripts: tuple  # what the person says at each listen; "" is silence
    answers: tuple  # expected checkin answer states, in order
    outcomes: tuple  # expected outcome in each "Decision:" row (two rows when the person stands up)
    alarm_after: int | None  # the alarm comes right after this many answers; None: never
    standup: bool = False  # send presence moving once the alarm is on screen
    why: str = ""


SILENCE3 = ("", "", "")

CASES = (
    Case("ok", "Event, someone there, says \"I'm okay\"", "quake", "moving", ("I'm okay",),
         ("ok",), ("ok",), None,
         why="classify: okay -> ok. rule.decide: ok -> log_ok. One ask, no alarm."),
    Case("help", "Event, someone there, says \"Help\"", "help_gesture", "moving", ("Help",),
         ("help",), ("alarm",), 1,
         why="classify: help -> help. rule.decide: help -> alarm after the 1st answer."),
    Case("silence", "Event, someone there (still), silent 3 times", "fall_hint", "still", SILENCE3,
         ("no_answer",) * 3, ("alarm",), 3,
         why="Empty transcript -> no_answer. Someone detected: ask again up to 3 tries, alarm after the 3rd."),
    Case("nobody", "Event, nobody there, silent", "quake", "none", SILENCE3,
         ("no_answer",), ("no_alarm",), None,
         why="rule.decide(someone=False, no_answer) -> no_alarm on the 1st miss. The box asks once and stops."),
    Case("unclear_then_ok", "Unclear reply, then \"yeah, I'm fine\"", "fall_hint", "still",
         ("um, what was that", "yeah, I'm fine"),
         ("no_answer", "ok"), ("ok",), None,
         why="classify: no help, negation or ok word -> no_answer, so it counts as a miss and the box asks "
             "again. The 2nd reply is ok -> log only."),
    Case("hedge", "Hedged reply \"I'm not sure\"", "fall_hint", "still", ("I'm not sure",),
         ("help",), ("alarm",), 1,
         why="classify: any negation (not) counts as help, so a hedge raises the alarm after the 1st answer."),
    Case("still_vs_moving_still", "Quake, presence still, silent 3 times", "quake", "still", SILENCE3,
         ("no_answer",) * 3, ("alarm",), 3,
         why="rule.someone_detected: still counts as someone. Same as moving."),
    Case("still_vs_moving_moving", "Quake, presence moving, silent 3 times", "quake", "moving", SILENCE3,
         ("no_answer",) * 3, ("alarm",), 3,
         why="rule.someone_detected: moving counts as someone. Same as still."),
    Case("standup", "Alarm, then the person stands up and says \"I'm okay\"", "fall_hint", "still",
         (*SILENCE3, "I'm okay"), ("no_answer",) * 3 + ("ok",), ("alarm", "clear"), 3, standup=True,
         why="checkin._on_presence: still -> moving after the alarm asks standup_ask once. ok -> outcome clear."),
)

EVENT_EXTRAS = {"quake": {"peak_g": 0.82}, "help_gesture": {"source": "camera"}, "fall_hint": {}}


def event_msg(case: Case) -> dict:
    return {"type": case.trigger, **EVENT_EXTRAS[case.trigger]}
