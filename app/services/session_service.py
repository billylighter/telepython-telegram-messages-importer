import os
from app.utils.file_utils import load_meta, save_meta
from app.utils.constants import SESSIONS_DIR

def remove_session(session_name: str):
    path = os.path.join(SESSIONS_DIR, f"{session_name}.session")
    if os.path.exists(path):
        os.remove(path)

    meta = load_meta()
    if f"{session_name}.session" in meta:
        info = meta.pop(f"{session_name}.session")
        avatar_path = info.get("avatar")
        if avatar_path and os.path.exists(avatar_path):
            os.remove(avatar_path)
        save_meta(meta)
