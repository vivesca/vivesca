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
    import sys

    from telethon import TelegramClient

    api_id = int(os.environ["TELEGRAM_API_ID"])
    api_hash = os.environ["TELEGRAM_API_HASH"]
    SESSION_DIR.mkdir(parents=True, exist_ok=True)
    session_path = str(SESSION_DIR / SESSION_NAME)

    phone = sys.argv[1] if len(sys.argv) > 1 else None
    code = sys.argv[2] if len(sys.argv) > 2 else None

    client = TelegramClient(session_path, api_id, api_hash)
    await client.connect()

    if not await client.is_user_authorized():
        if not phone:
            phone = input("Phone (with country code): ")
        await client.send_code_request(phone)
        if not code:
            code = input("Enter the code you received: ")
        await client.sign_in(phone, code)

    me = await client.get_me()  # type: ignore[misc]
    first = getattr(me, "first_name", None) or "unknown"
    phone = getattr(me, "phone", None) or "unknown"
    print(f"Authenticated as: {first} ({phone})")
    await client.disconnect()  # type: ignore[misc]


if __name__ == "__main__":
    asyncio.run(main())
