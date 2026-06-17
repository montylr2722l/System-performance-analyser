"""Load and save database settings from a local JSON file."""

import json
import os

from paths import get_data_path

DB_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "password",
    "database": "system_performance",
}

SETTINGS_FILE = get_data_path("db_settings.json")


def get_db_config():
    """Return DB config, preferring saved settings over defaults."""
    config = DB_CONFIG.copy()
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r", encoding="utf-8") as file:
            saved = json.load(file)
        for key, value in saved.items():
            if key == "password" and not value:
                continue
            config[key] = value
    return config


def save_db_config(host, port, user, password, database):
    """Save database credentials to local settings file."""
    settings = {
        "host": host,
        "port": int(port),
        "user": user,
        "password": password,
        "database": database,
    }
    with open(SETTINGS_FILE, "w", encoding="utf-8") as file:
        json.dump(settings, file, indent=2)
    return settings


def test_db_config(config):
    """Test MySQL server login (without requiring database to exist)."""
    import mysql.connector
    from mysql.connector import Error

    try:
        server_config = {k: v for k, v in config.items() if k != "database"}
        conn = mysql.connector.connect(**server_config)
        conn.close()
        return True, "Connection successful!"
    except Error as exc:
        return False, str(exc)
