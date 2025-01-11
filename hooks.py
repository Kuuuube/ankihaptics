from aqt import gui_hooks
from . import config_util, haptics_commands

ease_to_button = {
    1: "again",
    2: "hard",
    3: "good",
    4: "easy"
}

def handle_hooks(mw, client, hook):
    config = config_util.get_config(mw)
    devices = client.devices
    for config_device in config["devices"]:
        if config_device[hook]["enabled"]:
            client_device = [device for device in devices if device["DeviceName"] == config_device["device_name"]]
            if client_device:
                print("Activating device. Strength: " + str(config_device[hook]["strength"]) + ", Duration: " + str(config_device[hook]["duration"]) + "s")
                if len(client_device.actuators) != 0:
                    haptics_commands.run_scalar_command(client_device.actuators[0], config_device[hook]["strength"], 0, config_device[hook]["duration"])

def answer_button_press(mw, client, reviewer, card, ease):
    button_name = ease_to_button[ease]
    handle_hooks(mw, client, button_name)

def show_question(mw, client, card):
    handle_hooks(mw, client, "show_question")

def show_answer(mw, client, card):
    handle_hooks(mw, client, "show_answer")

def register_hooks(mw, client):
    # https://github.com/ankitects/anki/blob/main/qt/tools/genhooks_gui.py
    gui_hooks.reviewer_did_answer_card.append(lambda reviewer, card, ease: answer_button_press(mw, client, reviewer, card, ease))
    gui_hooks.reviewer_did_show_question.append(lambda card: show_question(mw, client, card))
    gui_hooks.reviewer_did_show_answer.append(lambda card: show_answer(mw, client, card))
