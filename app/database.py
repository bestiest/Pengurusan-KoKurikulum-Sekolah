import sqlite3
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_DIR = BASE_DIR / "data"
DB_PATH = DB_DIR / "kokurikulum.db"

def get_db_connection():
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), timeout=15.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_db_connection()
    try:
        conn.execute("PRAGMA journal_mode = WAL")
    except Exception:
        pass
    cursor = conn.cursor()

    # 1. School Settings
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS school_settings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        school_name TEXT NOT NULL DEFAULT 'SEKOLAH KEBANGSAAN SUNGAI DENDANG',
        school_code TEXT NOT NULL DEFAULT 'ABA6034',
        address TEXT NOT NULL DEFAULT 'SK Sungai Dendang, 34140 Rantau Panjang, Selama, Perak Darul Ridzuan',
        phone TEXT NOT NULL DEFAULT '05-8391234',
        email TEXT NOT NULL DEFAULT 'aba6034@moe.edu.my',
        principal_name TEXT NOT NULL DEFAULT 'EN. AHMAD BIN ABDULLAH (GURU BESAR)',
        gpk_koko_name TEXT NOT NULL DEFAULT 'PN. SITI ZALEHA BINTI MOHD NOR (GPK KOKURIKULUM)',
        su_koko_name TEXT NOT NULL DEFAULT 'EN. MOHD FAIZAL BIN HASSAN (SETIAUSAHA KOKURIKULUM)',
        session_year TEXT NOT NULL DEFAULT '2026/2027',
        logo_url TEXT NOT NULL DEFAULT '/static/images/school_logo.png',
        letter_template TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 2. Users
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        full_name TEXT NOT NULL,
        role TEXT NOT NULL,
        email TEXT,
        phone TEXT,
        assigned_category TEXT,
        assigned_org_ids TEXT,
        is_active INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 3. Classes
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS classes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        grade INTEGER NOT NULL,
        class_name TEXT NOT NULL,
        class_teacher TEXT,
        academic_year TEXT DEFAULT '2026/2027',
        UNIQUE(grade, class_name, academic_year)
    )
    """)

    # 4. Teachers
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS teachers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        ic_number TEXT,
        phone TEXT,
        email TEXT,
        designation TEXT,
        is_active INTEGER DEFAULT 1
    )
    """)

    # 5. Organizations
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS organizations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        code TEXT,
        advisor_teachers TEXT,
        coordinator_name TEXT,
        logo_icon TEXT,
        color_code TEXT,
        vision_mission TEXT,
        meeting_day TEXT,
        meeting_time TEXT,
        meeting_venue TEXT,
        academic_year TEXT DEFAULT '2026/2027',
        status TEXT DEFAULT 'Aktif',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 6. Students
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT NOT NULL,
        ic_number TEXT UNIQUE NOT NULL,
        birth_date TEXT,
        gender TEXT NOT NULL,
        grade INTEGER NOT NULL,
        class_name TEXT NOT NULL,
        guardian_name TEXT,
        guardian_phone TEXT,
        address TEXT,
        health_info TEXT DEFAULT 'Tiada alahan / Masalah kesihatan',
        sport_house_id INTEGER,
        uniform_unit_id INTEGER,
        club_society_id INTEGER,
        sports_game_id INTEGER,
        status TEXT DEFAULT 'Aktif',
        academic_year TEXT DEFAULT '2026/2027',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (sport_house_id) REFERENCES organizations(id) ON DELETE SET NULL,
        FOREIGN KEY (uniform_unit_id) REFERENCES organizations(id) ON DELETE SET NULL,
        FOREIGN KEY (club_society_id) REFERENCES organizations(id) ON DELETE SET NULL,
        FOREIGN KEY (sports_game_id) REFERENCES organizations(id) ON DELETE SET NULL
    )
    """)

    # 7. Organization Members
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS organization_members (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        organization_id INTEGER NOT NULL,
        student_id INTEGER NOT NULL,
        academic_year TEXT DEFAULT '2026/2027',
        joined_date TEXT DEFAULT CURRENT_DATE,
        status TEXT DEFAULT 'Aktif',
        UNIQUE(organization_id, student_id, academic_year),
        FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE,
        FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
    )
    """)

    # 8. Student Committees
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS student_committees (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        organization_id INTEGER NOT NULL,
        student_id INTEGER NOT NULL,
        position TEXT NOT NULL,
        academic_year TEXT DEFAULT '2026/2027',
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(organization_id, student_id, position, academic_year),
        FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE,
        FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
    )
    """)

    # 9. Attendance Sessions
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS attendance_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        organization_id INTEGER NOT NULL,
        session_date TEXT NOT NULL,
        start_time TEXT,
        end_time TEXT,
        venue TEXT,
        activity_title TEXT NOT NULL,
        advisor_teacher TEXT,
        academic_year TEXT DEFAULT '2026/2027',
        total_enrolled INTEGER DEFAULT 0,
        total_present INTEGER DEFAULT 0,
        total_absent INTEGER DEFAULT 0,
        total_late INTEGER DEFAULT 0,
        total_excused INTEGER DEFAULT 0,
        notes TEXT,
        created_by TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE
    )
    """)

    # 10. Attendance Records
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS attendance_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id INTEGER NOT NULL,
        student_id INTEGER NOT NULL,
        status TEXT NOT NULL DEFAULT 'Hadir',
        remarks TEXT,
        recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(session_id, student_id),
        FOREIGN KEY (session_id) REFERENCES attendance_sessions(id) ON DELETE CASCADE,
        FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
    )
    """)

    # 11. Weekly Activities
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS weekly_activities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        organization_id INTEGER NOT NULL,
        activity_date TEXT NOT NULL,
        start_time TEXT,
        end_time TEXT,
        venue TEXT,
        title TEXT NOT NULL,
        objectives TEXT,
        description_rundown TEXT,
        teachers_involved TEXT,
        attendees_count INTEGER DEFAULT 0,
        reflection TEXT,
        suggestions TEXT,
        photo_1 TEXT,
        photo_2 TEXT,
        photo_3 TEXT,
        photo_4 TEXT,
        attachment_file TEXT,
        status TEXT DEFAULT 'Draf',
        review_remarks TEXT,
        submitted_by TEXT,
        submitted_at TIMESTAMP,
        reviewed_by TEXT,
        reviewed_at TIMESTAMP,
        approved_by TEXT,
        approved_at TIMESTAMP,
        academic_year TEXT DEFAULT '2026/2027',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE
    )
    """)

    # 12. Permission Letters
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS permission_letters (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        letter_no TEXT,
        program_name TEXT NOT NULL,
        destination_venue TEXT NOT NULL,
        start_datetime TEXT NOT NULL,
        end_datetime TEXT NOT NULL,
        organizer TEXT NOT NULL,
        transportation TEXT,
        accompanying_teachers TEXT,
        fee_amount REAL DEFAULT 0.0,
        contact_person TEXT,
        contact_phone TEXT,
        special_instructions TEXT,
        academic_year TEXT DEFAULT '2026/2027',
        created_by TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 13. Permission Letter Students
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS permission_letter_students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        letter_id INTEGER NOT NULL,
        student_id INTEGER NOT NULL,
        permission_status TEXT DEFAULT 'Belum Diedarkan',
        parent_notes TEXT,
        response_date TEXT,
        UNIQUE(letter_id, student_id),
        FOREIGN KEY (letter_id) REFERENCES permission_letters(id) ON DELETE CASCADE,
        FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
    )
    """)

    # 14. External Participations
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS external_participations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        program_name TEXT NOT NULL,
        event_date TEXT NOT NULL,
        venue TEXT NOT NULL,
        organizer TEXT NOT NULL,
        activity_category TEXT NOT NULL,
        participation_level TEXT NOT NULL,
        represented_org_id INTEGER,
        academic_year TEXT DEFAULT '2026/2027',
        notes TEXT,
        certificate_url TEXT,
        evidence_url TEXT,
        created_by TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        verified_by TEXT,
        verified_at TIMESTAMP,
        status TEXT DEFAULT 'Disahkan',
        FOREIGN KEY (represented_org_id) REFERENCES organizations(id) ON DELETE SET NULL
    )
    """)

    # 15. External Participation Students
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS external_participation_students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        participation_id INTEGER NOT NULL,
        student_id INTEGER NOT NULL,
        role TEXT NOT NULL DEFAULT 'Peserta',
        achievement TEXT NOT NULL DEFAULT 'Penyertaan',
        pajsk_score REAL DEFAULT 0.0,
        remarks TEXT,
        UNIQUE(participation_id, student_id),
        FOREIGN KEY (participation_id) REFERENCES external_participations(id) ON DELETE CASCADE,
        FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
    )
    """)

    # 16. Audit Logs
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        username TEXT NOT NULL,
        user_role TEXT,
        action TEXT NOT NULL,
        module TEXT NOT NULL,
        description TEXT,
        target_id INTEGER,
        old_values TEXT,
        new_values TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 18. School Sports Day Events, Participants & Results
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS school_sports_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_name TEXT NOT NULL,
        category TEXT NOT NULL DEFAULT 'Balapan',
        gender TEXT NOT NULL DEFAULT 'Lelaki',
        grade_level TEXT NOT NULL DEFAULT 'Tahap 2',
        event_type TEXT NOT NULL DEFAULT 'Individu',
        metric_type TEXT NOT NULL DEFAULT 'Masa (Saat)',
        school_record_holder TEXT,
        school_record_value TEXT,
        school_record_year TEXT,
        school_record_num REAL,
        event_date TEXT DEFAULT '2026-07-15',
        academic_year TEXT DEFAULT '2026/2027',
        status TEXT DEFAULT 'Pendaftaran'
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS school_sports_participants (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_id INTEGER NOT NULL,
        student_id INTEGER NOT NULL,
        sport_house_id INTEGER NOT NULL,
        lane_number INTEGER,
        bib_number TEXT,
        academic_year TEXT DEFAULT '2026/2027',
        registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(event_id, student_id),
        FOREIGN KEY (event_id) REFERENCES school_sports_events(id) ON DELETE CASCADE,
        FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
        FOREIGN KEY (sport_house_id) REFERENCES organizations(id) ON DELETE CASCADE
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS school_sports_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_id INTEGER NOT NULL,
        student_id INTEGER NOT NULL,
        sport_house_id INTEGER NOT NULL,
        position_rank INTEGER NOT NULL,
        medal_type TEXT NOT NULL,
        record_metric TEXT,
        record_num REAL,
        is_record_broken INTEGER DEFAULT 0,
        house_points INTEGER NOT NULL DEFAULT 0,
        bonus_points INTEGER NOT NULL DEFAULT 0,
        pajsk_score REAL DEFAULT 0.0,
        remarks TEXT,
        UNIQUE(event_id, position_rank),
        FOREIGN KEY (event_id) REFERENCES school_sports_events(id) ON DELETE CASCADE,
        FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
        FOREIGN KEY (sport_house_id) REFERENCES organizations(id) ON DELETE CASCADE
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sports_scoring_settings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        individual_1st INTEGER DEFAULT 7,
        individual_2nd INTEGER DEFAULT 5,
        individual_3rd INTEGER DEFAULT 3,
        individual_4th INTEGER DEFAULT 1,
        group_1st INTEGER DEFAULT 14,
        group_2nd INTEGER DEFAULT 10,
        group_3rd INTEGER DEFAULT 6,
        group_4th INTEGER DEFAULT 2,
        record_broken_bonus INTEGER DEFAULT 2,
        include_cross_country INTEGER DEFAULT 1
    )
    """)

    # Seed default scoring settings if not present
    cursor.execute("SELECT COUNT(*) FROM sports_scoring_settings")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
        INSERT INTO sports_scoring_settings (id, individual_1st, individual_2nd, individual_3rd, individual_4th, group_1st, group_2nd, group_3rd, group_4th, record_broken_bonus, include_cross_country)
        VALUES (1, 7, 5, 3, 1, 14, 10, 6, 2, 2, 1)
        """)

    # 19. School Cross Country Categories, Records & Scoring Settings
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cross_country_categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category_name TEXT NOT NULL UNIQUE,
        gender TEXT NOT NULL,
        grade_level TEXT NOT NULL DEFAULT 'Tahap 2',
        distance_km REAL DEFAULT 3.0,
        school_record_holder TEXT,
        school_record_time TEXT,
        school_record_seconds REAL,
        school_record_year TEXT DEFAULT '2024',
        academic_year TEXT DEFAULT '2026/2027'
    )
    """)

    # Seed default categories if not present
    cursor.execute("SELECT COUNT(*) FROM cross_country_categories")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
        INSERT INTO cross_country_categories (id, category_name, gender, grade_level, distance_km, school_record_holder, school_record_time, school_record_seconds, school_record_year)
        VALUES 
        (1, 'Lelaki (Tahap 2)', 'Lelaki', 'Tahap 2', 3.5, 'Muhammad Danish Irfan (Merah)', '14m 15s', 855.0, '2024'),
        (2, 'Perempuan (Tahap 2)', 'Perempuan', 'Tahap 2', 3.0, 'Nur Syazwani binti Azhar (Hijau)', '16m 30s', 990.0, '2024')
        """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cross_country_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT NOT NULL,
        student_id INTEGER,
        sport_house_id INTEGER NOT NULL,
        rank_position INTEGER NOT NULL,
        time_recorded TEXT,
        time_seconds REAL,
        is_record_broken INTEGER DEFAULT 0,
        house_points INTEGER NOT NULL DEFAULT 0,
        bonus_points INTEGER DEFAULT 0,
        pajsk_score REAL DEFAULT 0.0,
        event_date TEXT DEFAULT '2026-05-10',
        academic_year TEXT DEFAULT '2026/2027',
        remarks TEXT,
        UNIQUE(category, rank_position, academic_year),
        FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
        FOREIGN KEY (sport_house_id) REFERENCES organizations(id) ON DELETE CASCADE
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cross_country_scoring_settings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        max_individual_placings INTEGER DEFAULT 15,
        max_total_finishers INTEGER DEFAULT 50,
        points_rank_1 INTEGER DEFAULT 20,
        points_rank_2 INTEGER DEFAULT 18,
        points_rank_3 INTEGER DEFAULT 16,
        points_rank_4 INTEGER DEFAULT 14,
        points_rank_5 INTEGER DEFAULT 12,
        points_rank_6 INTEGER DEFAULT 10,
        points_rank_7 INTEGER DEFAULT 9,
        points_rank_8 INTEGER DEFAULT 8,
        points_rank_9 INTEGER DEFAULT 7,
        points_rank_10 INTEGER DEFAULT 6,
        points_rank_11 INTEGER DEFAULT 5,
        points_rank_12 INTEGER DEFAULT 4,
        points_rank_13 INTEGER DEFAULT 3,
        points_rank_14 INTEGER DEFAULT 2,
        points_rank_15 INTEGER DEFAULT 1,
        points_rank_16_to_50 INTEGER DEFAULT 1,
        record_broken_bonus INTEGER DEFAULT 2
    )
    """)

    # Seed default cross country scoring settings if not present
    cursor.execute("SELECT COUNT(*) FROM cross_country_scoring_settings")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
        INSERT INTO cross_country_scoring_settings (
            id, max_individual_placings, max_total_finishers,
            points_rank_1, points_rank_2, points_rank_3, points_rank_4, points_rank_5,
            points_rank_6, points_rank_7, points_rank_8, points_rank_9, points_rank_10,
            points_rank_11, points_rank_12, points_rank_13, points_rank_14, points_rank_15,
            points_rank_16_to_50, record_broken_bonus
        ) VALUES (
            1, 15, 50,
            20, 18, 16, 14, 12,
            10, 9, 8, 7, 6,
            5, 4, 3, 2, 1,
            1, 2
        )
        """)

    # Ensure all 4 standard Rumah Sukan exist
    standard_houses = [
        ("Rumah Bendahara (Merah)", "Rumah Sukan", "#dc2626", "Cikgu Razak & Cikgu Siti", "Khamis", "3:00 - 5:00 Petang", "Padang A", "Maju dan Tangkas"),
        ("Rumah Temenggong (Kuning)", "Rumah Sukan", "#eab308", "Cikgu Kamal & Cikgu Noraini", "Khamis", "3:00 - 5:00 Petang", "Padang B", "Gagah dan Berani"),
        ("Rumah Laksamana (Biru)", "Rumah Sukan", "#2563eb", "Cikgu Hafiz & Cikgu Zulaikha", "Khamis", "3:00 - 5:00 Petang", "Padang C", "Pantas dan Cekap"),
        ("Rumah Syahbandar (Hijau)", "Rumah Sukan", "#16a34a", "Cikgu Syakir & Cikgu Salina", "Khamis", "3:00 - 5:00 Petang", "Padang D", "Teguh dan Cemerlang")
    ]
    for h_name, cat, col, adv, day, tim, ven, vm in standard_houses:
        exists = cursor.execute("SELECT id FROM organizations WHERE name = ? AND category = 'Rumah Sukan'", (h_name,)).fetchone()
        if not exists:
            cursor.execute("""
                INSERT INTO organizations (name, category, color_code, advisor_teachers, meeting_day, meeting_time, meeting_venue, vision_mission, status, academic_year)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Aktif', '2026/2027')
            """, (h_name, cat, col, adv, day, tim, ven, vm))

    # Safe column migrations for existing SQLite databases
    try:
        cursor.execute("ALTER TABLE school_sports_events ADD COLUMN event_type TEXT DEFAULT 'Individu'")
    except Exception:
        pass
    try:
        cursor.execute("ALTER TABLE school_sports_events ADD COLUMN metric_type TEXT DEFAULT 'Masa (Saat)'")
    except Exception:
        pass
    try:
        cursor.execute("ALTER TABLE school_sports_events ADD COLUMN school_record_holder TEXT")
    except Exception:
        pass
    try:
        cursor.execute("ALTER TABLE school_sports_events ADD COLUMN school_record_value TEXT")
    except Exception:
        pass
    try:
        cursor.execute("ALTER TABLE school_sports_events ADD COLUMN school_record_year TEXT")
    except Exception:
        pass
    try:
        cursor.execute("ALTER TABLE school_sports_events ADD COLUMN school_record_num REAL")
    except Exception:
        pass
    try:
        cursor.execute("ALTER TABLE school_sports_results ADD COLUMN record_num REAL")
    except Exception:
        pass
    try:
        cursor.execute("ALTER TABLE school_sports_results ADD COLUMN is_record_broken INTEGER DEFAULT 0")
    except Exception:
        pass
    try:
        cursor.execute("ALTER TABLE school_sports_results ADD COLUMN bonus_points INTEGER DEFAULT 0")
    except Exception:
        pass
    try:
        cols = [r[1] for r in cursor.execute("PRAGMA table_info(cross_country_records)").fetchall()]
        st_not_null = [r[3] for r in cursor.execute("PRAGMA table_info(cross_country_records)").fetchall() if r[1] == 'student_id']
        if st_not_null and st_not_null[0] == 1:
            cursor.execute("DROP TABLE cross_country_records")
            cursor.execute("""
            CREATE TABLE cross_country_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                student_id INTEGER,
                sport_house_id INTEGER NOT NULL,
                rank_position INTEGER NOT NULL,
                time_recorded TEXT,
                time_seconds REAL,
                is_record_broken INTEGER DEFAULT 0,
                house_points INTEGER NOT NULL DEFAULT 0,
                bonus_points INTEGER DEFAULT 0,
                pajsk_score REAL DEFAULT 0.0,
                event_date TEXT DEFAULT '2026-05-10',
                academic_year TEXT DEFAULT '2026/2027',
                remarks TEXT,
                UNIQUE(category, rank_position, academic_year),
                FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
                FOREIGN KEY (sport_house_id) REFERENCES organizations(id) ON DELETE CASCADE
            )
            """)
    except Exception:
        pass

    conn.commit()
    conn.close()

def log_audit(user_id: int, username: str, user_role: str, action: str, module: str, description: str, target_id: int = None, old_values: str = None, new_values: str = None):
    try:
        conn = get_db_connection()
        conn.execute(
            """
            INSERT INTO audit_logs (user_id, username, user_role, action, module, description, target_id, old_values, new_values)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, username, user_role, action, module, description, target_id, old_values, new_values)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Audit log error: {e}")

