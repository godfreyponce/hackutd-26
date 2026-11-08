"""Every line the box says or sends, by id. The LLM picks ids, never text.

The ask wording is still open between Godfrey and Rafael. The default is
"ask_stopped". Set AGENT_ASK_SCRIPT=ask_event for the originally agreed line.
"""

# Every line the agent says or writes about an alert with demo true carries these words.
DEMO_TEXT = "DEMO, not a real alert"

SCRIPTS = {
    "ask_stopped": "Hey, I noticed you stopped moving. Are you okay?",
    "ask_event": "Something just happened. Are you okay? Please respond.",
    "ask_gesture": "I saw your help sign. Are you okay? Say okay, or help.",
    "ask_retry_2": "I didn't catch that. Are you okay? Just say okay, or help.",
    "ask_retry_3": "I still can't hear you. If I don't hear from you, I'll get help. Are you okay?",
    "standup_ask": "Are you okay?",
    "escalate": "I haven't heard back, so I'm alerting your emergency contact now.",
    "reply_help": "Okay. I'm getting help now. Stay with me, you're not alone.",
    "reply_ok": "Good. I'm glad you're okay. I'll check on you again soon.",
    "alert_demo": f"{DEMO_TEXT}.",
}

ASK_SCRIPTS = ("ask_stopped", "ask_event", "ask_gesture")
# An EQW emergency alert check-in always asks with this line, whatever AGENT_ASK_SCRIPT says.
ALERT_ASK_SCRIPT = "ask_event"
# A camera help sign check-in always asks with this line. It asks "are you okay", not "do you
# need help", because the voice classifier hears "yes" as ok.
GESTURE_ASK_SCRIPT = "ask_gesture"
# Said before the first ask when the alert has demo true.
ALERT_DEMO_SCRIPT = "alert_demo"
# The `tone` field on the first `say` of an EQW alert check-in. The voice service plays a short
# warning tone, then speaks the line. Not the fake alarm's siren, and not the real EAS tones.
ALERT_TONE = "warning"
# Tries 2 and 3. Code picks the line by try number, so the planner cannot skip or reorder them.
RETRY_SCRIPTS = ("ask_retry_2", "ask_retry_3")
STANDUP_SCRIPT = "standup_ask"
ESCALATE_SCRIPT = "escalate"
# The reply each answer gets, spoken without listening.
REPLY_SCRIPTS = {"ok": "reply_ok", "help": "reply_help"}

# Sent only to TWILIO_TO, a verified teammate phone. Never an emergency number.
SMS_TEMPLATES = {
    "no_response": "HackUTD home safety demo: no response after an event at the box. Test alarm only.",
    "answered_ok": "HackUTD home safety demo: the person at the box answered that they are okay.",
    "said_help": "HackUTD home safety demo: the person at the box asked for help after an event. Test alarm only.",
}

ALARM_CALL_TEXT = (
    "This is a test alarm from the HackUTD home safety demo. "
    "There was no response after an event at the box."
)

# Demo contacts the hand-off note may name first. Teammates with role labels, no phone numbers.
# Nothing texts them: the alarm calls and texts only TWILIO_TO.
HANDOFF_CONTACTS = {
    "godfrey": {"name": "Godfrey", "role": "family contact, demo"},
    "rafael": {"name": "Rafael", "role": "neighbor, demo"},
}
