import json
import os
from datetime import datetime

CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cache")


def read_cache(name):
    path = os.path.join(CACHE_DIR, f"{name}.json")
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return None


def write_cache(name, data):
    os.makedirs(CACHE_DIR, exist_ok=True)
    path = os.path.join(CACHE_DIR, f"{name}.json")
    with open(path, "w") as f:
        json.dump(data, f)


def get_cache_timestamp():
    path = os.path.join(CACHE_DIR, "timestamp.txt")
    if os.path.exists(path):
        with open(path) as f:
            return f.read().strip()
    return None


def set_cache_timestamp():
    os.makedirs(CACHE_DIR, exist_ok=True)
    path = os.path.join(CACHE_DIR, "timestamp.txt")
    with open(path, "w") as f:
        f.write(datetime.now().strftime("%Y-%m-%d %H:%M"))
