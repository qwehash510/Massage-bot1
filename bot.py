import os
import logging
import asyncio
from datetime import datetime

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# =====================
# AYARLAR
# =====================

TOKEN = os.getenv("BOT_TOKEN")

OWNER_ID = 8464933639  # BURAYA KENDİ TELEGRAM ID YAZ

RESET_SECONDS = 86400  # 24 saat

scores = {}
start_time = datetime.now()

# =====================
# LOG
# =====================

logging.basicConfig(
    format="%(asctime)s - YAHUDA CORE - %(levelname)s - %(message)s",
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# =====================
# RESET SİSTEMİ
# =====================

async def auto_reset():

    global scores, start_time

    while True:

        await asyncio.sleep(RESET_SECONDS)

        scores = {}
        start_time = datetime.now()

        logger.info("YAHUDA CORE RESETLENDI")

# =====================
# START (SADECE OWNER)
# =====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != OWNER_ID:

        await update.message.reply_text(
            "⛔ YAHUDA CORE\nYetkisiz erişim."
        )
        return

    await update.message.reply_text(

        "╔══════════════════╗\n"
        "   YAHUDA CORE v7\n"
        "╚══════════════════╝\n\n"

        "⚡ Sistem Aktif\n"
        "⚡ Mesaj İzleme: AKTİF\n"
        "⚡ Skor Sistemi: AKTİF\n"
        "⚡ Reset: 24 Saat\n\n"

        "Hoşgeldin Efendim."

    )

# =====================
# MESAJ SAYMA
# =====================

async def count_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user
    name = user.first_name

    if name not in scores:
        scores[name] = 0

    scores[name] += 1

# =====================
# SKOR GÖSTER
# =====================

async def skor(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not scores:

        await update.message.reply_text(
            "YAHUDA CORE\nHenüz veri yok."
        )
        return

    text = "╔═══ YAHUDA SKOR ═══╗\n\n"

    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    for i, (name, score) in enumerate(sorted_scores[:10], 1):

        text += f"{i}. {name} » {score}\n"

    text += "\n╚══════════════════╝"

    await update.message.reply_text(text)

# =====================
# MAIN
# =====================

async def main():

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("skor", skor))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, count_message))

    asyncio.create_task(auto_reset())

    print("YAHUDA CORE ONLINE")

    await app.run_polling()

# =====================

if __name__ == "__main__":

    asyncio.run(main())
