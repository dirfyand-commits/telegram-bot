# ============================================================
# scheduler.py - Sistem Pengingat + Reset Jadwal Tiap Hari
# ============================================================

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from database import ambil_semua_user, reset_status_harian
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from datetime import datetime, timezone, timedelta
import pytz

WIB = timezone(timedelta(hours=7))
TIMEZONE = pytz.utc

scheduler = AsyncIOScheduler(timezone=TIMEZONE)

def init_scheduler(app):
    # Cek jadwal setiap menit
    scheduler.add_job(
        func=cek_dan_kirim,
        args=[app],
        trigger=CronTrigger(second=0),
        id="cek_jadwal",
        replace_existing=True
    )

    # Reset status jadwal setiap tengah malam WIB (17:00 UTC)
    scheduler.add_job(
        func=reset_harian,
        args=[app],
        trigger=CronTrigger(hour=17, minute=0),  # 00:00 WIB = 17:00 UTC
        id="reset_harian",
        replace_existing=True
    )

    scheduler.start()
    print("✅ Scheduler berhasil dijalankan!")


async def cek_dan_kirim(app):
    sekarang = datetime.now(WIB)
    jam_sekarang = sekarang.strftime("%H:%M")

    for user_id, jadwal_list in ambil_semua_user():
        for item in jadwal_list:
            if item["jam"] == jam_sekarang:
                try:
                    from bot import JADWAL_WORKOUT, HARI_ID
                    hari = HARI_ID[sekarang.weekday()]
                    workout = JADWAL_WORKOUT.get(hari, "-")

                    keyboard = InlineKeyboardMarkup([
                        [
                            InlineKeyboardButton("✅ Sudah", callback_data=f"sudah:{item['jam']}"),
                            InlineKeyboardButton("❌ Belum", callback_data=f"belum:{item['jam']}"),
                        ]
                    ])

                    pesan = (
                        f"⏰ *Pengingat Jadwal*\n\n"
                        f"📅 *{hari}* — {sekarang.strftime('%H:%M WIB')}\n"
                        f"🏋️ Workout: {workout}\n\n"
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


async def reset_harian(app):
    """Reset status jadwal semua user setiap tengah malam WIB"""
    sekarang = datetime.now(WIB)
    hari = ["Senin","Selasa","Rabu","Kamis","Jumat","Sabtu","Minggu"][sekarang.weekday()]

    print(f"🔄 Reset jadwal harian — {hari} {sekarang.strftime('%d/%m/%Y')}")

    reset_status_harian()

    # Kirim notif ke semua user
    for user_id, jadwal_list in ambil_semua_user():
        if jadwal_list:
            try:
                from bot import JADWAL_WORKOUT
                workout = JADWAL_WORKOUT.get(hari, "-")

                await app.bot.send_message(
                    chat_id=int(user_id),
                    text=(
                        f"🌅 *Selamat Pagi! Hari Baru Dimulai!*\n\n"
                        f"📅 *{hari}*, {sekarang.strftime('%d/%m/%Y')}\n"
                        f"🏋️ Workout hari ini: *{workout}*\n\n"
                        f"✨ Jadwal harianmu sudah direset.\n"
                        f"Ketik /jadwal untuk melihat jadwal hari ini.\n\n"
                        f"Semangat menjalani hari! 💪🔥"
                    ),
                    parse_mode="Markdown"
                )
            except Exception as e:
                print(f"❌ Gagal kirim reset notif ke {user_id}: {e}")


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown()

