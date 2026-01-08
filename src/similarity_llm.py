import json
import requests
import logging

def find_similar_groups_llm(items: list[dict], settings: dict) -> list[list[dict]]:
    """
    Finds groups of similar items using an LLM.

    Args:
        items (list[dict]): List of items to process.
        settings (dict): Settings dictionary containing LLM config.

    Returns:
        list[list[dict]]: A list of groups (lists of dicts).
    """

    api_key = settings.get('llm_api_key')
    api_base = settings.get('llm_api_base')
    model = settings.get('llm_model')

    if not api_key or not api_base or not model:
        raise ValueError("LLM configuration is missing.")

    # Prepare data for prompt - minimal payload to save tokens
    simple_items = [{'id': item['id'], 'name': item['name']} for item in items]
    
    # Construct prompt
    prompt = f"""
    You are a data cleaning assistant. Your task is to identify duplicate or similar entities in a list of names.
    The list represents correspondents or document types from a document management system.
    
    Look for:
    - Typos (e.g., "Amazn" vs "Amazon")
    - Variations (e.g., "Amazon.com" vs "Amazon DE")
    - Acronyms vs full names (if obvious)
    - Formatting differences
    
    Here is the list of items in JSON format:
    {json.dumps(simple_items, indent=None)}
    
    Output strictly a JSON object with a single key 'groups'.
    The value of 'groups' must be a list of lists, where each inner list contains the numeric IDs of the items that belong to the same group.
    Only include groups with at least 2 items.
    Do not include items that have no duplicates.
    Example Output: {{ "groups": [[1, 5], [10, 12, 15]] }}
    
    Response (JSON only):
    """

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant that outputs only JSON."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.0
    }

    url = f"{api_base.rstrip('/')}/chat/completions"

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()
        
        content = result['choices'][0]['message']['content']
        
        # Clean potential markdown code blocks
        if content.startswith('```json'):
            content = content[7:]
        if content.startswith('```'):
            content = content[3:]
        if content.endswith('```'):
            content = content[:-3]
        content = content.strip()

        parsed = json.loads(content)
        id_groups = parsed.get('groups', [])
        
        # Convert list of ID lists back to list of item lists
        # We need a lookup map for efficiency
        item_map = {item['id']: item for item in items}
        
        final_groups = []
        for group_ids in id_groups:
            # Filter valid IDs and map back to items
            current_group = [item_map[gid] for gid in group_ids if gid in item_map]
            if len(current_group) > 1:
                final_groups.append(current_group)
                
        return final_groups

    except Exception as e:
        logging.error(f"LLM Error: {e}")
        if 'response' in locals() and hasattr(response, 'text'):
             logging.error(f"LLM Response Body: {response.text}")
        raise e
