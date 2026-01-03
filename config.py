import json
import os

SETTINGS_FILE = 'settings.json'

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'r') as f:
            return json.load(f)
    return {'api_url': '', 'api_token': ''}

def save_settings(api_url, api_token):
    settings = {'api_url': api_url, 'api_token': api_token}
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(settings, f)
