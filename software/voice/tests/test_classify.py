import pytest

from software.voice.classify import classify

TABLE = [
    # help wins over everything
    ("help", "help"),
    ("Help me.", "help"),
    ("help me please", "help"),
    ("I'm hurt", "help"),
    ("it hurts", "help"),
    ("this is an emergency", "help"),
    ("I can't get up", "help"),
    ("I can’t get up", "help"),  # curly apostrophe from a transcriber
    ("I'm okay but I need help", "help"),
    ("yes help", "help"),
    # distress phrases (#68)
    ("I fell", "help"),
    ("I fell down", "help"),
    ("I fell over", "help"),
    ("I've fallen", "help"),
    ("I have fallen and I can't get up", "help"),
    ("I fell but I'm okay", "help"),
    ("I need an ambulance", "help"),
    ("call an ambulance", "help"),
    ("cant breathe", "help"),
    ("I can't breathe", "help"),
    ("I cannot breathe", "help"),
    ("I can not breathe", "help"),
    ("I cannot get up", "help"),
    ("I am on the floor", "help"),
    ("I'm on the floor", "help"),
    ("I'm on the ground", "help"),
    ("I'm bleeding", "help"),
    ("chest pain", "help"),
    ("I have chest pain", "help"),
    ("I fell.", "help"),
    ("cant breath", "help"),  # a transcriber may write the noun
    ("Chest  pain", "help"),  # extra space from a transcriber
    ("I'm on the  floor", "help"),
    ("fellow", "no_answer"),
    # Rafael's words from pi-integration (1670e66)
    ("I'm injured", "help"),
    ("there's blood", "help"),
    ("I'm in pain", "help"),
    ("it's painful", "help"),
    ("call 911", "help"),
    ("call 9-1-1", "help"),
    ("call 9 1 1", "help"),
    ("I have an injury", "help"),
    ("okay, there's smoke", "help"),
    ("call nine one one", "help"),
    ("I need a doctor", "help"),
    ("get a paramedic", "help"),
    ("my chest", "help"),
    ("I'm dizzy", "help"),
    ("I feel faint", "help"),
    ("I fainted", "help"),
    ("I'm stuck", "help"),
    ("I'm trapped", "help"),
    ("fire!", "help"),
    ("there's smoke", "help"),
    ("call someone", "help"),
    ("call somebody", "help"),
    ("save me", "help"),
    ("please come", "help"),
    # forms his prefix match caught, kept
    ("call the doctors", "help"),
    ("paramedics", "help"),
    ("I'm fainting", "help"),
    ("I need my painkillers", "help"),
    ("call the firefighters", "help"),
    ("get a fireman", "help"),
    ("call the firemen", "help"),
    ("I can barely breathe", "help"),
    ("I can hardly get up", "help"),
    ("there are fires", "help"),
    # whole words only: these contain a help word but are not one
    ("I'm painting", "no_answer"),
    ("I'm fine, just painting", "ok"),
    ("the fireplace is on", "no_answer"),
    ("I got fired", "no_answer"),
    ("Chester", "no_answer"),
    ("a chestnut", "no_answer"),
    ("I'm a smoker", "no_answer"),
    ("I faintly heard it", "no_answer"),
    # words narrowed because a natural ok reply uses them;
    # a missed help still reaches the alarm after 3 asks
    ("my doctor said I'm fine", "ok"),
    ("I'm okay, I'm at the doctor's office", "ok"),
    ("I'm okay, I can breathe", "ok"),
    ("okay, I'll call my daughter later", "ok"),
    ("I'm fine, I was about to call for pizza", "ok"),
    ("yes, the fire alarm is just the oven", "ok"),
    ("I'm fine, the smoke detector beeped", "ok"),
    ("I'm fine, the bloody cat knocked it over", "ok"),
    ("yeah I'm fine, just checking my blood pressure", "ok"),
    ("I'm okay, just did my blood sugar", "ok"),
    ("yes, I'm fine, I'm just smoking on the porch", "ok"),
    ("I'm fine, I fell back asleep", "ok"),
    ("room 9115", "no_answer"),
    # "fell asleep" is not a fall: it follows the normal order
    ("I fell asleep", "no_answer"),
    ("I fell asleep, I'm okay", "ok"),
    ("I've fallen asleep", "no_answer"),
    # a negated answer must never become ok
    ("I'm not okay", "help"),
    ("not okay", "help"),
    ("I'm not ok.", "help"),
    ("I'm not fine", "help"),
    ("I'm not alright", "help"),
    ("no", "help"),
    ("No.", "help"),
    ("nope", "help"),
    ("I don't feel okay", "help"),
    # negations with no apostrophe, as a transcriber may write them.
    # Some realistic ok replies become help, same as their apostrophe form;
    # a false help only brings the fake alarm sooner.
    ("I cannot move", "help"),
    ("I cant stand", "help"),
    ("I dont feel good", "help"),
    ("yes I cannot", "help"),
    ("I cannot, okay", "help"),
    ("I wont be okay", "help"),
    ("I didnt hear, I'm okay", "help"),
    ("it isnt okay", "help"),
    ("I wouldnt say fine", "help"),
    ("I couldnt get up", "help"),
    ("doesnt matter, I'm fine", "help"),
    ("I'm fine, dont worry", "help"),
    ("I wasnt okay", "help"),
    ("things arent okay", "help"),
    ("my legs werent working", "help"),
    ("I shouldnt move", "help"),
    ("I havent been okay", "help"),
    ("it hasnt been fine", "help"),
    ("I aint okay", "help"),
    ("I hadnt noticed, I'm fine", "help"),
    # ok
    ("yes", "ok"),
    ("Yeah, I'm okay.", "ok"),
    ("yeah I'm okay", "ok"),
    ("okay", "ok"),
    ("ok", "ok"),
    ("I'm ok.", "ok"),
    ("I'm fine", "ok"),
    ("I'm alright", "ok"),
    ("I'm all right", "ok"),
    ("yep I'm good", "ok"),
    # silence or unrelated speech
    ("", "no_answer"),
    ("   ", "no_answer"),
    ("the weather is nice today", "no_answer"),
    ("I know", "no_answer"),  # "know" is not "no"
    ("token", "no_answer"),  # "token" is not "ok"
    ("cantaloupe", "no_answer"),  # not "cant"
    ("wonton", "no_answer"),  # not "wont"
    ("Good boy", "no_answer"),  # a real mishearing of room chatter; "good" is not an answer
    ("I'm good", "no_answer"),
]


@pytest.mark.parametrize("transcript,expected", TABLE)
def test_classify(transcript, expected):
    assert classify(transcript) == expected


def test_none_is_no_answer():
    assert classify(None) == "no_answer"
