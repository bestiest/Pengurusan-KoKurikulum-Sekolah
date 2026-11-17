import sqlite3
import os
from pathlib import Path

BASE_DIR = Path("C:/Antigravity/Sistem Pengurusan Unit Kokurikulum")
DB_PATH = BASE_DIR / "data" / "kokurikulum.db"

conn = sqlite3.connect(str(DB_PATH))
cursor = conn.cursor()

# 1. Add columns to permission_letters if missing
pl_cols = [r[1] for r in cursor.execute("PRAGMA table_info(permission_letters)").fetchall()]
if "participation_level" not in pl_cols:
    print("Adding participation_level to permission_letters...")
    cursor.execute("ALTER TABLE permission_letters ADD COLUMN participation_level TEXT DEFAULT 'Daerah'")
if "activity_category" not in pl_cols:
    print("Adding activity_category to permission_letters...")
    cursor.execute("ALTER TABLE permission_letters ADD COLUMN activity_category TEXT DEFAULT 'Sukan & Permainan'")
if "represented_org_id" not in pl_cols:
    print("Adding represented_org_id to permission_letters...")
    cursor.execute("ALTER TABLE permission_letters ADD COLUMN represented_org_id INTEGER NULL")

# 2. Add permission_letter_id to external_participations if missing
ep_cols = [r[1] for r in cursor.execute("PRAGMA table_info(external_participations)").fetchall()]
if "permission_letter_id" not in ep_cols:
    print("Adding permission_letter_id to external_participations...")
    cursor.execute("ALTER TABLE external_participations ADD COLUMN permission_letter_id INTEGER NULL")

# 3. Synchronize existing permission letters to external_participations
letters = cursor.execute("SELECT * FROM permission_letters").fetchall()
col_names = [d[0] for d in cursor.description]

def get_pajsk_score(level, achievement, role="Peserta"):
    matrix = {
        "Antarabangsa": { "Johan": 20.0, "Naib Johan": 20.0, "Tempat Ketiga": 19.0, "Saguhati": 18.0, "Penyertaan": 17.0 },
        "Kebangsaan": { "Johan": 20.0, "Naib Johan": 19.0, "Tempat Ketiga": 18.0, "Saguhati": 17.0, "Penyertaan": 16.0 },
        "Negeri": { "Johan": 17.0, "Naib Johan": 16.0, "Tempat Ketiga": 15.0, "Saguhati": 14.0, "Penyertaan": 13.0 },
        "Daerah": { "Johan": 14.0, "Naib Johan": 13.0, "Tempat Ketiga": 12.0, "Saguhati": 11.0, "Penyertaan": 10.0 },
        "Zon": { "Johan": 11.0, "Naib Johan": 10.0, "Tempat Ketiga": 9.0, "Saguhati": 8.0, "Penyertaan": 7.0 }
    }
    return matrix.get(level, {}).get(achievement, 10.0)

for row in letters:
    let = dict(zip(col_names, row))
    let_id = let["id"]
    
    # Check if already in external_participations
    existing_ep = cursor.execute("SELECT id FROM external_participations WHERE permission_letter_id = ?", (let_id,)).fetchone()
    
    # Try finding represented_org_id if null
    org_id = let.get("represented_org_id")
    if not org_id:
        p_name = let["program_name"].lower()
        if "bola baling" in p_name:
            found_org = cursor.execute("SELECT id FROM organizations WHERE LOWER(name) LIKE '%bola baling%'").fetchone()
            if found_org: org_id = found_org[0]
        elif "bola sepak" in p_name:
            found_org = cursor.execute("SELECT id FROM organizations WHERE LOWER(name) LIKE '%bola sepak%'").fetchone()
            if found_org: org_id = found_org[0]

    level = let.get("participation_level") or "Daerah"
    category = let.get("activity_category") or "Sukan & Permainan"
    event_date = (let.get("start_datetime") or "2026-08-25").split()[0]
    
    if not existing_ep:
        print(f"Syncing letter {let_id} ({let['program_name']}) to external_participations...")
        cursor.execute("""
        INSERT INTO external_participations (
            permission_letter_id, program_name, event_date, venue, organizer,
            activity_category, participation_level, represented_org_id,
            academic_year, notes, status, created_by, verified_by, verified_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, '2026/2027', ?, 'Disahkan', ?, 'Penyelaras Kokurikulum', CURRENT_TIMESTAMP)
        """, (
            let_id,
            let["program_name"],
            event_date,
            let["destination_venue"],
            let["organizer"],
            category,
            level,
            org_id,
            f"Dijana secara automatik daripada Surat Kebenaran No: {let['letter_no']}",
            let.get("created_by") or "admin"
        ))
        ep_id = cursor.lastrowid
    else:
        ep_id = existing_ep[0]

    # Sync students
    st_rows = cursor.execute("SELECT student_id FROM permission_letter_students WHERE letter_id = ?", (let_id,)).fetchall()
    for st in st_rows:
        s_id = st[0]
        already_eps = cursor.execute("SELECT id FROM external_participation_students WHERE participation_id = ? AND student_id = ?", (ep_id, s_id)).fetchone()
        if not already_eps:
            score = get_pajsk_score(level, "Penyertaan", "Peserta")
            cursor.execute("""
            INSERT INTO external_participation_students (
                participation_id, student_id, role, achievement, pajsk_score, remarks
            ) VALUES (?, ?, 'Peserta', 'Penyertaan', ?, 'Dijana dari Surat Kebenaran')
            """, (ep_id, s_id, score))

conn.commit()
conn.close()
print("Database migration and sync completed successfully!")
