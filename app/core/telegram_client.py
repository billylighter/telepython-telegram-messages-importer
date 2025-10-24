import asyncio
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from telethon.tl.types import User

class TelegramClientManager:
    def __init__(self):
        self.client = None
        self.loop = asyncio.get_event_loop()

    def connect(self, session_path: str, api_id: int, api_hash: str):
        self.client = TelegramClient(session_path, api_id, api_hash)
        self.loop.run_until_complete(self.client.connect())
        return self.client

    def is_authorized(self):
        return self.loop.run_until_complete(self.client.is_user_authorized())

    def disconnect(self):
        if self.client:
            self.loop.run_until_complete(self.client.disconnect())
            self.client = None

    def get_me(self) -> User:
        return self.loop.run_until_complete(self.client.get_me())

    async def get_dialogs(self, limit=50):
        return await self.client.get_dialogs(limit=limit)

    async def send_message(self, entity, message):
        return await self.client.send_message(entity, message)

    # -------------------- Телефонный вход --------------------
    def send_code(self, phone):
        """Отправка кода на номер телефона"""
        return self.loop.run_until_complete(self.client.send_code_request(phone))

    def sign_in(self, phone, code, phone_code_hash=None):
        """Вход с кодом из Telegram"""
        return self.loop.run_until_complete(
            self.client.sign_in(phone=phone, code=code, phone_code_hash=phone_code_hash)
        )

    def sign_in_2fa(self, password):
        """Вход через двухфакторную аутентификацию"""
        return self.loop.run_until_complete(self.client.sign_in(password=password))

    def download_avatar(self, user, filename):
        """Скачать аватар пользователя и вернуть путь к файлу"""
        file_path = self.loop.run_until_complete(self.client.download_profile_photo(user, file=filename))
        return file_path
