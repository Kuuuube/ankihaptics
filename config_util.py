from .config_schemas import config_schema, device_schema

def set_config(mw, namespace_config):
    config = dict(namespace_config.__dict__)
    for key in list(config.keys()):
        if key not in config_schema.keys():
            del config[key]
    mw.addonManager.writeConfig(__name__, config)

def get_config(mw):
    config = mw.addonManager.getConfig(__name__)

    if config_schema["version"]["default"] > config["version"]:
        config = migrate_config(config)
        mw.addonManager.writeConfig(__name__, config)

    return validate_config(config)

def reset_config(mw):
    default_config = dict(map(lambda item: (item[0], item[1]["default"]), config_schema.items()))
    mw.addonManager.writeConfig(__name__, default_config)

def dict_validator(target_dict, schema):
    new_dict = target_dict

    if type(target_dict) is not dict:
        new_dict = {}
        for schema_key in schema.keys():
            new_dict[schema_key] = schema[schema_key]["default"]
        return new_dict

    for schema_key in schema.keys():
        if schema_key in target_dict.keys():
            if type(schema[schema_key]["default"]) is type(target_dict[schema_key]):
                if type(target_dict[schema_key]) is dict:
                    new_dict[schema_key] = dict_validator(target_dict[schema_key], schema[schema_key]["default"])
                    continue
                if "enum" in schema[schema_key]:
                    if target_dict[schema_key] in config_schema[schema_key]["enum"]:
                        continue
                else:
                    continue
        new_dict[schema_key] = schema[schema_key]["default"]

    return new_dict

def validate_config(config):
    config = dict_validator(config, config_schema)
    i = 0
    while i < len(config["devices"]):
        config["devices"][i] = dict_validator(config["devices"][i], device_schema)
        i += 1
    return config

def migrate_config(config):
    config_updates = []
    if len(config_updates) > config["version"]:
        for config_update in config_updates[config["version"]:]:
            config = config_update(config)
        config["version"] = config_schema["version"]["default"]
    return config
