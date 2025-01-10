from aqt import mw, gui_hooks

from . import config_util

def answer_button_press(reviewer, card, ease):
    config = config_util.get_config(mw)
    print(config)
    print(ease)

def register_hooks():
    gui_hooks.reviewer_did_answer_card.append(answer_button_press)
