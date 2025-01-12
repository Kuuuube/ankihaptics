import aqt

from .config_schemas import config_schema, device_schema


def ensure_device_settings(config: dict, devices: dict) -> dict:
    device_names = [*((x.device_name) for x in devices)]
    config_device_names = [*((x["device_name"]) for x in config["devices"])]
    for device_name in device_names:
        if device_name not in config_device_names:
            config["devices"].append({"device_name": device_name})
    return validate_config(config)

def set_config(mw: aqt.main.AnkiQt, config: dict) -> None:
    for key in list(config.keys()):
        if key not in config_schema:
            del config[key]
    mw.addonManager.writeConfig(__name__, config)

def get_config(mw: aqt.main.AnkiQt) -> dict:
    config = mw.addonManager.getConfig(__name__)

    if config_schema["version"]["default"] > config["version"]:
        config = _migrate_config(config)
        mw.addonManager.writeConfig(__name__, config)

    return validate_config(config)

def reset_config(mw: aqt.main.AnkiQt) -> None:
    default_config = {item[0]: item[1]["default"] for item in config_schema.items()}
    mw.addonManager.writeConfig(__name__, default_config)

def get_dict_defaults(schema: dict) -> dict:
    default_dict = {}
    for schema_key in schema:
        if type(schema[schema_key]["default"]) is dict:
            default_dict[schema_key] = get_dict_defaults(schema[schema_key])
        else:
            default_dict[schema_key] = schema[schema_key]["default"]

    return default_dict

def dict_validator(target_dict: dict, schema: dict) -> dict:
    new_dict = target_dict

    if type(target_dict) is not dict:
        new_dict = {}
        for schema_key in schema:
            new_dict[schema_key] = schema[schema_key]["default"]
        return new_dict

    for schema_key in schema:
        if schema_key in target_dict and type(schema[schema_key]["default"]) is type(target_dict[schema_key]):
            if type(target_dict[schema_key]) is dict:
                new_dict[schema_key] = dict_validator(target_dict[schema_key], schema[schema_key]["default"])
                continue
            if "enum" in schema[schema_key]:
                if target_dict[schema_key] in config_schema[schema_key]["enum"]:
                    continue
            else:
                continue

        if type(schema[schema_key]["default"]) is dict:
            new_dict[schema_key] = get_dict_defaults(schema[schema_key]["default"])
        else:
            new_dict[schema_key] = schema[schema_key]["default"]

    return new_dict

def validate_config(config: dict) -> dict:
    config = dict_validator(config, config_schema)
    i = 0
    while i < len(config["devices"]):
        config["devices"][i] = dict_validator(config["devices"][i], device_schema)
        i += 1
    return config

def _migrate_config(config: dict) -> dict:
    config_updates = []
    if len(config_updates) > config["version"]:
        for config_update in config_updates[config["version"]:]:
            config = config_update(config)
        config["version"] = config_schema["version"]["default"]
    return config
