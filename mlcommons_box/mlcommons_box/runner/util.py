import copy

def merge_dict(base, overlay):
    result = copy.deepcopy(base)
    for key, val in overlay.items():
        if isinstance(val, dict):
            node = result.setdefault(key, {})
            merge_dict(val, node)
        else:
            result[key] = val
    return result
