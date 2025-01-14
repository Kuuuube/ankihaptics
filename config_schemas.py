duration_schema = {
    "again":  {
        "default": 0.5,
    },
    "hard":  {
        "default": 0.5,
    },
    "good":  {
        "default": 0.5,
    },
    "easy":  {
        "default": 0.5,
    },
    "show_question":  {
        "default": 0.5,
    },
    "show_answer":  {
        "default": 0.5,
    },
}

streak_again_button_schema = {
    "enabled": {
        "default": False,
    },
    "strength": {
        "default": 1.0,
    },
    "duration": {
        "default": 1.0,
    },
}

streak_hard_button_schema = {
    "enabled": {
        "default": False,
    },
    "strength": {
        "default": 1.125,
    },
    "duration": {
        "default": 1.125,
    },
}

streak_good_button_schema = {
    "enabled": {
        "default": False,
    },
    "strength": {
        "default": 1.25,
    },
    "duration": {
        "default": 1.25,
    },
}

streak_easy_button_schema = {
    "enabled": {
        "default": False,
    },
    "strength": {
        "default": 1.5,
    },
    "duration": {
        "default": 1.5,
    },
}

streak_schema = {
    "streak_type": {
        "default": "Per Deck",
    },
    "again":  {
        "default": streak_again_button_schema,
    },
    "hard":  {
        "default": streak_hard_button_schema,
    },
    "good":  {
        "default": streak_good_button_schema,
    },
    "easy":  {
        "default": streak_easy_button_schema,
    },
    "min_length": {
        "default": 2,
    },
    "max_length": {
        "default": 5,
    },
    "streak_time_epoch_ms": {
        "default": 3600000,
    },
}

config_schema = {
    "version": {
        "default": 1,
    },
    "websocket_path": {
        "default": "ws://127.0.0.1:12345",
    },
    "reconnect_delay": {
        "default": 1,
    },
    "websocket_polling_delay_ms": {
        "default": 1,
    },
    "duration": {
        "default": duration_schema,
    },
    "streak": {
        "default": streak_schema,
    },
    "devices": {
        "default": [],
    },
}

again_button_schema = {
    "enabled": {
        "default": False,
    },
    "strength": {
        "default": 0.1,
    },
}

hard_button_schema = {
    "enabled": {
        "default": False,
    },
    "strength": {
        "default": 0.25,
    },
}

good_button_schema = {
    "enabled": {
        "default": True,
    },
    "strength": {
        "default": 0.5,
    },
}

easy_button_schema = {
    "enabled": {
        "default": True,
    },
    "strength": {
        "default": 1.0,
    },
}

show_question_schema = {
    "enabled": {
        "default": False,
    },
    "strength": {
        "default": 0.1,
    },
}

show_answer_schema = {
    "enabled": {
        "default": False,
    },
    "strength": {
        "default": 0.1,
    },
}

device_schema = {
    "device_name": {
        "default": "",
    },
    "enabled": {
        "default": False,
    },
    "actuators": {
        "default": [],
    },
    "enabled_pattern": {
        "default": "*",
    },
    "again": {
        "default": again_button_schema,
    },
    "hard": {
        "default": hard_button_schema,
    },
    "good": {
        "default": good_button_schema,
    },
    "easy": {
        "default": easy_button_schema,
    },
    "show_question": {
        "default": show_question_schema,
    },
    "show_answer": {
        "default": show_answer_schema,
    },
}

actuator_schema = {
    "index": {
        "default": -1,
    },
    "name": {
        "default": "",
    },
    "enabled": {
        "default": True,
    },
}
