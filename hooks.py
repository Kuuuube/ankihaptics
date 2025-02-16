import traceback

import anki
import anki.utils
import aqt.reviewer

from . import config_util, get_streaks, logger

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
        except Exception:  # noqa: BLE001
            logger.error_log("Hook failed to find device", traceback.format_exc())
            continue

        enabled_actuators = []
        for device_actuator in client_device.actuators:
            for config_actuator in config_device["actuators"]:
                if config_actuator["index"] == device_actuator.index and config_actuator["enabled"]:
                    enabled_actuators.append({"actuator": device_actuator, "strength_multiplier": config_actuator["strength_multiplier"], "duration_multiplier": config_actuator["duration_multiplier"]})

        if len(enabled_actuators) > 0:
            streak_multipliers = {"strength_multiplier": 1.0, "duration_multiplier": 1.0}
            if config["streak"]["streak_type"] == "Per Card":
                streak_multipliers = get_streaks.get_streak_multipliers_per_card(mw, config, card)
            elif config["streak"]["streak_type"] == "Per Deck":
                streak_multipliers = get_streaks.get_streak_multipliers_per_deck(mw, config, card)
            elif config["streak"]["streak_type"] == "Per Collection":
                streak_multipliers = get_streaks.get_streak_multipliers_per_collection(mw, config, card)
            command_strength = config_device[hook]["strength"] * streak_multipliers["strength_multiplier"]
            command_duration = config_device[hook]["duration"] * streak_multipliers["duration_multiplier"]
            websocket_command["args"]["devices"].append({"index": client_device.index, "actuators": enabled_actuators, "strength": command_strength, "duration": command_duration})

    if len(websocket_command["args"]["devices"]) > 0:
        ankihaptics_ref.websocket_command_queue.append(websocket_command)

def _answer_button_press(mw: aqt.main.AnkiQt, ankihaptics_ref, _reviewer: aqt.reviewer.Reviewer, card: anki.cards.Card, ease: int) -> None:  # noqa: ANN001
    button_name = ease_to_button[ease]
    _handle_hooks(mw, ankihaptics_ref, button_name, card)

def _show_question(mw: aqt.main.AnkiQt, ankihaptics_ref, card: anki.cards.Card) -> None:  # noqa: ANN001
    _handle_hooks(mw, ankihaptics_ref, "show_question", card)

def _show_answer(mw: aqt.main.AnkiQt, ankihaptics_ref, card: anki.cards.Card) -> None:  # noqa: ANN001
    _handle_hooks(mw, ankihaptics_ref, "show_answer", card)

reviewer_did_answer_card_lambda_func = None
reviewer_did_show_question_lambda_func = None
reviewer_did_show_answer_lambda_func = None

def register_hooks(mw: aqt.main.AnkiQt, ankihaptics_ref) -> None:  # noqa: ANN001
    global reviewer_did_answer_card_lambda_func, reviewer_did_show_question_lambda_func, reviewer_did_show_answer_lambda_func  # noqa: PLW0603
    def reviewer_did_answer_card_lambda_func(reviewer: aqt.reviewer.Reviewer, card: anki.cards.Card, ease: int) -> None:
        return _answer_button_press(mw, ankihaptics_ref, reviewer, card, ease)
    def reviewer_did_show_question_lambda_func(card: anki.cards.Card) -> None:
        return _show_question(mw, ankihaptics_ref, card)
    def reviewer_did_show_answer_lambda_func(card: anki.cards.Card) -> None:
        return _show_answer(mw, ankihaptics_ref, card)
    # https://github.com/ankitects/anki/blob/main/qt/tools/genhooks_gui.py
    aqt.gui_hooks.reviewer_did_answer_card.append(reviewer_did_answer_card_lambda_func)
    aqt.gui_hooks.reviewer_did_show_question.append(reviewer_did_show_question_lambda_func)
    aqt.gui_hooks.reviewer_did_show_answer.append(reviewer_did_show_answer_lambda_func)

def remove_hooks() -> None:
    aqt.gui_hooks.reviewer_did_answer_card.remove(reviewer_did_answer_card_lambda_func)
    aqt.gui_hooks.reviewer_did_show_question.remove(reviewer_did_show_question_lambda_func)
    aqt.gui_hooks.reviewer_did_show_answer.remove(reviewer_did_show_answer_lambda_func)
