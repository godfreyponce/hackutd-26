"""Turn a transcript into ok, help or no_answer. Keyword match only, no LLM.

Order matters: a help word wins over everything, then any negation counts as help
(so "not okay" and "no" never become ok), then an ok word, else no_answer.
"""

import re

HELP = re.compile(r"\b(help|hurt|emergency|can ?not get up|can't get up|cant get up)")
NEGATION = re.compile(r"\b(no|nope|nah|not|never)\b|n't\b")
OK = re.compile(r"\b(yes|yeah|yep|yup|okay|ok|fine|alright|all right|good)\b")


def classify(transcript: str | None) -> str:
    text = (transcript or "").lower().replace("’", "'")
    if HELP.search(text) or NEGATION.search(text):
        return "help"
    if OK.search(text):
        return "ok"
    return "no_answer"
