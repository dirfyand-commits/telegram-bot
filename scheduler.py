# ============================================================
# scheduler.py - Sistem Pengingat Jadwal Otomatis
# ============================================================

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from database import ambil_semua_user
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from datetime import datetime
import pytz

TIMEZONE = pytz.utc

scheduler = AsyncIOScheduler(timezone=TIMEZONE)

def init_scheduler(app):
    scheduler.add_job(
        func=cek_dan_kirim,
        args=[app],
        trigger=CronTrigger(second=0),
        id="cek_jadwal",
        replace_existing=True
    )
    scheduler.start()
    print("✅ Scheduler berhasil dijalankan!")


async def cek_dan_kirim(app):
    # WIB = UTC+7
    from datetime import timezone, timedelta
    wib = timezone(timedelta(hours=7))
    sekarang = datetime.now(wib)
    jam_sekarang = sekarang.strftime("%H:%M")

    for user_id, jadwal_list in ambil_semua_user():
        for item in jadwal_list:
            if item["jam"] == jam_sekarang:
                try:
                    # Buat tombol Sudah dan Belum
                    keyboard = InlineKeyboardMarkup([
                        [
                            InlineKeyboardButton("✅ Sudah", callback_data=f"sudah:{item['jam']}"),
                            InlineKeyboardButton("❌ Belum", callback_data=f"belum:{item['jam']}"),
                        ]
                    ])

                    pesan = (
                        f"⏰ *Pengingat Jadwal*\n\n"
                        f"Sekarang waktunya:\n"
                        f"📌 *{item['kegiatan']}*\n\n"
                        f"Apakah sudah dikerjakan?"
                    )

                    await app.bot.send_message(
                        chat_id=int(user_id),
                        text=pesan,
                        parse_mode="Markdown",
                        reply_markup=keyboard
                    )
                    print(f"✅ Pengingat dikirim ke {user_id}: {item['kegiatan']}")
                except Exception as e:
                    print(f"❌ Gagal kirim ke {user_id}: {e}")


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown()

