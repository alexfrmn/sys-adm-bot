#!/usr/bin/env python3
"""
Add post to queue for @sys_adm channel.

Usage:
    # Auto-schedule to next available morning slot (7:00-8:00 MSK)
    python add_post.py --text "Post text"

    # Schedule to specific date/time
    python add_post.py --text "Post text" --schedule "2026-02-05T07:30"

    # Post immediately
    python add_post.py --text "Post text" --now
"""

import argparse
import json
import random
import sys
from datetime import datetime, timedelta
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


def get_next_available_slot(queue: dict) -> datetime:
    """Find next available morning slot (7:00-8:00 MSK)."""
    tz = ZoneInfo(TIMEZONE)
    now = datetime.now(tz)

    # Get all scheduled dates
    scheduled_dates = set()
    for post in queue.get("posts", []):
        if post.get("status") == "pending":
            try:
                dt = datetime.fromisoformat(post["scheduled"])
                scheduled_dates.add(dt.date())
            except:
                pass

    # Find next available date (start from tomorrow)
    check_date = now.date() + timedelta(days=1)
    while check_date in scheduled_dates:
        check_date += timedelta(days=1)

    # Random time between 07:00 and 07:59
    hour = 7
    minute = random.randint(0, 59)

    return datetime(
        check_date.year, check_date.month, check_date.day,
        hour, minute, 0, tzinfo=tz
    )


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
        # Auto-schedule to next available morning slot
        scheduled_dt = get_next_available_slot(queue)

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
    parser.add_argument("--schedule", "-s", help="Scheduled time (ISO format: 2026-02-05T07:30)")
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
