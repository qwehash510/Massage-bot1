import logging
import asyncio
import time
import re
import requests
from telethon import TelegramClient, events
from telethon.errors import PhoneCodeInvalidError, FloodWaitError

# --- AYARLAR ---
API_ID = 33188452
API_HASH = 'ac4afbd122081956a173b16590c02609'
BOT_TOKEN = '8700345149:AAEGWow2t1ig6kB_Z9FstDXYO7FJ_rG4g1M'

BOT_NAME = "VATİKAN ÜCRETSİZ SMS"
OWNERS = {8620961678}

client = TelegramClient('free_sms_v2', API_ID, API_HASH)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

active_numbers = {}  # {user_id: {"phone": str, "inbox_url": str}}

def get_best_free_number():
    """En kuralsız ücretsiz numara çekme - receive-smss + fallback"""
    sites = [
        "https://receive-smss.com/",
        "https://quackr.io/",
        "https://tempsmss.com/"
    ]
    for site in sites:
        try:
            r = requests.get(site, timeout=12, headers={"User-Agent": "Mozilla/5.0"})
            # Telefon numaralarını yakala (+country code format)
            phones = re.findall(r'(\+\d{8,15})', r.text)
            for phone in phones:
                if len(phone) > 10:  # Geçerli numara
                    inbox_url = f"https://receive-smss.com/sms/{phone.replace('+', '')}" if "receive-smss" in site else f"https://quackr.io/{phone.replace('+', '')}"
                    return phone, inbox_url
        except:
            continue
    return None, None

@client.on(events.NewMessage(pattern='/sms', chats=None))
async def get_free_number(event):
    if event.sender_id not in OWNERS or not event.is_private:
        return

    await event.respond("📱 **En iyi ücretsiz Telegram numarası aranıyor...**")

    phone, inbox_url = get_best_free_number()
    if not phone:
        await event.respond("❌ Şu anda uygun ücretsiz numara bulunamadı.\nBirkaç dakika sonra tekrar dene (/sms).")
        return

    # Telegram kontrolü (numarada aktif hesap var mı?)
    has_account = "Bilinmiyor"
    try:
        test = TelegramClient(f'test_{int(time.time())}', API_ID, API_HASH)
        await test.connect()
        await test.send_code_request(phone)
        has_account = "✅ Yeni hesap açılabilir"
    except Exception as e:
        if "already" in str(e).lower():
            has_account = "⚠️ Bu numarada hesap olabilir"
        else:
            has_account = "⚠️ Test edilemedi"
    finally:
        try:
            await test.disconnect()
        except:
            pass

    active_numbers[event.sender_id] = {"phone": phone, "inbox_url": inbox_url}

    await event.respond(
        f"✅ **Numara Hazır**\n"
        f"Numara: `{phone}`\n"
        f"Durum: {has_account}\n\n"
        f"Kod geldiğinde `/kod {phone}` yaz.\n"
        f"Bot otomatik inbox tarayacak ve kodu getirecek."
    )

@client.on(events.NewMessage(pattern='/kod', chats=None))
async def fetch_code(event):
    if event.sender_id not in OWNERS or not event.is_private:
        return

    try:
        phone = event.message.text.split(maxsplit=1)[1].strip()
    except:
        await event.respond("❗️ Kullanım: `/kod +905551234567`")
        return

    if event.sender_id not in active_numbers or active_numbers[event.sender_id]["phone"] != phone:
        await event.respond("❌ Bu numara için aktif işlem bulunamadı.")
        return

    inbox_url = active_numbers[event.sender_id]["inbox_url"]
    await event.respond("🔍 **Kod bekleniyor...** (her 5 saniyede taranıyor)")

    for attempt in range(36):  # ~3 dakika
        try:
            r = requests.get(inbox_url, timeout=10)
            # Telegram kodlarını yakala (genelde 5-7 haneli)
            code_match = re.search(r'(\d{5,7})', r.text)
            if code_match:
                code = code_match.group(1)
                await event.respond(
                    f"✅ **Kod Başarıyla Yakalandı!**\n"
                    f"Numara: `{phone}`\n"
                    f"**Kod:** `{code}`\n\n"
                    f"Telegram'a yapıştır ve yeni hesap aç."
                )
                if event.sender_id in active_numbers:
                    del active_numbers[event.sender_id]
                return
        except:
            pass

        await asyncio.sleep(5)

    await event.respond("⏳ Kod yakalanamadı. Numara süresi dolmuş olabilir.\nTekrar `/sms` yaz.")

async def main():
    await client.start(bot_token=BOT_TOKEN)
    print(f"🚀 {BOT_NAME} çalışıyor... En kuralsız ücretsiz SMS + otomatik kod yakalama modu aktif")
    await client.run_until_disconnected()

asyncio.run(main())
