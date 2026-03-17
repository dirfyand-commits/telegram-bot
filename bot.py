# ============================================================
# bot.py - Bot Telegram Pengingat Jadwal Produktif
# Dibuat oleh: NellStore
# ============================================================

import os
import random
import logging
from datetime import datetime, timezone, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes
)
from database import (
    init_db, simpan_jadwal, ambil_jadwal, hapus_jadwal,
    update_status, ambil_kegiatan_by_jam,
    tambah_exp, ambil_exp, get_level,
    update_streak, ambil_streak, ambil_last_active
)
from parser import parse_jadwal, format_jadwal_tampil
from scheduler import init_scheduler

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)
BOT_TOKEN = os.environ.get("8642003715:AAGvUd8fSWv7mZQOuLhpaH8EDZnMZDnyoA0", "")

# ── Timezone WIB ─────────────────────────────────────────────
WIB = timezone(timedelta(hours=7))

# ── Motivasi ─────────────────────────────────────────────────
MOTIVASI = [
    "💪 Kamu pasti bisa! Semangat terus!",
    "🔥 Jangan menyerah, setiap langkah kecil itu berarti!",
    "⭐ Konsistensi adalah kunci kesuksesan!",
    "🚀 Mulai sekarang lebih baik daripada tidak sama sekali!",
    "🌟 Kamu lebih kuat dari yang kamu kira!",
    "💡 Fokus pada prosesnya, hasil akan mengikuti!",
    "🎯 Satu langkah hari ini, seribu langkah esok hari!",
    "🏆 Orang sukses melakukan hal yang tidak ingin dilakukan orang gagal!",
]

# ── Jadwal Workout Kizzy ─────────────────────────────────────
JADWAL_WORKOUT = {
    "Senin":    "💪 Chest, Triceps, Shoulders",
    "Selasa":   "💪 Biceps, Back, Traps",
    "Rabu":     "🦵 Leg Day, Abs",
    "Kamis":    "💪 Chest, Triceps, Shoulders",
    "Jumat":    "💪 Biceps, Back, Traps",
    "Sabtu":    "🦵 Leg Day, Abs",
    "Minggu":   "😴 Rest / Arm Day",
}

HARI_ID = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]

menunggu_jadwal = set()

# ── Tanggal mulai workout (ubah sesuai hari pertama kamu mulai) ──
TANGGAL_MULAI_WORKOUT = datetime(2026, 3, 17, tzinfo=WIB)

def get_hari_sekarang():
    now = datetime.now(WIB)
    return HARI_ID[now.weekday()]

def get_hari_ke():
    now = datetime.now(WIB)
    delta = (now - TANGGAL_MULAI_WORKOUT).days + 1
    return max(1, delta)

def badge_level(level):
    if level >= 10: return "👑 Legend"
    if level >= 7: return "💎 Master"
    if level >= 5: return "🥇 Expert"
    if level >= 3: return "🥈 Intermediate"
    return "🥉 Beginner"


# ════════════════════════════════════════════
# COMMAND /start
# ════════════════════════════════════════════

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    nama = update.effective_user.first_name
    menunggu_jadwal.add(user_id)

    hari = get_hari_sekarang()
    workout = JADWAL_WORKOUT.get(hari, "-")
    hari_ke = get_hari_ke()
    now = datetime.now(WIB).strftime("%d/%m/%Y %H:%M WIB")

    pesan = (
        f"Halo, *{nama}*! 👋\n"
        f"Aku adalah bot pengingat jadwal produktif.\n\n"
        f"📅 *Hari ini:* {hari} — Hari ke-*{hari_ke}*\n"
        f"🕐 *Waktu:* {now}\n"
        f"🏋️ *Workout hari ini:* {workout}\n\n"
        f"Silakan kirim jadwal harian kamu:\n\n"
        f"`07:00 Bangun pagi`\n"
        f"`08:00 Belajar coding`\n"
        f"`12:00 Istirahat makan siang`\n"
        f"`20:00 Review hari`\n\n"
        f"📌 Kirim semua jadwal dalam *satu pesan*.\n"
        f"💡 Setiap kegiatan selesai = *+20 EXP* 🎮"
    )
    await update.message.reply_text(pesan, parse_mode="Markdown")


# ════════════════════════════════════════════
# COMMAND /workout
# ════════════════════════════════════════════

async def cmd_workout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    hari_ke = get_hari_ke()
    hari = get_hari_sekarang()
    now = datetime.now(WIB).strftime("%d/%m/%Y %H:%M WIB")

    teks = (
        f"🏋️ *Jadwal Workout Kizzy*\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"📅 Hari ini: *{hari}* (Hari ke-*{hari_ke}*)\n"
        f"🕐 Waktu: {now}\n\n"
    )

    for hari_nama, latihan in JADWAL_WORKOUT.items():
        ikon = "▶️" if hari_nama == hari else "▪️"
        teks += f"{ikon} *{hari_nama}:* {latihan}\n"

    teks += f"\n━━━━━━━━━━━━━━━━━━\n"
    teks += f"💪 *Workout hari ini:* {JADWAL_WORKOUT.get(hari, '-')}\n"
    teks += f"_Semangat latihan!_ 🔥"

    await update.message.reply_text(teks, parse_mode="Markdown")


# ════════════════════════════════════════════
# COMMAND /hari
# ════════════════════════════════════════════

async def cmd_hari(update: Update, context: ContextTypes.DEFAULT_TYPE):
    hari_ke = get_hari_ke()
    hari = get_hari_sekarang()
    now = datetime.now(WIB)
    tanggal = now.strftime("%A, %d %B %Y")
    waktu = now.strftime("%H:%M:%S WIB")
    workout = JADWAL_WORKOUT.get(hari, "-")

    # Hitung progress minggu
    hari_index = now.weekday() + 1
    progress = "█" * hari_index + "░" * (7 - hari_index)

    pesan = (
        f"📅 *Info Hari*\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"🗓️ Tanggal : {tanggal}\n"
        f"🕐 Waktu   : {waktu}\n"
        f"📍 Zona    : WIB (UTC+7)\n\n"
        f"📊 *Progress Minggu Ini:*\n"
        f"`{progress}` {hari_index}/7\n\n"
        f"🏋️ *Hari ke-{hari_ke} workout*\n"
        f"💪 Latihan : {workout}\n\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"_Tetap konsisten setiap hari!_ 🔥"
    )
    await update.message.reply_text(pesan, parse_mode="Markdown")


# ════════════════════════════════════════════
# COMMAND /jadwal
# ════════════════════════════════════════════

async def cmd_jadwal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    jadwal = ambil_jadwal(user_id)

    if not jadwal:
        await update.message.reply_text("❌ Belum ada jadwal. Ketik /start untuk input jadwal.")
        return

    hari = get_hari_sekarang()
    now = datetime.now(WIB).strftime("%H:%M WIB")

    teks = f"📅 *Jadwal Harian — {hari}*\n"
    teks += f"🕐 {now}\n"
    teks += "━━━━━━━━━━━━━━━━━━\n"
    sudah = 0
    for item in jadwal:
        status = item.get("status", "belum")
        ikon = "✅" if status == "sudah" else "⏳"
        if status == "sudah": sudah += 1
        teks += f"{ikon} `{item['jam']}` — {item['kegiatan']}\n"

    total = len(jadwal)
    persen = int((sudah / total) * 100) if total > 0 else 0
    progress = "█" * (persen // 10) + "░" * (10 - persen // 10)

    teks += f"━━━━━━━━━━━━━━━━━━\n"
    teks += f"📊 Progress: `{progress}` {persen}%\n"
    teks += f"✅ Selesai: {sudah}/{total} kegiatan"

    await update.message.reply_text(teks, parse_mode="Markdown")


# ════════════════════════════════════════════
# COMMAND /profil
# ════════════════════════════════════════════

async def cmd_profil(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    nama = update.effective_user.first_name

    exp = ambil_exp(user_id)
    streak = ambil_streak(user_id)
    last_active = ambil_last_active(user_id)
    level, exp_sekarang, exp_needed = get_level(exp)
    badge = badge_level(level)
    hari_ke = get_hari_ke()

    exp_bar = "█" * min(10, int((exp_sekarang / exp_needed) * 10))
    exp_bar += "░" * (10 - len(exp_bar))

    pesan = (
        f"👤 *Profil {nama}*\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"🏅 Badge   : {badge}\n"
        f"⭐ Level   : {level}\n"
        f"✨ EXP     : {exp_sekarang}/{exp_needed}\n"
        f"📈 Progress: `{exp_bar}`\n\n"
        f"🔥 Streak  : {streak} hari berturut-turut\n"
        f"🏋️ Hari ke : {hari_ke} workout\n"
        f"📅 Terakhir aktif: {last_active}\n\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"_Selesaikan kegiatan untuk dapat EXP!_ 💪"
    )
    await update.message.reply_text(pesan, parse_mode="Markdown")


# ════════════════════════════════════════════
# COMMAND /reset
# ════════════════════════════════════════════

async def cmd_reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    hapus_jadwal(user_id)
    menunggu_jadwal.add(user_id)
    await update.message.reply_text(
        "🗑️ *Jadwal berhasil direset!*\n\nKirim jadwal baru kamu sekarang. 📝",
        parse_mode="Markdown"
    )


# ════════════════════════════════════════════
# COMMAND /help
# ════════════════════════════════════════════

async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pesan = (
        f"📋 *Panduan Bot Pengingat Jadwal*\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"▸ /start — 🚀 Mulai & input jadwal\n"
        f"▸ /jadwal — 📅 Lihat jadwal + progress\n"
        f"▸ /workout — 🏋️ Jadwal workout mingguan\n"
        f"▸ /hari — 📅 Info hari + waktu WIB\n"
        f"▸ /profil — 🏅 Lihat EXP, level & streak\n"
        f"▸ /reset — 🗑️ Reset jadwal\n"
        f"▸ /help — ❓ Bantuan\n\n"
        f"*Sistem EXP:*\n"
        f"✅ Selesai kegiatan = +20 EXP\n"
        f"🔥 Aktif tiap hari = streak bertambah\n\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"_Bot by NellStore_"
    )
    await update.message.reply_text(pesan, parse_mode="Markdown")


# ════════════════════════════════════════════
# HANDLER PESAN
# ════════════════════════════════════════════

async def handler_pesan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    teks = update.message.text

    if user_id not in menunggu_jadwal:
        await update.message.reply_text(
            "Ketik /start untuk memulai atau /help untuk bantuan. 😊"
        )
        return

    jadwal_list = parse_jadwal(teks)

    if not jadwal_list:
        await update.message.reply_text(
            "❌ *Format tidak valid!*\n\nGunakan format:\n`07:00 Bangun pagi`\n\nCoba lagi. 📝",
            parse_mode="Markdown"
        )
        return

    simpan_jadwal(user_id, jadwal_list)
    menunggu_jadwal.discard(user_id)

    tampilan = format_jadwal_tampil(jadwal_list)
    pesan = (
        f"✅ *Jadwal berhasil disimpan!*\n\n"
        f"{tampilan}\n\n"
        f"🔔 Pengingat otomatis aktif!\n"
        f"💡 Setiap kegiatan selesai = *+20 EXP* 🎮"
    )
    await update.message.reply_text(pesan, parse_mode="Markdown")


# ════════════════════════════════════════════
# HANDLER TOMBOL
# ════════════════════════════════════════════

async def handler_tombol(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    user_id = query.from_user.id
    nama = query.from_user.first_name

    parts = data.split(":", 1)
    if len(parts) != 2:
        return

    aksi, jam = parts
    kegiatan = ambil_kegiatan_by_jam(user_id, jam)

    if not kegiatan:
        await query.edit_message_text("❌ Kegiatan tidak ditemukan.")
        return

    if aksi == "sudah":
        update_status(user_id, jam, "sudah")
        total_exp, level = tambah_exp(user_id)
        streak = update_streak(user_id)
        _, exp_now, exp_needed = get_level(total_exp)
        badge = badge_level(level)

        await query.edit_message_text(
            f"✅ *Keren, {nama}!*\n\n"
            f"Kamu sudah menyelesaikan:\n"
            f"📌 *{kegiatan['kegiatan']}* pukul `{jam}`\n\n"
            f"🎮 *+20 EXP* didapat!\n"
            f"⭐ Level: {level} {badge}\n"
            f"✨ EXP: {exp_now}/{exp_needed}\n"
            f"🔥 Streak: {streak} hari\n\n"
            f"Pertahankan semangat ini! 💪",
            parse_mode="Markdown"
        )

    elif aksi == "belum":
        update_status(user_id, jam, "belum")
        motivasi = random.choice(MOTIVASI)

        await query.edit_message_text(
            f"⏳ *Belum dikerjakan*\n\n"
            f"📌 *{kegiatan['kegiatan']}* pukul `{jam}`\n\n"
            f"{motivasi}\n\n"
            f"_Masih ada kesempatan untuk menyelesaikannya!_ 🙏",
            parse_mode="Markdown"
        )


# ════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════

def main():
    init_db()

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("jadwal", cmd_jadwal))
    app.add_handler(CommandHandler("workout", cmd_workout))
    app.add_handler(CommandHandler("hari", cmd_hari))
    app.add_handler(CommandHandler("profil", cmd_profil))
    app.add_handler(CommandHandler("reset", cmd_reset))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handler_pesan))
    app.add_handler(CallbackQueryHandler(handler_tombol))

    async def post_init(application):
        init_scheduler(application)

    app.post_init = post_init

    print("🤖 Bot Pengingat Jadwal siap dijalankan!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()

