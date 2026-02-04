#!/usr/bin/env python3
"""Send local photo to channel."""

import sys
import httpx
from config import BOT_TOKEN, CHANNEL_ID

API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"


def send_local_photo(file_path: str, caption: str = None) -> bool:
    """Send local photo file to channel."""
    try:
        with open(file_path, 'rb') as f:
            files = {"photo": f}
            data = {"chat_id": CHANNEL_ID}
            if caption:
                data["caption"] = caption

            response = httpx.post(
                f"{API_URL}/sendPhoto",
                data=data,
                files=files,
                timeout=60
            )
            response.raise_for_status()
            print(f"✓ Photo sent successfully")
            return True
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: send_local_photo.py <file_path> [caption]")
        sys.exit(1)

    file_path = sys.argv[1]
    caption = sys.argv[2] if len(sys.argv) > 2 else None

    send_local_photo(file_path, caption)
