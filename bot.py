import os
import sqlite3
import logging
import datetime
import math
from PIL import Image, ImageDraw, ImageFont

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

# CONFIG
TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))

logging.basicConfig(level=logging.INFO)

# DATABASE
conn = sqlite3.connect("yahuda.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
user_id INTEGER PRIMARY KEY,
username TEXT,
xp INTEGER,
level INTEGER,
total INTEGER,
daily INTEGER,
weekly INTEGER,
last_day TEXT,
last_week TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS system(
status TEXT
)
""")

conn.commit()

# FIRST RUN OFF
cursor.execute("SELECT status FROM system")
if not cursor.fetchone():
    cursor.execute("INSERT INTO system VALUES('OFF')")
    conn.commit()


# STATUS CHECK
def is_active():

    cursor.execute("SELECT status FROM system")
    return cursor.fetchone()[0] == "ON"


# TIME
def get_day():
    return datetime.datetime.now().strftime("%Y-%m-%d")

def get_week():
    return datetime.datetime.now().strftime("%Y-%W")


# LEVEL
def calc_level(xp):
    return int(math.sqrt(xp / 10))


# AUTO RESET SYSTEM
def auto_reset():

    today = get_day()
    week = get_week()

    cursor.execute("SELECT user_id,last_day,last_week FROM users")
    users = cursor.fetchall()

    for user_id, last_day, last_week in users:

        if last_day != today:

            cursor.execute("""
            UPDATE users SET daily=0,last_day=?
            WHERE user_id=?
            """, (today, user_id))

        if last_week != week:

            cursor.execute("""
            UPDATE users SET weekly=0,last_week=?
            WHERE user_id=?
            """, (week, user_id))

    conn.commit()


# CREATE RANK CARD IMAGE
def create_rank_card(username, level, xp, total):

    width = 800
    height = 300

    img = Image.new("RGB", (width, height), (5, 5, 5))
    draw = ImageDraw.Draw(img)

    green = (0, 255, 120)

    font = ImageFont.load_default()

    draw.text((50, 30), "YAHUDA #KABİLE", fill=green, font=font)

    draw.text((50, 80), f"USER: @{username}", fill=green, font=font)

    draw.text((50, 120), f"LEVEL: {level}", fill=green, font=font)

    draw.text((50, 160), f"XP: {xp}", fill=green, font=font)

    draw.text((50, 200), f"TOTAL MSG: {total}", fill=green, font=font)

    # XP BAR
    bar_x = 50
    bar_y = 240
    bar_width = 700
    bar_height = 20

    draw.rectangle(
        (bar_x, bar_y, bar_x + bar_width, bar_y + bar_height),
        outline=green,
        width=2
    )

    progress = int((xp % 100) * 7)

    draw.rectangle(
        (bar_x, bar_y, bar_x + progress, bar_y + bar_height),
        fill=green
    )

    path = f"rank_{username}.png"

    img.save(path)

    return path


# START OWNER ONLY
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != OWNER_ID:
        return

    cursor.execute("UPDATE system SET status='ON'")
    conn.commit()

    await update.message.reply_text(
"""
☠ YAHUDA #KABİLE ☠
━━━━━━━━━━━━━━━━━━
SYSTEM STATUS: ONLINE
ROOT ACCESS GRANTED
"""
)


# STOP OWNER ONLY
async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != OWNER_ID:
        return

    cursor.execute("UPDATE system SET status='OFF'")
    conn.commit()

    await update.message.reply_text(
"""
☠ YAHUDA SYSTEM ☠
━━━━━━━━━━━━━━━━━━
SYSTEM STATUS: OFFLINE
"""
)


# MESSAGE COUNT SYSTEM
async def count(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_active():
        return

    if update.message.chat.type == "private":
        return

    auto_reset()

    user = update.message.from_user

    user_id = user.id
    username = user.username or "unknown"

    today = get_day()
    week = get_week()

    cursor.execute("""
    SELECT xp,total,daily,weekly FROM users WHERE user_id=?
    """, (user_id,))

    data = cursor.fetchone()

    if data:

        xp, total, daily, weekly = data

        xp += 5
        total += 1
        daily += 1
        weekly += 1

        level = calc_level(xp)

        cursor.execute("""
        UPDATE users SET
        username=?,
        xp=?,
        level=?,
        total=?,
        daily=?,
        weekly=?,
        last_day=?,
        last_week=?
        WHERE user_id=?
        """, (
            username,
            xp,
            level,
            total,
            daily,
            weekly,
            today,
            week,
            user_id
        ))

    else:

        cursor.execute("""
        INSERT INTO users VALUES(?,?,?,?,?,?,?,?,?)
        """, (
            user_id,
            username,
            5,
            0,
            1,
            1,
            1,
            today,
            week
        ))

    conn.commit()


# TOP PANEL
async def top(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_active():
        return

    keyboard = [

        [
            InlineKeyboardButton("📅 DAILY", callback_data="daily"),
            InlineKeyboardButton("📅 WEEKLY", callback_data="weekly")
        ],

        [
            InlineKeyboardButton("☠ TOTAL", callback_data="total")
        ]

    ]

    await update.message.reply_text(
"""
☠ YAHUDA RANK PANEL ☠
━━━━━━━━━━━━━━━━━━
SELECT CATEGORY
""",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# BUTTON HANDLER
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    type = query.data

    if type == "daily":

        cursor.execute("SELECT username,daily,level FROM users ORDER BY daily DESC LIMIT 10")

    elif type == "weekly":

        cursor.execute("SELECT username,weekly,level FROM users ORDER BY weekly DESC LIMIT 10")

    else:

        cursor.execute("SELECT username,total,level FROM users ORDER BY total DESC LIMIT 10")

    rows = cursor.fetchall()

    text = "☠ YAHUDA RANKING ☠\n━━━━━━━━━━━━━━━━━━\n"

    i = 1

    for username, count, level in rows:

        text += f"{i}. @{username} | MSG: {count} | LVL: {level}\n"

        i += 1

    await query.edit_message_text(text)


# RANK CARD COMMAND
async def rank(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_active():
        return

    user_id = update.effective_user.id

    cursor.execute("""
    SELECT username,xp,level,total FROM users WHERE user_id=?
    """, (user_id,))

    data = cursor.fetchone()

    if not data:
        return

    username, xp, level, total = data

    path = create_rank_card(username, level, xp, total)

    await update.message.reply_photo(photo=open(path, "rb"))


# MAIN
def main():

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))

    app.add_handler(CommandHandler("top", top))
    app.add_handler(CommandHandler("rank", rank))

    app.add_handler(CallbackQueryHandler(button))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, count))

    print("YAHUDA ELITE SYSTEM ACTIVE")

    app.run_polling()


if __name__ == "__main__":
    main()
