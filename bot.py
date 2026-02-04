#!/usr/bin/env python3
"""
Interactive bot for managing @sys_adm channel queue.
Features:
- Button menu for easy navigation
- Photo attachment to posts
- AI artifact checker
- Queue management
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import (
    InlineKeyboardButton, InlineKeyboardMarkup,
    ReplyKeyboardMarkup, KeyboardButton
)
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
ADMIN_ID = 219787633  # Alex's Telegram ID

# Main menu keyboard
MAIN_MENU = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📋 Очередь"), KeyboardButton(text="🎨 Промпты")],
        [KeyboardButton(text="✍️ Проверить текст"), KeyboardButton(text="📊 Статус")],
    ],
    resize_keyboard=True,
    is_persistent=True
)


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


def format_post_preview(post: dict, short: bool = False) -> str:
    """Format post for preview."""
    text = post.get("text", "")[:40 if short else 50]
    scheduled = post.get("scheduled", "")
    if scheduled:
        try:
            dt = datetime.fromisoformat(scheduled)
            scheduled = dt.strftime("%d.%m %H:%M")
        except:
            pass
    has_image = "🖼" if post.get("image_url") else "📝"
    return f"{has_image} {scheduled}: {text}..."


# ==================== HANDLERS ====================

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    await message.answer(
        "👋 <b>Sys-Adm Bot</b>\n\n"
        "Управление каналом @sys_adm\n\n"
        "📸 <b>Картинки:</b> просто скинь фото\n"
        "✍️ <b>Проверка:</b> ответь на текст кнопкой",
        parse_mode="HTML",
        reply_markup=MAIN_MENU
    )


@dp.message(F.text == "📋 Очередь")
async def btn_queue(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    posts = get_pending_posts()
    if not posts:
        await message.answer("📭 Очередь пуста", reply_markup=MAIN_MENU)
        return

    text = "📋 <b>Очередь постов:</b>\n\n"
    for post in posts:
        post_id = post.get("id")
        has_img = "✅" if post.get("image_url") else "❌"
        scheduled = post.get("scheduled", "")
        try:
            dt = datetime.fromisoformat(scheduled)
            date_str = dt.strftime("%d.%m %H:%M")
        except:
            date_str = "?"

        preview = post.get("text", "")[:60]
        text += f"<b>#{post_id}</b> | {date_str} | Картинка: {has_img}\n"
        text += f"<i>{preview}...</i>\n\n"

    await message.answer(text, parse_mode="HTML", reply_markup=MAIN_MENU)


@dp.message(F.text == "🎨 Промпты")
async def btn_prompts(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    posts = get_pending_posts()
    posts_without_images = [p for p in posts if not p.get("image_url")]

    if not posts_without_images:
        await message.answer("✅ Все посты уже с картинками!", reply_markup=MAIN_MENU)
        return

    # Style reference
    style = (
        "Dark background, grunge aesthetic, film grain texture, glitch effects, "
        "red accent color, underground techno style, distressed typography, "
        "circle badge design, anti-mainstream vibe"
    )

    # Keyword-based prompts
    prompts_map = {
        "психолог": f"Brain with cracks and healing light, therapy concept, {style}",
        "терапевт": f"Brain with cracks and healing light, therapy concept, {style}",
        "выгор": f"Burning candle melting into laptop, burnout concept, {style}",
        "бот": f"Chat interface with AI brain, digital journal concept, {style}",
        "вертушк": f"Vinyl turntable with dust particles, DJ equipment, {style}",
        "пластин": f"Vinyl record collection, music passion concept, {style}",
        "23:00": f"Clock showing 23:00 with laptop closing, sleep vs work concept, {style}",
        "сон": f"Moon and pillow with laptop shutting down, rest concept, {style}",
        "автоматиз": f"Robot hands typing code, automation concept, {style}",
    }

    text = "🎨 <b>Промпты для Nano Banana Pro:</b>\n\n"

    for post in posts_without_images:
        post_text = post.get("text", "").lower()
        scheduled = post.get("scheduled", "")
        try:
            dt = datetime.fromisoformat(scheduled)
            date_str = dt.strftime("%d.%m")
        except:
            date_str = "?"

        # Find matching prompt
        prompt = None
        matched_key = None
        for key, p in prompts_map.items():
            if key in post_text:
                prompt = p
                matched_key = key
                break

        if prompt:
            text += f"<b>#{post.get('id')} ({date_str}) — {matched_key}:</b>\n"
            text += f"<code>{prompt}</code>\n\n"
        else:
            text += f"<b>#{post.get('id')} ({date_str}):</b>\n"
            text += f"<i>Промпт не найден, придумай сам</i>\n\n"

    await message.answer(text, parse_mode="HTML", reply_markup=MAIN_MENU)


@dp.message(F.text == "✍️ Проверить текст")
async def btn_check_hint(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    await message.answer(
        "✍️ <b>Проверка текста на AI-артефакты</b>\n\n"
        "Отправь текст следующим сообщением\n"
        "или ответь на сообщение с текстом",
        parse_mode="HTML",
        reply_markup=MAIN_MENU
    )

    # Set state to expect text
    dp["awaiting_check"] = True


@dp.message(F.text == "📊 Статус")
async def btn_status(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    posts = get_pending_posts()
    total = len(posts)
    with_images = len([p for p in posts if p.get("image_url")])
    without_images = total - with_images

    # Next post
    next_post = None
    if posts:
        posts_sorted = sorted(posts, key=lambda p: p.get("scheduled", ""))
        next_post = posts_sorted[0]

    text = "📊 <b>Статус канала @sys_adm</b>\n\n"
    text += f"📋 Постов в очереди: <b>{total}</b>\n"
    text += f"🖼 С картинками: <b>{with_images}</b>\n"
    text += f"📝 Без картинок: <b>{without_images}</b>\n\n"

    if next_post:
        scheduled = next_post.get("scheduled", "")
        try:
            dt = datetime.fromisoformat(scheduled)
            date_str = dt.strftime("%d.%m в %H:%M")
        except:
            date_str = "?"
        text += f"⏰ Следующий пост: <b>{date_str}</b>\n"
        text += f"<i>{next_post.get('text', '')[:50]}...</i>"

    await message.answer(text, parse_mode="HTML", reply_markup=MAIN_MENU)


@dp.message(F.photo)
async def handle_photo(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    posts = get_pending_posts()
    posts_without_images = [p for p in posts if not p.get("image_url")]

    if not posts_without_images:
        await message.answer(
            "✅ Все посты уже с картинками!\n"
            "Добавь новый пост через add_post.py",
            reply_markup=MAIN_MENU
        )
        return

    # Save photo temporarily
    photo = message.photo[-1]  # Highest resolution

    # Create keyboard with post options
    keyboard = []
    for post in posts_without_images:
        preview = format_post_preview(post, short=True)
        callback_data = f"attach_{post['id']}"
        keyboard.append([InlineKeyboardButton(text=preview, callback_data=callback_data)])

    # Store file_id in memory for callback
    dp["pending_photo"] = photo.file_id

    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    await message.answer(
        "🖼 <b>К какому посту привязать?</b>",
        reply_markup=markup,
        parse_mode="HTML"
    )


@dp.callback_query(F.data.startswith("attach_"))
async def attach_photo(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return

    # Parse post ID
    post_id = int(callback.data.split("_")[1])
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

    await callback.message.edit_text(
        f"✅ Картинка привязана к посту <b>#{post_id}</b>",
        parse_mode="HTML"
    )
    await callback.answer("Готово!")


@dp.message(F.text)
async def handle_text(message: types.Message):
    """Handle any text - check for AI artifacts if awaiting or reply."""
    if message.from_user.id != ADMIN_ID:
        return

    # Skip menu buttons
    if message.text in ["📋 Очередь", "🎨 Промпты", "✍️ Проверить текст", "📊 Статус"]:
        return

    # Get text to check
    text_to_check = None

    # Check if replying to a message
    if message.reply_to_message and message.reply_to_message.text:
        text_to_check = message.reply_to_message.text
    # Check if awaiting text
    elif dp.get("awaiting_check"):
        text_to_check = message.text
        dp["awaiting_check"] = False

    if not text_to_check:
        return

    # AI artifact patterns (Critic A: Generic Detector)
    generic_phrases = [
        "важно понимать", "важно отметить", "стоит подчеркнуть",
        "в современном мире", "на сегодняшний день", "безусловно",
        "в заключение", "подводя итог", "таким образом",
        "играет ключевую роль", "является важным", "необходимо учитывать",
        "следует отметить", "нельзя не упомянуть", "очевидно, что",
        "не секрет, что", "как известно", "само собой разумеется"
    ]

    issues = []
    text_lower = text_to_check.lower()

    # Check generic phrases
    for phrase in generic_phrases:
        if phrase in text_lower:
            issues.append(f"🔴 <b>Generic:</b> «{phrase}»")

    # Check sentence length uniformity (Critic B)
    sentences = [s.strip() for s in text_to_check.replace('!', '.').replace('?', '.').split('.') if s.strip()]
    if len(sentences) >= 3:
        lengths = [len(s.split()) for s in sentences]
        avg_len = sum(lengths) / len(lengths)
        uniform_count = sum(1 for l in lengths if abs(l - avg_len) < 3)
        if uniform_count >= len(lengths) * 0.7:
            issues.append("🟡 <b>Rhythm:</b> предложения слишком одинаковые")

    # Check for specificity (Critic C)
    has_numbers = any(c.isdigit() for c in text_to_check)
    has_personal = any(p in text_lower for p in ["я ", "мой ", "моя ", "мне ", "меня ", "мои "])

    if not has_numbers:
        issues.append("🟡 <b>Specificity:</b> нет чисел/дат")
    if not has_personal:
        issues.append("🟡 <b>Specificity:</b> нет личного опыта")

    # Format response
    if issues:
        response = f"🔍 <b>Найдено {len(issues)} проблем:</b>\n\n"
        response += "\n".join(issues)
    else:
        response = "✅ <b>Текст чистый!</b>\nAI-артефактов не обнаружено."

    await message.answer(response, parse_mode="HTML", reply_markup=MAIN_MENU)


async def main():
    logger.info("Starting sys-adm-bot...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
