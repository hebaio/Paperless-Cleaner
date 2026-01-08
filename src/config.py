import json
import os

SETTINGS_FILE = 'settings.json'

def load_settings() -> dict[str, str]:
    """Load settings from the JSON file.
    Returns:
        dict[str, str]: A dictionary of settings.
    """
    defaults = {
        'api_url': '',
        'api_token': '',
        'llm_enabled': 'false', 
        'llm_api_base': 'https://api.openai.com/v1',
        'llm_api_key': '',
        'llm_model': 'gpt-5-mini'
    }
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'r') as f:
            data = json.load(f)
            # Merge loaded data with defaults to ensure all keys exist
            return {**defaults, **data}
    return defaults

def save_settings(api_url: str, api_token: str, llm_enabled: str = 'false', llm_api_base: str = '', llm_api_key: str = '', llm_model: str = ''):
    """Save settings to the JSON file.
    Args:
        api_url (str): The API URL to save.
        api_token (str): The API token to save.
        llm_enabled (str): Whether LLM is enabled ('true'/'false').
        llm_api_base (str): LLM API Base URL.
        llm_api_key (str): LLM API Key.
        llm_model (str): LLM Model name.
    """
    settings = {
        'api_url': api_url, 
        'api_token': api_token,
        'llm_enabled': llm_enabled,
        'llm_api_base': llm_api_base,
        'llm_api_key': llm_api_key,
        'llm_model': llm_model
    }
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(settings, f, indent=4)
