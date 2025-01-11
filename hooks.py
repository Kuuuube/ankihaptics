from aqt import gui_hooks
from . import config_util

ease_to_button = {
    1: "again",
    2: "hard",
    3: "good",
    4: "easy"
}

def handle_hooks(mw, client, hook):
    config = config_util.get_config(mw)
    for device in config["devices"]:
        if device[hook]["enabled"]:
            print("Activating device. Strength: " + str(device[hook]["strength"]) + ", Duration: " + str(device[hook]["duration"]) + "s")

def answer_button_press(mw, client, reviewer, card, ease):
    button_name = ease_to_button[ease]
    handle_hooks(mw, client, button_name)

def show_question(mw, client, card):
    handle_hooks(mw, client, "show_question")

def show_answer(mw, client, card):
    handle_hooks(mw, client, "show_answer")

def register_hooks(mw, client):
    gui_hooks.reviewer_did_answer_card.append(lambda reviewer, card, ease: answer_button_press(mw, client, reviewer, card, ease))
    gui_hooks.reviewer_did_show_question.append(lambda card: show_question(mw, client, card))
    gui_hooks.reviewer_did_show_answer.append(lambda card: show_answer(mw, client, card))
