import os
import sqlite3
import logging
import time
import threading
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, ContextTypes, filters

TOKEN = os.getenv("TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))

logging.basicConfig(
    format="%(asctime)s - YAHUDA SCORE - %(levelname)s - %(message)s",
    level=logging.INFO
)

# database
conn = sqlite3.connect("yahuda.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS scores (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    name TEXT,
    score INTEGER
)
""")
conn.commit()


# OWNER kontrol
def is_owner(user_id):
    return user_id == OWNER_ID


# 24 saat reset
def reset_loop():

    while True:

        time.sleep(86400)

        cursor.execute("DELETE FROM scores")
        conn.commit()

        print("YAHUDA SCORE RESETLENDİ")


# mesaj geldiğinde skor ekle
async def add_score(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    user_id = user.id
    username = user.username if user.username else "no_username"
    name = user.first_name

    cursor.execute("SELECT score FROM scores WHERE user_id=?", (user_id,))
    data = cursor.fetchone()

    if data is None:

        cursor.execute(
            "INSERT INTO scores VALUES (?, ?, ?, ?)",
            (user_id, username, name, 1)
        )

    else:

        cursor.execute(
            "UPDATE scores SET score=?, username=?, name=? WHERE user_id=?",
            (data[0] + 1, username, name, user_id)
        )

    conn.commit()


# herkes kullanabilir
async def skor(update: Update, context: ContextTypes.DEFAULT_TYPE):

    cursor.execute(
        "SELECT username, name, score FROM scores ORDER BY score DESC LIMIT 15"
    )

    rows = cursor.fetchall()

    text = """
𐱅 YAHUDA #KABİLE
━━━━━━━━━━━━━━━━━━━
⚡ DARK SCORE PANEL
━━━━━━━━━━━━━━━━━━━
"""

    rank = 1

    for username, name, score in rows:

        text += f"""
#{rank} ☠ {name}
└ 👤 @{username}
└ 💬 {score} mesaj
━━━━━━━━━━━━━━━━━━━
"""

        rank += 1

    text += "\n👁‍🗨 YAHUDA CORE ACTIVE"

    await update.message.reply_text(text)


# sadece OWNER kullanabilir
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_owner(update.effective_user.id):
        return

    await update.message.reply_text(
        """
𐱅 YAHUDA #KABİLE CORE
⚡ Sistem başlatıldı
☠ 24 saat reset aktif
👁‍🗨 Kabile izleniyor
"""
    )


# başlat
def main():

    threading.Thread(target=reset_loop, daemon=True).start()

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("skor", skor))

    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        add_score
    ))

    print("YAHUDA KABİLE SCORE ONLINE")

    app.run_polling()


if __name__ == "__main__":
    main()
