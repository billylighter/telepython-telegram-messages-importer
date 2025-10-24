import asyncio
from telethon import TelegramClient
from app.utils.constants import SESSIONS_DIR, IMAGES_DIR

class TelegramClientManager:
    def __init__(self, loop):
        self.loop = loop
        self.client = None

    def connect(self, session_name, api_id, api_hash):
        # создаём клиент, используя тот же event loop
        self.client = TelegramClient(f"{SESSIONS_DIR}/{session_name}", api_id, api_hash, loop=self.loop)
        future = asyncio.run_coroutine_threadsafe(self.client.connect(), self.loop)
        future.result()
        return self.client

    def is_authorized(self):
        future = asyncio.run_coroutine_threadsafe(self.client.is_user_authorized(), self.loop)
        return future.result()

    def disconnect(self):
        if self.client:
            try:
                future = asyncio.run_coroutine_threadsafe(self.client.disconnect(), self.loop)
                future.result()
            except Exception:
                pass
            self.client = None

    def send_code(self, phone):
        future = asyncio.run_coroutine_threadsafe(self.client.send_code_request(phone), self.loop)
        return future.result()

    def sign_in(self, phone, code, phone_code_hash):
        future = asyncio.run_coroutine_threadsafe(
            self.client.sign_in(phone=phone, code=code, phone_code_hash=phone_code_hash),
            self.loop
        )
        return future.result()

    def sign_in_2fa(self, password):
        future = asyncio.run_coroutine_threadsafe(self.client.sign_in(password=password), self.loop)
        return future.result()

    def get_me(self):
        future = asyncio.run_coroutine_threadsafe(self.client.get_me(), self.loop)
        return future.result()

    async def get_dialogs(self, limit=50):
        dialogs = []
        async for dialog in self.client.iter_dialogs(limit=limit):
            print(dialog.name, 'has ID', dialog.id)
            dialogs.append(dialog)
        return dialogs

    def send_message(self, to, text):
        future = asyncio.run_coroutine_threadsafe(self.client.send_message(to, text), self.loop)
        return future.result()

    def download_avatar(self, entity, filename):
        path = f"{IMAGES_DIR}/{filename}"
        future = asyncio.run_coroutine_threadsafe(
            self.client.download_profile_photo(entity, file=path),
            self.loop
        )
        return future.result()
