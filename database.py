# ============================================================
# database.py - Penyimpanan Jadwal + EXP + Streak
# ============================================================

import json
import os
from datetime import datetime, timezone, timedelta

DB_PATH = "data/jadwal.json"
WIB = timezone(timedelta(hours=7))

def init_db():
    os.makedirs("data", exist_ok=True)
    if not os.path.exists(DB_PATH):
        with open(DB_PATH, "w") as f:
            json.dump({}, f)
    print("✅ Database berhasil diinisialisasi.")

def baca_db():
    try:
        with open(DB_PATH, "r") as f:
            return json.load(f)
    except:
        return {}

def tulis_db(data):
    os.makedirs("data", exist_ok=True)
    with open(DB_PATH, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def simpan_jadwal(user_id, jadwal_list):
    db = baca_db()
    uid = str(user_id)
    # Pertahankan data exp & streak jika sudah ada
    exp = db.get(uid, {}).get("exp", 0)
    streak = db.get(uid, {}).get("streak", 0)
    last_active = db.get(uid, {}).get("last_active", "")

    for item in jadwal_list:
        item["status"] = "belum"

    db[uid] = {
        "jadwal": jadwal_list,
        "exp": exp,
        "streak": streak,
        "last_active": last_active
    }
    tulis_db(db)

def ambil_jadwal(user_id):
    db = baca_db()
    data = db.get(str(user_id), {})
    if isinstance(data, list):
        return data
    return data.get("jadwal", [])

def hapus_jadwal(user_id):
    db = baca_db()
    uid = str(user_id)
    if uid in db:
        # Reset jadwal tapi pertahankan exp & streak
        db[uid]["jadwal"] = []
        tulis_db(db)

def ambil_semua_user():
    db = baca_db()
    result = []
    for uid, data in db.items():
        if isinstance(data, list):
            result.append((uid, data))
        else:
            result.append((uid, data.get("jadwal", [])))
    return result

def update_status(user_id, jam, status):
    db = baca_db()
    uid = str(user_id)
    if uid not in db:
        return False

    data = db[uid]
    jadwal = data.get("jadwal", data) if isinstance(data, dict) else data

    for item in jadwal:
        if item["jam"] == jam:
            item["status"] = status
            if isinstance(data, dict):
                db[uid]["jadwal"] = jadwal
            tulis_db(db)
            return True
    return False

def ambil_kegiatan_by_jam(user_id, jam):
    jadwal = ambil_jadwal(user_id)
    for item in jadwal:
        if item["jam"] == jam:
            return item
    return None

# ════════════════════════════════════════════
# EXP SYSTEM
# ════════════════════════════════════════════

EXP_PER_KEGIATAN = 20

def get_level(exp):
    """Hitung level berdasarkan EXP"""
    level = 1
    threshold = 100
    while exp >= threshold:
        exp -= threshold
        level += 1
        threshold = int(threshold * 1.5)
    return level, exp, threshold

def tambah_exp(user_id):
    """Tambah EXP saat kegiatan selesai"""
    db = baca_db()
    uid = str(user_id)
    if uid not in db or isinstance(db[uid], list):
        return 0, 1

    db[uid]["exp"] = db[uid].get("exp", 0) + EXP_PER_KEGIATAN
    tulis_db(db)
    return db[uid]["exp"], get_level(db[uid]["exp"])[0]

def ambil_exp(user_id):
    db = baca_db()
    data = db.get(str(user_id), {})
    if isinstance(data, dict):
        return data.get("exp", 0)
    return 0

# ════════════════════════════════════════════
# STREAK SYSTEM
# ════════════════════════════════════════════

def update_streak(user_id):
    """Update streak harian user"""
    db = baca_db()
    uid = str(user_id)
    if uid not in db or isinstance(db[uid], list):
        return 1

    hari_ini = datetime.now(WIB).strftime("%Y-%m-%d")
    last_active = db[uid].get("last_active", "")
    streak = db[uid].get("streak", 0)

    if last_active == hari_ini:
        # Sudah aktif hari ini, tidak perlu update
        return streak
    
    # Cek apakah kemarin aktif (streak berlanjut)
    kemarin = (datetime.now(WIB) - timedelta(days=1)).strftime("%Y-%m-%d")
    if last_active == kemarin:
        streak += 1
    else:
        streak = 1  # Reset streak

    db[uid]["streak"] = streak
    db[uid]["last_active"] = hari_ini
    tulis_db(db)
    return streak

def ambil_streak(user_id):
    db = baca_db()
    data = db.get(str(user_id), {})
    if isinstance(data, dict):
        return data.get("streak", 0)
    return 0

def ambil_last_active(user_id):
    db = baca_db()
    data = db.get(str(user_id), {})
    if isinstance(data, dict):
        return data.get("last_active", "-")
    return "-"

# ════════════════════════════════════════════
# RESET STATUS HARIAN
# ════════════════════════════════════════════

def reset_status_harian():
    """Reset semua status jadwal jadi 'belum' setiap hari baru"""
    db = baca_db()
    for uid in db:
        data = db[uid]
        if isinstance(data, dict):
            for item in data.get("jadwal", []):
                item["status"] = "belum"
        elif isinstance(data, list):
            for item in data:
                item["status"] = "belum"
    tulis_db(db)
    print("✅ Status jadwal semua user berhasil direset.")

