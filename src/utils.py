import json


def clamp(v, low, high):
    return max(low, min(high, v))

def to_linear(v, low, high, begin, end):
    v = clamp(v, low, high)
    v = (v - low) / (high - low) * (end - begin) + begin
    return v

def load_json(path):
    with Path(path).open("r") as f:
        content = json.load(f)
    return content
