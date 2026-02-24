import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ParseMode
from pyrogram.idle import idle

from pytgcalls import PyTgCalls
from pytgcalls.types.input_stream import InputAudioStream
from pytgcalls.types.input_stream.quality import HighQualityAudio

import yt_dlp

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Client(
    "WESTEROS_ULTRA",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

call = PyTgCalls(bot)

# --------------------------
# Queue ve veri yapıları
queues = {}

def buttons():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("⏸ Pause", callback_data="pause"),
            InlineKeyboardButton("▶ Resume", callback_data="resume"),
            InlineKeyboardButton("⏭ Skip", callback_data="skip"),
            InlineKeyboardButton("⏹ Stop", callback_data="stop")
        ]
    ])

# --------------------------
# YouTube arama fonksiyonu
def yt_search(query):
    ydl_opts = {"format": "bestaudio", "noplaylist": True, "quiet": True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(f"ytsearch:{query}", download=False)["entries"][0]
        return info["url"], info["title"], info["thumbnail"], info["duration"]

# --------------------------
# /play komutu
@bot.on_message(filters.command("play") & filters.group)
async def play(_, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("❌ /play şarkı adı yazın")
    query = " ".join(message.command[1:])
    msg = await message.reply_text("🔍 WESTEROS arıyor...")
    url, title, thumb, duration = yt_search(query)
    chat_id = message.chat.id

    if chat_id not in queues:
        queues[chat_id] = []

    queues[chat_id].append(url)

    if len(queues[chat_id]) == 1:
        await call.join_group_call(chat_id, InputAudioStream(url, HighQualityAudio()))
        caption = f"👑 **WESTEROS MUSIC ULTRA**\n\n🎵 {title}\n⏱ {duration}s\n👤 {message.from_user.mention}"
        await msg.delete()
        await bot.send_photo(chat_id, photo=thumb, caption=caption, parse_mode=ParseMode.MARKDOWN, reply_markup=buttons())
    else:
        await msg.edit_text(f"📜 Sıraya eklendi: {title}\n📊 Sıra: {len(queues[chat_id])}")

# --------------------------
# Callback butonları
@bot.on_callback_query()
async def callbacks(_, query):
    chat_id = query.message.chat.id
    if query.data == "pause":
        await call.pause_stream(chat_id); await query.answer("⏸ Duraklatıldı")
    elif query.data == "resume":
        await call.resume_stream(chat_id); await query.answer("▶ Devam ediyor")
    elif query.data == "skip":
        if chat_id in queues and queues[chat_id]:
            queues[chat_id].pop(0)
            if queues[chat_id]:
                await call.join_group_call(chat_id, InputAudioStream(queues[chat_id][0], HighQualityAudio()))
        await query.answer("⏭ Geçildi")
    elif query.data == "stop":
        queues[chat_id] = []
        await call.leave_group_call(chat_id)
        await query.answer("⏹ Durduruldu")

# --------------------------
# /start komutu
@bot.on_message(filters.command("start"))
async def start(_, message: Message):
    await message.reply_photo(
        photo="https://i.imgur.com/8B7QZ8G.jpeg",
        caption="👑 **WESTEROS MUSIC ULTRA**\n\nPremium, albüm kapaklı, butonlu, queue destekli ve hatasız müzik botu.\n\nKomutlar:\n/play şarkı adı\nButonlarla kontrol",
        parse_mode=ParseMode.MARKDOWN
    )

# --------------------------
# Botu başlat
async def main():
    await bot.start()
    await call.start()
    print("👑 WESTEROS ULTRA AKTİF")
    await idle()

asyncio.run(main())
