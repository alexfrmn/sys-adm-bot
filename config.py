"""Configuration for sys-adm channel bot."""

import os
from dotenv import load_dotenv

load_dotenv()

# Telegram
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID", "@sys_adm")
ADMIN_ID = int(os.getenv("ADMIN_ID", "219787633"))

# Paths
QUEUE_FILE = "/opt/lifecoach/sys-adm-bot/queue.json"
POSTED_DIR = "/opt/lifecoach/sys-adm-bot/posted"
LOG_FILE = "/opt/lifecoach/sys-adm-bot/bot.log"

# Timezone
TIMEZONE = "Europe/Moscow"
