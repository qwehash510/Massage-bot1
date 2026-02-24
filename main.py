import os
import asyncio
from pyrogram import Client, filters, idle
from pyrogram.types import Message
from pytgcalls import PyTgCalls
from pytgcalls.types.input_stream import AudioPiped
import yt_dlp

# WESTEROS SETTINGS
BOT_NAME = "🏰 WESTEROS MUSIC"

API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")

bot = Client(
    "westeros_music_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

call = PyTgCalls(bot)

queues = {}
playing = {}

# DOWNLOAD FUNCTION
def download(query):

    ydl_opts = {
        "format": "bestaudio",
        "outtmpl": "%(id)s.%(ext)s",
        "quiet": True,
        "noplaylist": True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:

        info = ydl.extract_info(f"ytsearch:{query}", download=True)

        file = ydl.prepare_filename(info["entries"][0])
        title = info["entries"][0]["title"]

        return file, title


# PLAY NEXT SONG
async def play_next(chat_id):

    if chat_id in queues and queues[chat_id]:

        file, title = queues[chat_id].pop(0)

        await call.change_stream(
            chat_id,
            AudioPiped(file)
        )

        playing[chat_id] = title


# START COMMAND
@bot.on_message(filters.command("start"))
async def start(_, message: Message):

    await message.reply(
f"""{BOT_NAME}

⚔️ Westeros krallığının resmi müzik botu

Komutlar:
/play şarkı
/skip
/pause
/resume
/stop
/queue
"""
)


# PLAY COMMAND
@bot.on_message(filters.command("play"))
async def play(_, message: Message):

    if len(message.command) < 2:
        return await message.reply("Kullanım: /play şarkı adı")

    chat_id = message.chat.id
    query = " ".join(message.command[1:])

    msg = await message.reply("🏰 Westeros müzik aranıyor...")

    file, title = download(query)

    if chat_id not in queues:
        queues[chat_id] = []

    if chat_id in playing:

        queues[chat_id].append((file, title))

        return await msg.edit(f"📜 Sıraya eklendi:\n{title}")

    await call.join_group_call(
        chat_id,
        AudioPiped(file)
    )

    playing[chat_id] = title

    await msg.edit(f"▶️ Çalıyor:\n{title}")


# SKIP
@bot.on_message(filters.command("skip"))
async def skip(_, message: Message):

    chat_id = message.chat.id

    if chat_id not in queues or not queues[chat_id]:
        return await message.reply("Sırada müzik yok")

    await play_next(chat_id)

    await message.reply("⏭️ Atlandı")


# PAUSE
@bot.on_message(filters.command("pause"))
async def pause(_, message: Message):

    await call.pause_stream(message.chat.id)

    await message.reply("⏸️ Duraklatıldı")


# RESUME
@bot.on_message(filters.command("resume"))
async def resume(_, message: Message):

    await call.resume_stream(message.chat.id)

    await message.reply("▶️ Devam ediyor")


# STOP
@bot.on_message(filters.command("stop"))
async def stop(_, message: Message):

    chat_id = message.chat.id

    queues[chat_id] = []
    playing.pop(chat_id, None)

    await call.leave_group_call(chat_id)

    await message.reply("⏹️ Durduruldu")


# QUEUE
@bot.on_message(filters.command("queue"))
async def queue(_, message: Message):

    chat_id = message.chat.id

    if chat_id not in queues or not queues[chat_id]:
        return await message.reply("Sıra boş")

    text = "📜 Sıra:\n\n"

    for i, (_, title) in enumerate(queues[chat_id]):
        text += f"{i+1}. {title}\n"

    await message.reply(text)


# MAIN
async def main():

    await bot.start()
    await call.start()

    print("🏰 WESTEROS MUSIC aktif")

    await idle()


if __name__ == "__main__":
    asyncio.run(main())
