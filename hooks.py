from aqt import gui_hooks
from . import config_util

def answer_button_press(mw, reviewer, card, ease):
    config = config_util.get_config(mw)
    print(config)
    print(ease)

def register_hooks(mw):
    gui_hooks.reviewer_did_answer_card.append(lambda reviewer, card, ease: answer_button_press(mw, reviewer, card, ease))
