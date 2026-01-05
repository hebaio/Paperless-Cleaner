import json
import os

SETTINGS_FILE = 'settings.json'

def load_settings() -> dict[str, str]:
    """Load settings from the JSON file.
    Returns:
        dict[str, str]: A dictionary with 'api_url' and 'api_token'.
    """
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'r') as f:
            return json.load(f)
    return {'api_url': '', 'api_token': ''}

def save_settings(api_url: str, api_token: str):
    """Save settings to the JSON file.
    Args:
        api_url (str): The API URL to save.
        api_token (str): The API token to save.
    """
    settings = {'api_url': api_url, 'api_token': api_token}
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(settings, f)
