#!/usr/bin/env python3
"""
Add post to queue for @sys_adm channel.

Usage:
    # Schedule post
    python add_post.py --text "Post text" --schedule "2026-02-05T18:00"

    # Schedule with image
    python add_post.py --text "Caption" --image "https://..." --schedule "2026-02-05T18:00"

    # Post immediately (schedule = now)
    python add_post.py --text "Post text" --now
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from config import QUEUE_FILE, TIMEZONE


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


def get_next_id(queue: dict) -> int:
    """Get next available post ID."""
    if not queue.get("posts"):
        return 1
    return max(p.get("id", 0) for p in queue["posts"]) + 1


def add_post(text: str, image_url: str = None, scheduled: str = None, now: bool = False) -> dict:
    """Add post to queue."""
    queue = load_queue()

    # Determine scheduled time
    if now:
        scheduled_dt = datetime.now(ZoneInfo(TIMEZONE))
    elif scheduled:
        scheduled_dt = datetime.fromisoformat(scheduled)
        if scheduled_dt.tzinfo is None:
            scheduled_dt = scheduled_dt.replace(tzinfo=ZoneInfo(TIMEZONE))
    else:
        print("Error: Either --schedule or --now is required")
        sys.exit(1)

    post = {
        "id": get_next_id(queue),
        "scheduled": scheduled_dt.isoformat(),
        "text": text,
        "image_url": image_url,
        "status": "pending",
        "created_at": datetime.now(ZoneInfo(TIMEZONE)).isoformat()
    }

    queue["posts"].append(post)
    save_queue(queue)

    return post


def main():
    parser = argparse.ArgumentParser(description="Add post to @sys_adm channel queue")
    parser.add_argument("--text", "-t", required=True, help="Post text")
    parser.add_argument("--image", "-i", help="Image URL or local file path")
    parser.add_argument("--schedule", "-s", help="Scheduled time (ISO format: 2026-02-05T18:00)")
    parser.add_argument("--now", "-n", action="store_true", help="Post immediately")

    args = parser.parse_args()

    post = add_post(
        text=args.text,
        image_url=args.image,
        scheduled=args.schedule,
        now=args.now
    )

    print(f"✓ Post added to queue:")
    print(f"  ID: {post['id']}")
    print(f"  Scheduled: {post['scheduled']}")
    print(f"  Text: {post['text'][:50]}...")
    if post['image_url']:
        print(f"  Image: {post['image_url'][:50]}...")


if __name__ == "__main__":
    main()
