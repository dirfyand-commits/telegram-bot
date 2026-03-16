# ============================================================
# parser.py - Membaca Format Jadwal dari Pesan User
# ============================================================

import re

def parse_jadwal(teks):
    """
    Membaca pesan jadwal dari user dengan format:
    JAM KEGIATAN
    
    Contoh:
    07:00 Bangun pagi
    08:00 Belajar coding
    20:00 Olahraga
    
    Return: list of dict [{"jam": "07:00", "kegiatan": "Bangun pagi"}, ...]
    """
    hasil = []
    baris_list = teks.strip().split("\n")

    for baris in baris_list:
        baris = baris.strip()
        if not baris:
            continue

        # Cari pola jam HH:MM di awal baris
        match = re.match(r"^(\d{1,2}:\d{2})\s+(.+)$", baris)
        if match:
            jam = match.group(1)
            kegiatan = match.group(2).strip()

            # Validasi format jam
            try:
                jam_parts = jam.split(":")
                hour = int(jam_parts[0])
                minute = int(jam_parts[1])
                if 0 <= hour <= 23 and 0 <= minute <= 59:
                    # Normalisasi jam jadi HH:MM
                    jam_normal = f"{hour:02d}:{minute:02d}"
                    hasil.append({
                        "jam": jam_normal,
                        "kegiatan": kegiatan
                    })
            except:
                continue

    # Urutkan berdasarkan jam
    hasil.sort(key=lambda x: x["jam"])
    return hasil


def format_jadwal_tampil(jadwal_list):
    """
    Format jadwal untuk ditampilkan ke user
    """
    if not jadwal_list:
        return "❌ Belum ada jadwal tersimpan."

    teks = "📅 *Jadwal Harian Kamu:*\n"
    teks += "━━━━━━━━━━━━━━━━━━\n"
    for item in jadwal_list:
        teks += f"⏰ `{item['jam']}` — {item['kegiatan']}\n"
    teks += "━━━━━━━━━━━━━━━━━━"
    return teks

