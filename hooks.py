from aqt import gui_hooks
from . import config_util

ease_to_button = {
    1: "again",
    2: "hard",
    3: "good",
    4: "easy"
}

def answer_button_press(mw, client, reviewer, card, ease):
    config = config_util.get_config(mw)
    for device in config["devices"]:
        button_name = ease_to_button[ease]
        if device[button_name]["enabled"]:
            print("Activating device. Strength: " + str(device[button_name]["strength"]) + ", Duration: " + str(device[button_name]["duration"]) + "s")

    # for device in client.devices:
    #     if len(device.actuators) != 0:
    #         await device.actuators[0].command(0.5)
    #     if len(device.linear_actuators) != 0:
    #         await device.linear_actuators[0].command(1000, 0.5)
    #     if len(device.rotatory_actuators) != 0:
    #         await device.rotatory_actuators[0].command(0.5, True)

def register_hooks(mw, client):
    gui_hooks.reviewer_did_answer_card.append(lambda reviewer, card, ease: answer_button_press(mw, client, reviewer, card, ease))
