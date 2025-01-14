from datetime import datetime, timezone

import anki
import anki.utils
import aqt.reviewer

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

def _calculate_multipliers(revlog_rows: list, config: dict) -> dict:
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

def get_streak_multipliers_per_collection(mw: aqt.main.AnkiQt, config: dict, _card: anki.cards.Card) -> dict:
    current_epoch_time = int(datetime.now(tz=timezone.utc).timestamp() * 1000)
    allowed_epoch_time = str(current_epoch_time - config["streak"]["streak_time_epoch_ms"])
    card_ids = mw.col.find_cards("*")
    # cid = card_id, id = epoch_ms_timestamp, ease = answer_button_pressed https://github.com/ankidroid/Anki-Android/wiki/Database-Structure#review-log
    revlog_rows = mw.col.db.all(f"SELECT cid, id, ease FROM revlog WHERE cid in {anki.utils.ids2str(card_ids)} AND id >= {allowed_epoch_time} ORDER BY id DESC")  # noqa: S608
    return _calculate_multipliers(revlog_rows, config)

def get_streak_multipliers_per_deck(mw: aqt.main.AnkiQt, config: dict, card: anki.cards.Card) -> dict:
    current_epoch_time = int(datetime.now(tz=timezone.utc).timestamp() * 1000)
    allowed_epoch_time = str(current_epoch_time - config["streak"]["streak_time_epoch_ms"])
    card_ids = mw.col.find_cards("did:" + str(card.did))
    # cid = card_id, id = epoch_ms_timestamp, ease = answer_button_pressed https://github.com/ankidroid/Anki-Android/wiki/Database-Structure#review-log
    revlog_rows = mw.col.db.all(f"SELECT cid, id, ease FROM revlog WHERE cid in {anki.utils.ids2str(card_ids)} AND id >= {allowed_epoch_time} ORDER BY id DESC")  # noqa: S608
    return _calculate_multipliers(revlog_rows, config)

def get_streak_multipliers_per_card(mw: aqt.main.AnkiQt, config: dict, card: anki.cards.Card) -> dict:
    current_epoch_time = int(datetime.now(tz=timezone.utc).timestamp() * 1000)
    allowed_epoch_time = str(current_epoch_time - config["streak"]["streak_time_epoch_ms"])
    # cid = card_id, id = epoch_ms_timestamp, ease = answer_button_pressed https://github.com/ankidroid/Anki-Android/wiki/Database-Structure#review-log
    revlog_rows = mw.col.db.all(f"SELECT cid, id, ease FROM revlog WHERE cid = {card.id} AND id >= {allowed_epoch_time} ORDER BY id DESC")  # noqa: S608
    return _calculate_multipliers(revlog_rows, config)
