import types

import anki
import aqt
import buttplug

from . import config_util, haptics_commands

ease_to_button = {
    1: "again",
    2: "hard",
    3: "good",
    4: "easy",
}

def _handle_hooks(mw: aqt.main.AnkiQt, client: buttplug.Client, hook: str) -> None:
    config = config_util.ensure_device_settings(types.SimpleNamespace(**config_util.get_config(mw)), client.devices)
    devices = client.devices
    for config_device in config["devices"]:
        if config_device[hook]["enabled"]:
            client_device = [device for device in devices if device.device_name == config_device["device_name"]]
            if client_device:
                print("Activating device. Strength: " + str(config_device[hook]["strength"]) + ", Duration: " + str(config_device[hook]["duration"]) + "s")
                if len(client_device.actuators) != 0:
                    target_actuators = [client_device.actuators[0]]
                    for target_actuator in target_actuators:
                        haptics_commands.run_scalar_command(target_actuator, int(config_device[hook]["strength"] * (target_actuator.step_count / 99)), 0, config_device[hook]["duration"])

def _answer_button_press(mw: aqt.main.AnkiQt, client: buttplug.Client, _reviewer: aqt.reviewer.Reviewer, _card: anki.cards.Card, ease: int) -> None:
    button_name = ease_to_button[ease]
    _handle_hooks(mw, client, button_name)

def _show_question(mw: aqt.main.AnkiQt, client: buttplug.Client, _card: anki.cards.Card) -> None:
    _handle_hooks(mw, client, "show_question")

def _show_answer(mw: aqt.main.AnkiQt, client: buttplug.Client, _card: anki.cards.Card) -> None:
    _handle_hooks(mw, client, "show_answer")

def register_hooks(mw: aqt.main.AnkiQt, client: buttplug.Client) -> None:
    # https://github.com/ankitects/anki/blob/main/qt/tools/genhooks_gui.py
    aqt.gui_hooks.reviewer_did_answer_card.append(lambda reviewer, card, ease: _answer_button_press(mw, client, reviewer, card, ease))
    aqt.gui_hooks.reviewer_did_show_question.append(lambda card: _show_question(mw, client, card))
    aqt.gui_hooks.reviewer_did_show_answer.append(lambda card: _show_answer(mw, client, card))
