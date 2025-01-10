config_schema = {
    "version": {
        "default": 1,
    }
}

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

def validate_config(config):
    for config_schema_key in config_schema.keys():
        if config_schema_key in config.keys():
            if type(config_schema[config_schema_key]["default"]) is type(config[config_schema_key]):
                if "enum" in config_schema[config_schema_key]:
                    if config[config_schema_key] in config_schema[config_schema_key]["enum"]:
                        continue
                else:
                    continue
        config[config_schema_key] = config_schema[config_schema_key]["default"]
    return config

def migrate_config(config):
    config_updates = []
    if len(config_updates) > config["version"]:
        for config_update in config_updates[config["version"]:]:
            config = config_update(config)
        config["version"] = config_schema["version"]["default"]
    return config
