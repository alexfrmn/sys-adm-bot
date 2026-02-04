#!/usr/bin/env python3
"""
Interactive bot for managing @sys_adm channel queue.
- Send photo → bot asks which post to attach it to
- /queue → show pending posts
- /prompts → get image prompts for posts
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from pathlib import Path

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from zoneinfo import ZoneInfo

from config import BOT_TOKEN, QUEUE_FILE, TIMEZONE

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Bot setup
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Images directory
IMAGES_DIR = Path("/opt/lifecoach/sys-adm-bot/images")
IMAGES_DIR.mkdir(exist_ok=True)

# Admin ID (only you can use this bot)
ADMIN_ID = 68632434  # Your Telegram ID


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


def get_pending_posts() -> list:
    """Get list of pending posts."""
    queue = load_queue()
    return [p for p in queue.get("posts", []) if p.get("status") == "pending"]


def format_post_preview(post: dict) -> str:
    """Format post for preview."""
    text = post.get("text", "")[:50]
    scheduled = post.get("scheduled", "")
    if scheduled:
        try:
            dt = datetime.fromisoformat(scheduled)
            scheduled = dt.strftime("%d.%m %H:%M")
        except:
            pass
    has_image = "🖼" if post.get("image_url") else "📝"
    return f"{has_image} {scheduled}: {text}..."


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    await message.answer(
        "👋 Бот для управления @sys_adm\n\n"
        "📸 Отправь фото — привяжу к посту\n"
        "📋 /queue — очередь постов\n"
        "🎨 /prompts — промпты для картинок"
    )


@dp.message(Command("queue"))
async def cmd_queue(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    posts = get_pending_posts()
    if not posts:
        await message.answer("📭 Очередь пуста")
        return

    text = "📋 **Очередь постов:**\n\n"
    for post in posts:
        preview = format_post_preview(post)
        text += f"• {preview}\n"

    await message.answer(text, parse_mode="Markdown")


@dp.message(Command("prompts"))
async def cmd_prompts(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    posts = get_pending_posts()
    if not posts:
        await message.answer("📭 Очередь пуста")
        return

    # Style reference for all prompts
    style = (
        "Dark background, grunge aesthetic, film grain texture, glitch effects, "
        "red accent color, underground techno style, distressed typography, "
        "circle badge design, anti-mainstream vibe"
    )

    prompts = {
        "психолог": f"Brain with cracks and healing light, therapy concept, {style}",
        "бот": f"Chat interface with AI brain, digital journal concept, {style}",
        "вертушки": f"Vinyl turntable with dust particles, DJ equipment, {style}",
        "23:00": f"Clock showing 23:00 with laptop closing, sleep vs work concept, {style}",
    }

    text = "🎨 **Промпты для Nano Banana Pro:**\n\n"

    for post in posts:
        post_text = post.get("text", "").lower()
        for key, prompt in prompts.items():
            if key in post_text:
                scheduled = post.get("scheduled", "")
                try:
                    dt = datetime.fromisoformat(scheduled)
                    date_str = dt.strftime("%d.%m")
                except:
                    date_str = "?"
                text += f"**{date_str} ({key}):**\n`{prompt}`\n\n"
                break

    await message.answer(text, parse_mode="Markdown")


@dp.message(F.photo)
async def handle_photo(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    posts = get_pending_posts()
    if not posts:
        await message.answer("📭 Очередь пуста. Сначала добавь посты.")
        return

    # Save photo temporarily
    photo = message.photo[-1]  # Highest resolution
    file = await bot.get_file(photo.file_id)

    # Create keyboard with post options
    keyboard = []
    for post in posts:
        preview = format_post_preview(post)
        callback_data = f"attach_{post['id']}_{photo.file_id}"
        # Callback data max 64 bytes, so truncate if needed
        if len(callback_data) > 64:
            callback_data = f"attach_{post['id']}"
        keyboard.append([InlineKeyboardButton(text=preview, callback_data=callback_data)])

    # Store file_id in memory for callback
    dp["pending_photo"] = photo.file_id

    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    await message.answer("К какому посту привязать картинку?", reply_markup=markup)


@dp.callback_query(F.data.startswith("attach_"))
async def attach_photo(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return

    # Parse post ID
    parts = callback.data.split("_")
    post_id = int(parts[1])

    # Get file_id from callback or memory
    if len(parts) > 2:
        file_id = "_".join(parts[2:])
    else:
        file_id = dp.get("pending_photo")

    if not file_id:
        await callback.answer("❌ Фото не найдено, отправь заново")
        return

    # Download and save photo
    file = await bot.get_file(file_id)
    file_path = IMAGES_DIR / f"post_{post_id}.jpg"
    await bot.download_file(file.file_path, file_path)

    # Update queue
    queue = load_queue()
    for post in queue.get("posts", []):
        if post.get("id") == post_id:
            post["image_url"] = str(file_path)
            break
    save_queue(queue)

    await callback.message.edit_text(f"✅ Картинка привязана к посту #{post_id}")
    await callback.answer()


async def main():
    logger.info("Starting bot...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
