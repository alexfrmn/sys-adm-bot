#!/usr/bin/env python3
"""
Sys-Adm Channel Poster
Reads queue.json and posts scheduled content to @sys_adm channel.
Run via cron every 5 minutes.
"""

import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

import httpx
from zoneinfo import ZoneInfo

from config import BOT_TOKEN, CHANNEL_ID, QUEUE_FILE, POSTED_DIR, LOG_FILE, TIMEZONE

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Telegram API
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"


def load_queue() -> dict:
    """Load queue from JSON file."""
    if not Path(QUEUE_FILE).exists():
        return {"posts": []}

    with open(QUEUE_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_queue(queue: dict) -> None:
    """Save queue to JSON file."""
    with open(QUEUE_FILE, 'w', encoding='utf-8') as f:
        json.dump(queue, f, ensure_ascii=False, indent=2)


def archive_post(post: dict) -> None:
    """Move posted content to archive."""
    Path(POSTED_DIR).mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_file = Path(POSTED_DIR) / f"post_{timestamp}.json"

    with open(archive_file, 'w', encoding='utf-8') as f:
        json.dump(post, f, ensure_ascii=False, indent=2)


def send_message(text: str) -> bool:
    """Send text message to channel."""
    try:
        response = httpx.post(
            f"{API_URL}/sendMessage",
            json={
                "chat_id": CHANNEL_ID,
                "text": text,
                "parse_mode": "HTML"
            },
            timeout=30
        )
        response.raise_for_status()
        logger.info(f"Message sent successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to send message: {e}")
        return False


def send_photo(image_source: str, caption: str = None) -> bool:
    """Send photo to channel. Supports URL or local file path."""
    try:
        # Check if it's a local file or URL
        if image_source.startswith(('http://', 'https://')):
            # Download from URL
            img_response = httpx.get(image_source, timeout=60)
            img_response.raise_for_status()
            photo_data = img_response.content
        else:
            # Read local file
            with open(image_source, 'rb') as f:
                photo_data = f.read()

        # Send to Telegram
        files = {"photo": ("image.jpg", photo_data)}
        data = {"chat_id": CHANNEL_ID}
        if caption:
            data["caption"] = caption
            data["parse_mode"] = "HTML"

        response = httpx.post(
            f"{API_URL}/sendPhoto",
            data=data,
            files=files,
            timeout=60
        )
        response.raise_for_status()
        logger.info(f"Photo sent successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to send photo: {e}")
        return False


def process_queue() -> None:
    """Process queue and post scheduled content."""
    queue = load_queue()

    if not queue.get("posts"):
        logger.debug("Queue is empty")
        return

    now = datetime.now(ZoneInfo(TIMEZONE))
    posts_to_remove = []

    for i, post in enumerate(queue["posts"]):
        if post.get("status") != "pending":
            continue

        # Parse scheduled time
        scheduled_str = post.get("scheduled")
        if not scheduled_str:
            logger.warning(f"Post {post.get('id')} has no scheduled time")
            continue

        try:
            scheduled = datetime.fromisoformat(scheduled_str)
            if scheduled.tzinfo is None:
                scheduled = scheduled.replace(tzinfo=ZoneInfo(TIMEZONE))
        except ValueError as e:
            logger.error(f"Invalid scheduled time for post {post.get('id')}: {e}")
            continue

        # Check if it's time to post
        if now >= scheduled:
            logger.info(f"Posting scheduled content: {post.get('id')}")

            success = False
            image_url = post.get("image_url")
            text = post.get("text", "")

            if image_url:
                success = send_photo(image_url, text)
            elif text:
                success = send_message(text)

            if success:
                post["status"] = "posted"
                post["posted_at"] = now.isoformat()
                archive_post(post)
                posts_to_remove.append(i)
            else:
                post["status"] = "failed"
                post["error_at"] = now.isoformat()

    # Remove posted items
    for i in sorted(posts_to_remove, reverse=True):
        queue["posts"].pop(i)

    save_queue(queue)


def main():
    """Main entry point."""
    logger.info("Starting queue processing...")
    process_queue()
    logger.info("Queue processing complete")


if __name__ == "__main__":
    main()
