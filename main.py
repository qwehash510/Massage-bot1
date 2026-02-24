import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ParseMode
import yt_dlp

from pytgcalls import PyTgCalls
from pytgcalls.types import Update
from pytgcalls.types.input_stream.stream import InputStream
from pytgcalls.types.input_stream.quality import HighQualityAudio

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Client("westeros_premium", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
pytgcall = PyTgCalls(bot)

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

def yt_search(query):
    opts = {"format": "bestaudio", "noplaylist": True, "quiet": True}
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(f"ytsearch:{query}", download=False)["entries"][0]
        return info["url"], info["title"], info["thumbnail"], info["duration"]

# ------------------------
@bot.on_message(filters.command("play") & filters.group)
async def play(_, message):
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
        # Yeni PyTgCalls v3 kullanımı
        await pytgcall.join_group_call(chat_id, InputStream(url, HighQualityAudio()))
        caption = f"👑 **WESTEROS MUSIC ULTRA**\n\n🎵 {title}\n⏱ {duration}s\n👤 {message.from_user.mention}"
        await msg.delete()
        await bot.send_photo(chat_id, photo=thumb, caption=caption, parse_mode=ParseMode.MARKDOWN, reply_markup=buttons())
    else:
        await msg.edit_text(f"📜 Sıraya eklendi: {title}\n📊 Sıra: {len(queues[chat_id])}")

# ------------------------
@bot.on_callback_query()
async def cb(_, query):
    chat_id = query.message.chat.id
    if query.data == "pause":
        await pytgcall.pause_stream(chat_id); await query.answer("⏸ Duraklatıldı")
    elif query.data == "resume":
        await pytgcall.resume_stream(chat_id); await query.answer("▶ Devam ediyor")
    elif query.data == "skip":
        if chat_id in queues and queues[chat_id]:
            queues[chat_id].pop(0)
            if queues[chat_id]:
                await pytgcall.join_group_call(chat_id, InputStream(queues[chat_id][0], HighQualityAudio()))
        await query.answer("⏭ Geçildi")
    elif query.data == "stop":
        queues[chat_id] = []
        await pytgcall.leave_group_call(chat_id)
        await query.answer("⏹ Durduruldu")

# ------------------------
@bot.on_message(filters.command("start"))
async def start(_, message):
    await message.reply_photo(
        photo="https://i.imgur.com/8B7QZ8G.jpeg",
        caption="👑 **WESTEROS MUSIC ULTRA**\nPremium, albüm kapaklı, butonlu, queue destekli ve hatasız müzik botu.\n/play şarkı adı ile başlatın.",
        parse_mode=ParseMode.MARKDOWN
    )

# ------------------------
async def main():
    await bot.start()
    await pytgcall.start()
    print("👑 WESTEROS ULTRA AKTİF")
    # idle yerine event ile beklet
    stop = asyncio.Event()
    await stop.wait()

asyncio.run(main())
