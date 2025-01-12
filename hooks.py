import anki
import aqt.reviewer
import buttplug

from . import config_util

ease_to_button = {
    1: "again",
    2: "hard",
    3: "good",
    4: "easy",
}

def _handle_hooks(mw: aqt.main.AnkiQt, ankihaptics_ref, hook: str) -> None:
    config = config_util.ensure_device_settings(config_util.get_config(mw), ankihaptics_ref.client.devices)
    devices: buttplug.Client.devices = ankihaptics_ref.client.devices
    websocket_command = {"command": "scalar_cmd", "args": {"devices": []}}
    for config_device in config["devices"]:
        if config_device["enabled"] and config_device[hook]["enabled"]:
            client_device: buttplug.Device = [device for device in devices.values() if device.name == config_device["device_name"]][0] #should only return one device
            websocket_command["args"]["devices"].append({"index": client_device.index, "actuators": client_device.actuators, "strength": config_device[hook]["strength"]})
            websocket_command["args"]["duration"] = config["duration"][hook]
            ankihaptics_ref.websocket_command = websocket_command

def _answer_button_press(mw: aqt.main.AnkiQt, ankihaptics_ref, _reviewer: aqt.reviewer.Reviewer, _card: anki.cards.Card, ease: int) -> None:
    button_name = ease_to_button[ease]
    _handle_hooks(mw, ankihaptics_ref, button_name)

def _show_question(mw: aqt.main.AnkiQt, ankihaptics_ref, _card: anki.cards.Card) -> None:
    _handle_hooks(mw, ankihaptics_ref, "show_question")

def _show_answer(mw: aqt.main.AnkiQt, ankihaptics_ref, _card: anki.cards.Card) -> None:
    _handle_hooks(mw, ankihaptics_ref, "show_answer")

def register_hooks(mw: aqt.main.AnkiQt, ankihaptics_ref) -> None:
    # https://github.com/ankitects/anki/blob/main/qt/tools/genhooks_gui.py
    aqt.gui_hooks.reviewer_did_answer_card.append(lambda reviewer, card, ease: _answer_button_press(mw, ankihaptics_ref, reviewer, card, ease))
    aqt.gui_hooks.reviewer_did_show_question.append(lambda card: _show_question(mw, ankihaptics_ref, card))
    aqt.gui_hooks.reviewer_did_show_answer.append(lambda card: _show_answer(mw, ankihaptics_ref, card))
