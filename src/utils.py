import yaml
import os

import paths

def load_config_schema(schema_path=None):
    """
    Loads the schema for the configuration file.
    """
    with open(schema_path or paths.SCHEMA_PATH, encoding='utf-8') as f:
        return yaml.safe_load(f)

def load_config_values(schema, config_path=paths.CONFIG_PATH):
    """
    Loads the values from the configuration file.
    Supports flat config structure (key-value pairs directly under categories).
    """
    config = {}
    for category, settings in schema.items():
        config[category] = {}
        for key, meta in settings.items():
            if isinstance(meta, dict) and 'value' in meta:
                # Direct key-value pair (flat structure)
                config[category][key] = meta['value']

    # Load user settings if they exist
    if config_path and os.path.isfile(config_path):
        with open(config_path, 'r') as file:
            user_config = yaml.safe_load(file)
            if user_config:
                for category, settings in user_config.items():
                    if category in config:
                        for key, value in settings.items():
                            config[category][key] = value

    return config

def save_config(config, config_path=paths.CONFIG_PATH):
    """
    Save the configuration to a yaml file.
    """
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    with open(config_path, 'w') as file:
        yaml.dump(config, file, default_flow_style=False)
