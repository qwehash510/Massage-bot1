import os
import json
import time
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, ContextTypes, filters

TOKEN = os.getenv("TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))

DATA_FILE = "scores.json"
RESET_TIME = 86400  # 24 saat

# veri yükle
def load():
    if not os.path.exists(DATA_FILE):
        return {"users": {}, "last_reset": time.time()}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

# veri kaydet
def save(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

data = load()

# reset sistemi
def reset_check():
    now = time.time()
    if now - data["last_reset"] > RESET_TIME:
        data["users"] = {}
        data["last_reset"] = now
        save(data)

# start (SADECE OWNER)
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return

    await update.message.reply_text(
        "⚡ YAHUDA #KABİLE SCORE SYSTEM ONLINE\n"
        "🧬 Sistem aktif.\n"
        "💀 Mesaj atan herkes skor kazanır."
    )

# skor sistemi
async def score(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reset_check()

    user = update.effective_user
    uid = str(user.id)

    if uid not in data["users"]:
        data["users"][uid] = {
            "name": user.first_name,
            "username": user.username,
            "score": 0
        }

    data["users"][uid]["score"] += 1
    save(data)

# skor göster
async def skor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)

    if uid not in data["users"]:
        await update.message.reply_text("Skorun yok.")
        return

    s = data["users"][uid]["score"]

    await update.message.reply_text(
        f"⚡ YAHUDA SKOR\n"
        f"👤 @{update.effective_user.username}\n"
        f"💀 Skor: {s}"
    )

# main
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("skor", skor))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, score))

    print("YAHUDA SCORE BOT ONLINE")

    app.run_polling()

if __name__ == "__main__":
    main()
