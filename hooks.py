import logging

import anki
import aqt.reviewer

from . import config_util

ease_to_button = {
    1: "again",
    2: "hard",
    3: "good",
    4: "easy",
}

def _handle_hooks(mw: aqt.main.AnkiQt, ankihaptics_ref, hook: str, card: anki.cards.Card) -> None:  # noqa: ANN001
    config = config_util.ensure_device_settings(config_util.get_config(mw), ankihaptics_ref.client.devices)
    devices = ankihaptics_ref.client.devices
    websocket_command = {"command": "scalar_cmd", "args": {"devices": []}}
    for config_device in config["devices"]:
        if not config_device["enabled"] or not config_device[hook]["enabled"]:
            continue
        if config_device["enabled_pattern"] != "*" and card.id not in mw.col.find_cards(config_device["enabled_pattern"]):
            continue

        client_device = None
        try:
            client_device = [device for device in devices.values() if device.name == config_device["device_name"]][0] #should only return one device
        except Exception:
            logging.exception("Hook failed to find device")
            continue

        websocket_command["args"]["devices"].append({"index": client_device.index, "actuators": client_device.actuators, "strength": config_device[hook]["strength"]})
        websocket_command["args"]["duration"] = config["duration"][hook]

    if len(websocket_command["args"]["devices"]) > 0:
        ankihaptics_ref.websocket_command_queue.append(websocket_command)

def _answer_button_press(mw: aqt.main.AnkiQt, ankihaptics_ref, _reviewer: aqt.reviewer.Reviewer, card: anki.cards.Card, ease: int) -> None:  # noqa: ANN001
    button_name = ease_to_button[ease]
    _handle_hooks(mw, ankihaptics_ref, button_name, card)

def _show_question(mw: aqt.main.AnkiQt, ankihaptics_ref, card: anki.cards.Card) -> None:  # noqa: ANN001
    _handle_hooks(mw, ankihaptics_ref, "show_question", card)

def _show_answer(mw: aqt.main.AnkiQt, ankihaptics_ref, card: anki.cards.Card) -> None:  # noqa: ANN001
    _handle_hooks(mw, ankihaptics_ref, "show_answer", card)

def register_hooks(mw: aqt.main.AnkiQt, ankihaptics_ref) -> None:  # noqa: ANN001
    # https://github.com/ankitects/anki/blob/main/qt/tools/genhooks_gui.py
    aqt.gui_hooks.reviewer_did_answer_card.append(lambda reviewer, card, ease: _answer_button_press(mw, ankihaptics_ref, reviewer, card, ease))
    aqt.gui_hooks.reviewer_did_show_question.append(lambda card: _show_question(mw, ankihaptics_ref, card))
    aqt.gui_hooks.reviewer_did_show_answer.append(lambda card: _show_answer(mw, ankihaptics_ref, card))
