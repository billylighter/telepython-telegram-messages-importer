import json
from .constants import META_FILE

def load_meta():
    if not META_FILE or not META_FILE.endswith(".json"):
        raise ValueError("Invalid META_FILE path")

    try:
        with open(META_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_meta(meta: dict):
    with open(META_FILE, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
