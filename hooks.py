import traceback
from datetime import datetime, timezone

import anki
import aqt.reviewer

from . import config_util, logger

ease_to_button = {
    1: "again",
    2: "hard",
    3: "good",
    4: "easy",
}

def _get_streak_buttons(config: dict) -> list:
    streak_buttons = []
    if config["streak"]["again"]["enabled"]:
        streak_buttons.append(1)
    if config["streak"]["hard"]["enabled"]:
        streak_buttons.append(2)
    if config["streak"]["good"]["enabled"]:
        streak_buttons.append(3)
    if config["streak"]["easy"]["enabled"]:
        streak_buttons.append(4)
    return streak_buttons

def _get_streak_multipliers(mw: aqt.main.AnkiQt, config: dict, card: anki.cards.Card) -> dict:
    current_epoch_time = int(datetime.now(tz=timezone.utc).timestamp() * 1000)
    allowed_epoch_time = str(current_epoch_time - config["streak"]["streak_time_epoch_ms"])
    # cid = card_id, id = epoch_ms_timestamp, ease = answer_button_pressed https://github.com/ankidroid/Anki-Android/wiki/Database-Structure#review-log
    revlog_rows = mw.col.db.all(f"SELECT cid, id, ease FROM revlog WHERE cid = {card.id} AND id >= {allowed_epoch_time} ORDER BY id DESC")  # noqa: S608
    recent_button_presses = []
    for revlog_row in revlog_rows:
        streak_buttons = _get_streak_buttons(config)
        if revlog_row[2] not in streak_buttons or len(recent_button_presses) > config["streak"]["max_length"]:
            break

        recent_button_presses.append({"strength_multiplier": config["streak"][ease_to_button[revlog_row[2]]]["strength"], "duration_multiplier": config["streak"][ease_to_button[revlog_row[2]]]["duration"]}) #append strength multiplier

    if len(recent_button_presses) < config["streak"]["min_length"]:
        return {"strength_multiplier": 1.0, "duration_multiplier": 1.0}

    multiplied_multipliers = {"strength_multiplier": 1.0, "duration_multiplier": 1.0}
    for recent_button_press in recent_button_presses:
        multiplied_multipliers["strength_multiplier"] *= recent_button_press["strength_multiplier"]
        multiplied_multipliers["duration_multiplier"] *= recent_button_press["duration_multiplier"]

    return multiplied_multipliers

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
            logger.error_log("Hook failed to find device", traceback.format_exc())
            continue

        enabled_actuators = []
        for device_actuator in client_device.actuators:
            for config_actuator in config_device["actuators"]:
                if config_actuator["index"] == device_actuator.index and config_actuator["enabled"]:
                    enabled_actuators.append(device_actuator)

        if len(enabled_actuators) > 0:
            streak_multipliers = _get_streak_multipliers(mw, config, card)
            print(streak_multipliers)
            command_strength = config_device[hook]["strength"] * streak_multipliers["strength_multiplier"]
            command_duration = config["duration"][hook] * streak_multipliers["duration_multiplier"]
            websocket_command["args"]["devices"].append({"index": client_device.index, "actuators": enabled_actuators, "strength": command_strength})
            websocket_command["args"]["duration"] = command_duration

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
