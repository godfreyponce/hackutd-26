"""Turn a transcript into ok, help or no_answer. Keyword match only, no LLM.

Order matters: a help word wins over everything, then any negation counts as help
(so "not okay" and "no" never become ok), then an ok word, else no_answer.
"""

import re

# "fell asleep" and "fallen asleep" answer about sleep, not a fall.
HELP = re.compile(
    r"\b(help|hurt|emergency|ambulance|bleed|chest pain"
    r"|(can ?not|can't|cant) (get up|breathe?)"
    r"|(fell|fallen)\b(?! asleep)"
    r"|on the (floor|ground))"
)
# cant, dont ... aint: -n't words as a transcriber may write them, with no apostrophe.
NEGATION = re.compile(
    r"\b(no|nope|nah|not|never|cannot"
    r"|cant|dont|wont|didnt|doesnt|isnt|wasnt|arent|werent"
    r"|couldnt|wouldnt|shouldnt|havent|hasnt|hadnt|aint)\b|n't\b"
)
OK = re.compile(r"\b(yes|yeah|yep|yup|okay|ok|fine|alright|all right)\b")


def classify(transcript: str | None) -> str:
    text = re.sub(r"\s+", " ", (transcript or "").lower().replace("’", "'"))
    if HELP.search(text) or NEGATION.search(text):
        return "help"
    if OK.search(text):
        return "ok"
    return "no_answer"
