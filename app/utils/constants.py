import os

SESSIONS_DIR = "sessions"
IMAGES_DIR = os.path.join("images", "profiles")
META_FILE = os.path.join(SESSIONS_DIR, "meta.json")
AVATAR_SIZE = 50

os.makedirs(SESSIONS_DIR, exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)