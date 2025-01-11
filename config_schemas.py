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
    "websocket_polling_delay": {
        "default": 1,
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
    "duration": {
        "default": 1.0,
    },
}

hard_button_schema = {
    "enabled": {
        "default": False,
    },
    "strength": {
        "default": 0.25,
    },
    "duration": {
        "default": 1.0,
    },
}

good_button_schema = {
    "enabled": {
        "default": True,
    },
    "strength": {
        "default": 0.5,
    },
    "duration": {
        "default": 1.0,
    },
}

easy_button_schema = {
    "enabled": {
        "default": True,
    },
    "strength": {
        "default": 1.0,
    },
    "duration": {
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
    "duration": {
        "default": 1.0,
    },
}

show_answer_schema = {
    "enabled": {
        "default": False,
    },
    "strength": {
        "default": 0.1,
    },
    "duration": {
        "default": 1.0,
    },
}

device_schema = {
    "device_name": {
        "default": "",
    },
    "enabled_by_default": {
        "default": False,
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
