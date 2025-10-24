import asyncio
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from app.utils.file_utils import load_meta, save_meta
from app.utils.constants import SESSIONS_DIR, IMAGES_DIR

class TelegramClientManager:
    def __init__(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.client = None

    def connect(self, session_name, api_id, api_hash):
        self.client = TelegramClient(f"{SESSIONS_DIR}/{session_name}", api_id, api_hash)
        self.loop.run_until_complete(self.client.connect())
        return self.client

    def is_authorized(self):
        return self.loop.run_until_complete(self.client.is_user_authorized())

    def disconnect(self):
        if self.client:
            try:
                self.client.disconnect()
            except:
                pass
            self.client = None

    def sign_in(self, phone, code, phone_code_hash):
        return self.loop.run_until_complete(
            self.client.sign_in(phone=phone, code=code, phone_code_hash=phone_code_hash)
        )

    def sign_in_2fa(self, password):
        return self.loop.run_until_complete(self.client.sign_in(password=password))

    def send_code(self, phone):
        return self.loop.run_until_complete(self.client.send_code_request(phone))

    def get_me(self):
        return self.loop.run_until_complete(self.client.get_me())

    def send_message(self, to, text):
        return self.loop.run_until_complete(self.client.send_message(to, text))

    def download_avatar(self, entity, filename):
        path = f"{IMAGES_DIR}/{filename}"
        file = self.loop.run_until_complete(self.client.download_profile_photo(entity, file=path))
        return file
