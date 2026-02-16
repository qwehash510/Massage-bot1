import os
import json
import asyncio
from datetime import datetime, timedelta

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ==============================
# CONFIG
# ==============================

TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = 8464933639  # BURAYA KENDİ TELEGRAM ID'ni yaz

DATA_FILE = "scores.json"
RESET_HOURS = 24

# ==============================
# DATA SYSTEM
# ==============================

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"users": {}, "last_reset": str(datetime.now())}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)


data = load_data()

# ==============================
# RESET SYSTEM
# ==============================

async def auto_reset():
    while True:
        now = datetime.now()
        last_reset = datetime.fromisoformat(data["last_reset"])

        if now - last_reset >= timedelta(hours=RESET_HOURS):
            data["users"] = {}
            data["last_reset"] = str(now)
            save_data(data)
            print("Skorlar resetlendi")

        await asyncio.sleep(60)


# ==============================
# START COMMAND (OWNER ONLY)
# ==============================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != OWNER_ID:
        return

    msg = f"""
⚡ YAHUDA #KABİLE V6 AKTİF

💀 Hacker Score System Online
🧬 Sistem Stabil
⚠️ 24 Saatte Reset Aktif

Owner: @{update.effective_user.username}
"""

    await update.message.reply_text(msg)


# ==============================
# SCORE COMMAND
# ==============================

async def skor(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user
    uid = str(user.id)

    if uid not in data["users"]:
        score = 0
    else:
        score = data["users"][uid]["score"]

    username = user.username or user.first_name

    msg = f"""
⚡ YAHUDA SKOR SİSTEMİ

👤 Kullanıcı: @{username}
💀 Skor: {score}

🧬 YAHUDA #KABİLE
"""

    await update.message.reply_text(msg)


# ==============================
# MESSAGE LISTENER
# ==============================

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user
    uid = str(user.id)

    if user.is_bot:
        return

    if uid not in data["users"]:
        data["users"][uid] = {
            "username": user.username,
            "name": user.first_name,
            "score": 0,
        }

    data["users"][uid]["score"] += 1

    save_data(data)


# ==============================
# MAIN
# ==============================

async def main():

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("skor", skor))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    asyncio.create_task(auto_reset())

    print("YAHUDA BOT V6 AKTİF")

    await app.run_polling()


if __name__ == "__main__":
    asyncio.run(main())
