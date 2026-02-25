import os
import time
import asyncio
import random
import string
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from pyrogram import Client, filters
from pyrogram.types import ChatPermissions

# ENV
API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
BOT_TOKEN = os.environ["BOT_TOKEN"]
PORT = int(os.environ.get("PORT", 10000))

# STYLE
YAHUDA = "『 ʏᴀʜᴜᴅᴀ 』"

# CLIENT
app = Client(
    "yahuda_godmode",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    workers=100
)

# DATABASE
joins = {}
messages = {}
captcha_db = {}
global_ban = set()
whitelist = set()
locked = set()

# SETTINGS
JOIN_LIMIT = 5
JOIN_TIME = 10

FLOOD_LIMIT = 7
FLOOD_TIME = 8

CAPTCHA_TIMEOUT = 60
LOCK_TIME = 30

SPAM_WORDS = [
    "http",
    "t.me/",
    "discord.gg",
    "https://",
    ".com"
]

# WEB SERVER (RENDER FIX)
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"YAHUDA GOD MODE ACTIVE")

def run_web():
    server = HTTPServer(("0.0.0.0", PORT), Handler)
    server.serve_forever()

# CAPTCHA
def generate_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

# LOCK
async def lock_group(chat_id):

    if chat_id in locked:
        return

    locked.add(chat_id)

    await app.set_chat_permissions(chat_id, ChatPermissions())

    await app.send_message(
        chat_id,
        f"{YAHUDA}\n\n🚨 RAID ALGILANDI\n🔒 GRUP KİLİTLENDİ\n🛡️ GOD MODE AKTİF"
    )

# UNLOCK
async def unlock_group(chat_id):

    if chat_id not in locked:
        return

    locked.remove(chat_id)

    await app.set_chat_permissions(
        chat_id,
        ChatPermissions(
            can_send_messages=True,
            can_send_media_messages=True,
            can_send_other_messages=True
        )
    )

    await app.send_message(
        chat_id,
        f"{YAHUDA}\n\n✅ GRUP AÇILDI\n🛡️ KORUMA DEVAM EDİYOR"
    )

# RAID PROTECT
@app.on_message(filters.new_chat_members)
async def raid_protect(client, message):

    chat_id = message.chat.id
    now = time.time()

    if chat_id not in joins:
        joins[chat_id] = []

    joins[chat_id].append(now)

    joins[chat_id] = [
        t for t in joins[chat_id]
        if now - t <= JOIN_TIME
    ]

    if len(joins[chat_id]) >= JOIN_LIMIT:

        await lock_group(chat_id)

        for user in message.new_chat_members:

            try:
                await client.ban_chat_member(chat_id, user.id)
                global_ban.add(user.id)
            except:
                pass

        await asyncio.sleep(LOCK_TIME)

        await unlock_group(chat_id)

        return

    # captcha
    for user in message.new_chat_members:

        if user.is_bot:
            await client.ban_chat_member(chat_id, user.id)
            return

        code = generate_code()

        captcha_db[user.id] = {
            "code": code,
            "chat": chat_id,
            "time": now
        }

        await message.reply(
            f"{YAHUDA}\n\n👤 {user.mention}\n🔐 KOD: `{code}`\n⏱ 60 saniye içinde yaz"
        )

# CAPTCHA VERIFY
@app.on_message(filters.text & filters.group)
async def captcha_verify(client, message):

    user_id = message.from_user.id

    if user_id not in captcha_db:
        return

    data = captcha_db[user_id]

    if time.time() - data["time"] > CAPTCHA_TIMEOUT:

        await client.ban_chat_member(
            data["chat"],
            user_id
        )

        del captcha_db[user_id]

        return

    if message.text == data["code"]:

        del captcha_db[user_id]

        await message.reply(
            f"{YAHUDA}\n\n✅ DOĞRULAMA BAŞARILI\n🛡️ HOŞGELDİN"
        )

# SPAM
@app.on_message(filters.text & filters.group)
async def spam_protect(client, message):

    user_id = message.from_user.id

    if user_id in whitelist:
        return

    text = message.text.lower()

    for word in SPAM_WORDS:

        if word in text:

            await message.delete()

            await client.ban_chat_member(
                message.chat.id,
                user_id
            )

            await message.reply(
                f"{YAHUDA}\n\n🚫 SPAM ENGELLENDİ"
            )

            return

# FLOOD
@app.on_message(filters.text & filters.group)
async def flood_protect(client, message):

    user_id = message.from_user.id

    now = time.time()

    if user_id not in messages:
        messages[user_id] = []

    messages[user_id].append(now)

    messages[user_id] = [
        t for t in messages[user_id]
        if now - t <= FLOOD_TIME
    ]

    if len(messages[user_id]) >= FLOOD_LIMIT:

        await client.ban_chat_member(
            message.chat.id,
            user_id
        )

        await message.reply(
            f"{YAHUDA}\n\n⚡ FLOOD ENGELLENDİ"
        )

# COMMANDS

@app.on_message(filters.command("yahuda"))
async def cmd_status(client, message):

    await message.reply(
        f"{YAHUDA}\n\n🛡️ GOD MODE AKTİF\n⭐ KORUMA: 5/5\n⚡ DURUM: STABİL"
    )

@app.on_message(filters.command("kilit"))
async def cmd_lock(client, message):

    await lock_group(message.chat.id)

@app.on_message(filters.command("ac"))
async def cmd_unlock(client, message):

    await unlock_group(message.chat.id)

@app.on_message(filters.command("whitelist"))
async def cmd_whitelist(client, message):

    if message.reply_to_message:

        uid = message.reply_to_message.from_user.id

        whitelist.add(uid)

        await message.reply(
            f"{YAHUDA}\n\n✅ WHITELIST EKLENDİ"
        )

# START
async def run_bot():

    print("YAHUDA GOD MODE BASLADI")

    await app.start()

    await asyncio.Future()

if __name__ == "__main__":

    threading.Thread(target=run_web).start()

    asyncio.run(run_bot())
