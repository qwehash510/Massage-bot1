import os, time, asyncio, random, string, logging
from pyrogram import Client, filters
from pyrogram.types import ChatPermissions
from dotenv import load_dotenv

load_dotenv()

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(level=logging.INFO)

# FONT & STYLING
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
    "yahuda_ultra_god",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    workers=200
)

# DATABASE
joins = {}
captcha_db = {}
messages = {}
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

SPAM = ["http","t.me/","discord.gg","@"]

# GENERATE CAPTCHA
def gen_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

# LOCK & UNLOCK
async def lock_group(chat):
    if chat in locked: return
    locked.add(chat)
    await app.set_chat_permissions(chat, ChatPermissions())
    await app.send_message(chat, f"{YAHUDA}\n\n{EMOJI['raid']} Raid algılandı\n{EMOJI['lock']} Grup kilitlendi\n{EMOJI['shield']} GOD MODE aktif")

async def unlock_group(chat):
    if chat not in locked: return
    locked.remove(chat)
    await app.set_chat_permissions(chat, ChatPermissions(
        can_send_messages=True,
        can_send_media_messages=True,
        can_send_other_messages=True
    ))
    await app.send_message(chat, f"{YAHUDA}\n\n{EMOJI['unlock']} Grup tekrar açıldı\n{EMOJI['shield']} Sistem stabil")

# RAID DETECT + CAPTCHA + BOT PROTECT
@app.on_message(filters.new_chat_members)
async def raid(client, message):
    chat = message.chat.id
    now = time.time()

    if chat not in joins: joins[chat]=[]
    joins[chat].append(now)
    joins[chat] = [t for t in joins[chat] if now-t <= JOIN_TIME]

    for user in message.new_chat_members:
        if user.id in global_ban or user.is_bot:
            await client.ban_chat_member(chat, user.id)
            return

    if len(joins[chat]) >= JOIN_LIMIT:
        await lock_group(chat)
        for user in message.new_chat_members:
            try:
                await client.ban_chat_member(chat, user.id)
                global_ban.add(user.id)
            except: pass
        await asyncio.sleep(LOCK_TIME)
        await unlock_group(chat)
        return

    for user in message.new_chat_members:
        code = gen_code()
        captcha_db[user.id]={"code":code,"chat":chat,"time":now}
        await message.reply(f"{YAHUDA}\n\n👤 {user.mention}\n{EMOJI['captcha']} Doğrulama kodu: `{code}`\n⏱ 60 saniye")

# CAPTCHA VERIFY
@app.on_message(filters.text & filters.group)
async def captcha_verify(client,message):
    uid=message.from_user.id
    if uid not in captcha_db: return
    data = captcha_db[uid]

    if time.time()-data["time"] > CAPTCHA_TIMEOUT:
        await client.ban_chat_member(data["chat"],uid)
        global_ban.add(uid)
        del captcha_db[uid]
        await message.reply(f"{YAHUDA}\n\n❌ Doğrulama başarısız\n🚫 Banlandı")
        return

    if message.text == data["code"]:
        del captcha_db[uid]
        await message.reply(f"{YAHUDA}\n\n✅ Doğrulama başarılı\n🛡️ Hoşgeldin")

# SPAM
@app.on_message(filters.text & filters.group)
async def spam(client,message):
    uid=message.from_user.id
    if uid in whitelist: return
    text=message.text.lower()
    for word in SPAM:
        if word in text:
            await message.delete()
            await client.ban_chat_member(message.chat.id,uid)
            global_ban.add(uid)
            await message.reply(f"{YAHUDA}\n\n{EMOJI['spam']} Spam tespit edildi\n⚔️ Kullanıcı banlandı")
            return

# FLOOD
@app.on_message(filters.text & filters.group)
async def flood(client,message):
    uid=message.from_user.id
    now=time.time()
    if uid not in messages: messages[uid]=[]
    messages[uid].append(now)
    messages[uid] = [t for t in messages[uid] if now-t <= FLOOD_TIME]
    if len(messages[uid]) >= FLOOD_LIMIT:
        await client.ban_chat_member(message.chat.id,uid)
        global_ban.add(uid)
        await message.reply(f"{YAHUDA}\n\n{EMOJI['flood']} Flood saldırısı engellendi")

# COMMANDS
@app.on_message(filters.command("yahuda"))
async def status(client,message):
    await message.reply(f"{YAHUDA}\n\n🛡️ GOD MODE ULTRA v7 aktif\n⭐ Tüm sistemler maksimum\n🚀 Koruma seviyesi: 5/5")

@app.on_message(filters.command("kilit"))
async def cmd_lock(client,message):
    await lock_group(message.chat.id)

@app.on_message(filters.command("ac"))
async def cmd_unlock(client,message):
    await unlock_group(message.chat.id)

print("『 ʏᴀʜᴜᴅᴀ 』 ULTRA GOD MODE v7 ACTIVE")
app.run()
