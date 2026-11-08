"""Turn a transcript into ok, help or no_answer. Keyword match only, no LLM.

Order matters: a help word wins over everything, then any negation counts as help
(so "not okay" and "no" never become ok), then an ok word, else no_answer.
One exception: a leading no right before an ok phrase is dropped first ("no, I'm fine").
"""

import re

# fell and the floor count only for the speaker: "a pot fell off the stove" is no fall.
# "fell asleep" and "fallen asleep" answer about sleep, not a fall; "slipped my mind" is no slip.
# Word edges keep "helpful", "painting", "fireplace", "Chester" and "smoker" out.
# doctor, breathe, call, blood and a fire or smoke alarm or detector are narrowed: an ok
# reply uses them ("my doctor said I'm fine"), and a missed help still reaches the alarm
# after 3 asks.
HELP = re.compile(
    r"\b(help(less)?\b|hurt|emergency|ambulance|bleed|injur(ed|y)|paramedic|dizzy"
    r"|(can ?not|can't|cant|can barely|can hardly) (get up|breathe?)"
    r"|(^|i('?ve|'?d| have| had)? (\w+ )?|i [^,.!?]* and )(fell|fallen)\b(?! (back |fast |sound |right )?(asleep|to sleep))"
    r"|(^|(i'?m|i am|been|lying|laying|down)( \w+)? )on the ((kitchen|bathroom) )?(floor|ground)\b(?! floor)"
    r"|(had a fall|heart attack|trouble breathing|hard to breathe?|short(ness)? of breath|hit my head)\b"
    r"|i('ve| have)? (just )?slipped\b(?! my mind| up| out)"
    r"|(need|get|call) (a |the |my )?doctors?\b"
    r"|(fires?|smoke)\b(?![ -](alarm|detector))"
    r"|blood\b(?! pressure| sugar)"
    r"|(pain(s|ed|ful|killers?)?|chest|faint(s|ed|ing)?|trapped"
    r"|firefighters?|fire(man|men)|smok(ed|es|ey))\b"
    r"|(911|9-1-1|9 1 1|nine[ -]one[ -]one)\b|call (someone|somebody)|save me)"
)
# cant, dont ... aint: -n't words as a transcriber may write them, with no apostrophe.
NEGATION = re.compile(
    r"\b(no|nope|nah|not|never|cannot"
    r"|cant|dont|wont|didnt|doesnt|isnt|wasnt|arent|werent"
    r"|couldnt|wouldnt|shouldnt|havent|hasnt|hadnt|aint)\b|n't\b"
)
# "No, I'm fine" answers "did you fall?". The no is dropped only if an ok phrase follows it.
# Bare "good" is left out so "no good" stays help.
LEADING_NO = re.compile(
    r"^ ?((no|nope|nah)\b[,.!]? ?)+"
    r"(?=(i'?m |i am )(doing |all )?good\b|(i'?m |i am )?(okay|ok|fine|alright|all right|all good|doing good)\b)"
)
OK = re.compile(r"\b(yes|yeah|yep|yup|okay|ok|fine|alright|all right|(i'?m|i am)( doing| all)? good|^(all|doing) good)\b")


def classify(transcript: str | None) -> str:
    text = re.sub(r"\s+", " ", (transcript or "").lower().replace("’", "'"))
    text = LEADING_NO.sub("", text, count=1)
    if HELP.search(text) or NEGATION.search(text):
        return "help"
    if OK.search(text):
        return "ok"
    return "no_answer"
