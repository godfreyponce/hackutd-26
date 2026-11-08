"""Every line the box says or sends, by id. The LLM picks ids, never text.

The ask wording is still open between Godfrey and Rafael. The default is
"ask_stopped". Set AGENT_ASK_SCRIPT=ask_event for the originally agreed line.
"""

SCRIPTS = {
    "ask_stopped": "I noticed you stopped moving. Are you okay? Please respond.",
    "ask_event": "I've detected a fall. Are you okay? Please respond.",
    "standup_ask": "Are you okay?",
    "escalate": "Alerting your emergency contact now.",
}

ASK_SCRIPTS = ("ask_stopped", "ask_event")
STANDUP_SCRIPT = "standup_ask"
ESCALATE_SCRIPT = "escalate"

# Sent only to TWILIO_TO, a verified teammate phone. Never an emergency number.
SMS_TEMPLATES = {
    "no_response": "HackUTD home safety demo: no response after an event at the box. Test alarm only.",
    "answered_ok": "HackUTD home safety demo: the person at the box answered that they are okay.",
}

ALARM_CALL_TEXT = (
    "This is a test alarm from the HackUTD home safety demo. "
    "There was no response after an event at the box."
)
