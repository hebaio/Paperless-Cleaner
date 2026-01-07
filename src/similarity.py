from difflib import SequenceMatcher

def find_similar_groups(items: list[dict], threshold: float = 0.8) -> list[list[dict]]:
    """
    Finds groups of similar items based on their names using SequenceMatcher.
    
    Args:
        items (list[dict]): List of items, each must have 'id' and 'name'.
        threshold (float): Similarity threshold (0.0 to 1.0).
        
    Returns:
        list[list[dict]]: A list of groups, where each group is a list of similar items.
    """
    groups = []
    seen = set()
    
    # Sort by name length descending to use longer names as potential anchors 
    # (though simple iteration also works)
    # Sorting helps consistency
    sorted_items = sorted(items, key=lambda x: x['name'].lower())

    for i, item1 in enumerate(sorted_items):
        if item1['id'] in seen:
            continue
            
        current_group = [item1]
        
        for j in range(i + 1, len(sorted_items)):
            item2 = sorted_items[j]
            if item2['id'] in seen:
                continue
                
            ratio = SequenceMatcher(None, item1['name'].lower(), item2['name'].lower()).ratio()
            if ratio >= threshold:
                current_group.append(item2)
                # We mark it as seen so it doesn't start its own group.
                # Note: This is a greedy approach. item2 is grouped with item1.
                # Even if item2 is arguably MORE similar to a later item3, 
                # it stays here. This is usually fine for deduplication.
                seen.add(item2['id'])
        
        if len(current_group) > 1:
            seen.add(item1['id'])
            groups.append(current_group)
            
    return groups
