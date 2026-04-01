"""One-time Telethon user auth. Run interactively:

    uv run python -m metabolon.organelles.telegram_auth

Enters phone, waits for OTP code, saves session file.
"""
import asyncio
import os
from pathlib import Path

SESSION_DIR = Path.home() / ".config" / "telethon"
SESSION_NAME = "vivesca"


async def main():
    from telethon import TelegramClient

    api_id = int(os.environ["TELEGRAM_API_ID"])
    api_hash = os.environ["TELEGRAM_API_HASH"]
    SESSION_DIR.mkdir(parents=True, exist_ok=True)
    session_path = str(SESSION_DIR / SESSION_NAME)

    client = TelegramClient(session_path, api_id, api_hash)
    await client.start()
    me = await client.get_me()
    print(f"Authenticated as: {me.first_name} ({me.phone})")
    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
