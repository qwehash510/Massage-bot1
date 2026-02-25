import os, time, asyncio, random, string, logging
from pyrogram import Client, filters
from pyrogram.types import ChatPermissions
from dotenv import load_dotenv

# LOAD ENV
load_dotenv()

API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")

logging.basicConfig(level=logging.INFO)

YAHUDA = "『 ʏᴀʜᴜᴅᴀ 』"

EMOJI = {
    "raid":"🚨",
    "lock":"🔒",
    "unlock":"✅",
    "shield":"🛡️",
    "flood":"⚡",
    "spam":"🚫",
    "captcha":"⏱"
}

# CLIENT
app = Client(
    "yahuda_render_god",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    workers=100
)

# DATABASE
joins = {}
captcha_db = {}
messages = {}
global_ban = set()
locked = set()

# SETTINGS
JOIN_LIMIT = 5
JOIN_TIME = 10
FLOOD_LIMIT = 7
FLOOD_TIME = 8
CAPTCHA_TIMEOUT = 60
LOCK_TIME = 30

SPAM = ["http","t.me/","discord.gg"]

# CAPTCHA
def gen_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

# LOCK
async def lock_group(chat):
    if chat in locked:
        return
    locked.add(chat)

    await app.set_chat_permissions(chat, ChatPermissions())

    await app.send_message(
        chat,
        f"{YAHUDA}\n\n🚨 Raid algılandı\n🔒 Grup kilitlendi\n🛡️ GOD MODE aktif"
    )

# UNLOCK
async def unlock_group(chat):
    if chat not in locked:
        return

    locked.remove(chat)

    await app.set_chat_permissions(
        chat,
        ChatPermissions(
            can_send_messages=True,
            can_send_media_messages=True,
            can_send_other_messages=True
        )
    )

    await app.send_message(
        chat,
        f"{YAHUDA}\n\n✅ Grup tekrar açıldı\n🛡️ Sistem stabil"
    )

# JOIN PROTECTION
@app.on_message(filters.new_chat_members)
async def join_handler(client, message):

    chat = message.chat.id
    now = time.time()

    if chat not in joins:
        joins[chat] = []

    joins[chat].append(now)

    joins[chat] = [t for t in joins[chat] if now - t <= JOIN_TIME]

    if len(joins[chat]) >= JOIN_LIMIT:

        await lock_group(chat)

        for user in message.new_chat_members:
            try:
                await client.ban_chat_member(chat, user.id)
            except:
                pass

        await asyncio.sleep(LOCK_TIME)

        await unlock_group(chat)

        return

    for user in message.new_chat_members:

        code = gen_code()

        captcha_db[user.id] = {
            "code": code,
            "chat": chat,
            "time": now
        }

        await message.reply(
            f"{YAHUDA}\n\n👤 {user.mention}\n⏱ Kod: `{code}`\n60 saniye"
        )

# CAPTCHA VERIFY
@app.on_message(filters.text & filters.group)
async def captcha_handler(client, message):

    user = message.from_user.id

    if user not in captcha_db:
        return

    data = captcha_db[user]

    if time.time() - data["time"] > CAPTCHA_TIMEOUT:

        await client.ban_chat_member(data["chat"], user)

        del captcha_db[user]

        return

    if message.text == data["code"]:

        del captcha_db[user]

        await message.reply(
            f"{YAHUDA}\n\n✅ Doğrulama başarılı\n🛡️ Hoşgeldin"
        )

# SPAM PROTECT
@app.on_message(filters.text & filters.group)
async def spam_handler(client, message):

    text = message.text.lower()

    for word in SPAM:

        if word in text:

            await message.delete()

            await client.ban_chat_member(
                message.chat.id,
                message.from_user.id
            )

            await message.reply(
                f"{YAHUDA}\n\n🚫 Spam engellendi"
            )

            return

# FLOOD
@app.on_message(filters.text & filters.group)
async def flood_handler(client, message):

    uid = message.from_user.id
    now = time.time()

    if uid not in messages:
        messages[uid] = []

    messages[uid].append(now)

    messages[uid] = [t for t in messages[uid] if now - t <= FLOOD_TIME]

    if len(messages[uid]) >= FLOOD_LIMIT:

        await client.ban_chat_member(
            message.chat.id,
            uid
        )

        await message.reply(
            f"{YAHUDA}\n\n⚡ Flood engellendi"
        )

# COMMAND
@app.on_message(filters.command("yahuda"))
async def status(client, message):

    await message.reply(
        f"{YAHUDA}\n\n🛡️ GOD MODE aktif\n⭐ Koruma: 5/5"
    )

# MAIN FIX (PYTHON 3.14 SAFE)
async def main():

    print("『 ʏᴀʜᴜᴅᴀ 』 GOD MODE RENDER ACTIVE")

    await app.start()

    await asyncio.Event().wait()


if __name__ == "__main__":

    asyncio.run(main())
