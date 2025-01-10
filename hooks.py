from aqt import gui_hooks
from . import config_util

ease_to_button = {
    1: "again",
    2: "hard",
    3: "good",
    4: "easy"
}

def answer_button_press(mw, reviewer, card, ease):
    config = config_util.get_config(mw)
    for device in config["devices"]:
        if device[ease_to_button[ease]]["enabled"]:
            print(ease, ease_to_button[ease], "activating device")
    print(config)
    print(ease)

def register_hooks(mw):
    gui_hooks.reviewer_did_answer_card.append(lambda reviewer, card, ease: answer_button_press(mw, reviewer, card, ease))
