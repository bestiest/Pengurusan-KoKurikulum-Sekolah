import json
from app.database import get_db_connection
from app.auth import hash_password

def seed_demo_data(force: bool = False):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if data already exists
    user_count = cursor.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    if user_count > 0 and not force:
        conn.close()
        return

    print("Menyemai Data Kokurikulum SK Sungai Dendang...")

    # Clear existing if force
    if force:
        tables = [
            "users", "school_settings", "classes", "teachers", "organizations",
            "students", "organization_members", "student_committees",
            "attendance_sessions", "attendance_records", "weekly_activities",
            "permission_letters", "permission_letter_students",
            "external_participations", "external_participation_students", "audit_logs"
        ]
        for t in tables:
            cursor.execute(f"DELETE FROM {t}")

    # 1. School Settings
    cursor.execute("""
    INSERT INTO school_settings (
        id, school_name, school_code, address, phone, email,
        principal_name, gpk_koko_name, su_koko_name, session_year, logo_url, letter_template
    ) VALUES (
        1,
        'SEKOLAH KEBANGSAAN SUNGAI DENDANG',
        'ABA6034',
        'SK Sungai Dendang, 34140 Rantau Panjang, Selama, Perak Darul Ridzuan',
        '05-8391234',
        'aba6034@moe.edu.my',
        'EN. AHMAD BIN ABDULLAH (GURU BESAR)',
        'PN. SITI ZALEHA BINTI MOHD NOR (GPK KOKURIKULUM)',
        'EN. MOHD FAIZAL BIN HASSAN (SETIAUSAHA KOKURIKULUM)',
        '2026/2027',
        '/static/images/school_logo.png',
        'Sukacita dimaklumkan bahawa pihak sekolah akan mengadakan aktiviti kokurikulum di luar sekolah seperti butiran yang dinyatakan di bawah. Sehubungan itu, pihak sekolah memohon kerjasama dan kebenaran daripada pihak tuan/puan untuk membenarkan anak/jagaan tuan/puan menyertai program ini.'
    )
    """)

    # 2. Users (5 Distinct Roles - Default password: aba6038)
    users_data = [
        ("admin", hash_password("aba6038"), "Pentadbir Sistem (Admin)", "Admin", "admin@sksungaidendang.edu.my", "019-5551101", None, None),
        ("gpk_koko", hash_password("aba6038"), "Pn. Siti Zaleha binti Mohd Nor", "GPK Kokurikulum", "gpk.koko@sksungaidendang.edu.my", "019-5551102", None, None),
        ("su_koko", hash_password("aba6038"), "En. Mohd Faizal bin Hassan", "Setiausaha Kokurikulum", "su.koko@sksungaidendang.edu.my", "019-5551103", None, None),
        ("penyelaras_uniform", hash_password("aba6038"), "Ustaz Mohd Syakir bin Othman", "Penyelaras Kokurikulum", "syakir@sksungaidendang.edu.my", "019-5551104", "Unit Beruniform", None),
        ("guru_penasihat", hash_password("aba6038"), "Cikgu Norhafizah binti Ismail", "Guru Penasihat", "norhafizah@sksungaidendang.edu.my", "019-5551105", None, "1,5,10,16")
    ]
    cursor.executemany("""
    INSERT INTO users (username, password_hash, full_name, role, email, phone, assigned_category, assigned_org_ids)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, users_data)

    # 3. Classes (Tahun 1 hingga 6)
    classes_data = [
        (1, "1 UM", "Pn. Salmiah binti Yusof", "2026/2027"),
        (2, "2 UKM", "Pn. Faridah binti Kassim", "2026/2027"),
        (3, "3 UPM", "Pn. Norliza binti Zakaria", "2026/2027"),
        (4, "4 USM", "Cikgu Norhafizah binti Ismail", "2026/2027"),
        (5, "5 UTM", "En. Mohd Faizal bin Hassan", "2026/2027"),
        (6, "6 UITM", "En. Zulkifli bin Daud", "2026/2027"),
    ]
    cursor.executemany("INSERT INTO classes (grade, class_name, class_teacher, academic_year) VALUES (?, ?, ?, ?)", classes_data)

    # 4. Teachers
    teachers_data = [
        ("En. Ahmad bin Abdullah", "780512085433", "019-5551001", "ahmad@sksungaidendang.edu.my", "Guru Besar"),
        ("Pn. Siti Zaleha binti Mohd Nor", "800315086542", "019-5551102", "gpk.koko@sksungaidendang.edu.my", "GPK Kokurikulum"),
        ("En. Mohd Faizal bin Hassan", "840722085119", "019-5551103", "faizal@sksungaidendang.edu.my", "Setiausaha Kokurikulum"),
        ("Ustaz Mohd Syakir bin Othman", "861104085871", "019-5551104", "syakir@sksungaidendang.edu.my", "Penyelaras Unit Beruniform"),
        ("Cikgu Norhafizah binti Ismail", "880918086224", "019-5551105", "norhafizah@sksungaidendang.edu.my", "Guru Penasihat Pengakap"),
        ("En. Zulkifli bin Daud", "820120085991", "019-5551106", "zulkifli@sksungaidendang.edu.my", "Penyelaras Sukan & Permainan"),
        ("Pn. Rosnah binti Abdul Wahab", "850614085440", "019-5551107", "rosnah@sksungaidendang.edu.my", "Penyelaras Kelab & Persatuan"),
        ("En. Khairul Azhar bin Ramli", "870425086113", "019-5551108", "khairul@sksungaidendang.edu.my", "Penyelaras Rumah Sukan"),
        ("Pn. Salmiah binti Yusof", "890802085332", "019-5551109", "salmiah@sksungaidendang.edu.my", "Guru Penasihat BSMM"),
        ("En. Shahril bin Mansor", "831205085773", "019-5551110", "shahril@sksungaidendang.edu.my", "Guru Penasihat Bola Sepak"),
        ("Pn. Faridah binti Kassim", "810419086118", "019-5551111", "faridah@sksungaidendang.edu.my", "Guru Penasihat Bola Jaring"),
        ("En. Azman bin Hashim", "860830085221", "019-5551112", "azman@sksungaidendang.edu.my", "Guru Penasihat Badminton"),
        ("Pn. Hasnah binti Salleh", "840211085664", "019-5551113", "hasnah@sksungaidendang.edu.my", "Guru Penasihat STEM"),
        ("Pn. Norliza binti Zakaria", "870709085882", "019-5551114", "norliza@sksungaidendang.edu.my", "Guru Penasihat PPIM"),
        ("En. Kamal Ariffin bin Bakar", "850917085337", "019-5551115", "kamal@sksungaidendang.edu.my", "Guru Penasihat TKRS")
    ]
    cursor.executemany("INSERT INTO teachers (name, ic_number, phone, email, designation) VALUES (?, ?, ?, ?, ?)", teachers_data)

    # 5. Organizations (4 Categories: 4 Rumah Sukan, 5 Unit Beruniform, 6 Kelab/Persatuan, 6 Sukan/Permainan)
    organizations_data = [
        # Rumah Sukan (IDs 1-4)
        (1, "Rumah Bendahara (Merah)", "Rumah Sukan", "RS-MERAH", "En. Khairul Azhar bin Ramli, Pn. Norliza binti Zakaria", "En. Khairul Azhar bin Ramli", "shield", "#ef4444", "Membina kecergasan fizikal dan semangat juang pahlawan.", "Selasa", "4:30 PM - 6:00 PM", "Padang Utama A"),
        (2, "Rumah Temenggong (Kuning)", "Rumah Sukan", "RS-KUNING", "En. Shahril bin Mansor, Pn. Hasnah binti Salleh", "En. Khairul Azhar bin Ramli", "shield", "#eab308", "Cemerlang dalam sukan, berdisiplin tinggi dan berdaya saing.", "Selasa", "4:30 PM - 6:00 PM", "Padang Utama B"),
        (3, "Rumah Laksamana (Biru)", "Rumah Sukan", "RS-BIRU", "En. Zulkifli bin Daud, Pn. Faridah binti Kassim", "En. Khairul Azhar bin Ramli", "shield", "#3b82f6", "Ketangkasan, ketahanan mental dan kerjasama berpasukan.", "Khamis", "4:30 PM - 6:00 PM", "Padang Utama A"),
        (4, "Rumah Syahbandar (Hijau)", "Rumah Sukan", "RS-HIJAU", "Ustaz Mohd Syakir bin Othman, Pn. Salmiah binti Yusof", "En. Khairul Azhar bin Ramli", "shield", "#10b981", "Semangat perpaduan dan kecemerlangan sukan berterusan.", "Khamis", "4:30 PM - 6:00 PM", "Padang Utama B"),

        # Unit Beruniform (IDs 5-9)
        (5, "Persekutuan Pengakap Malaysia (Pengakap)", "Unit Beruniform", "UB-PENGAKAP", "Cikgu Norhafizah binti Ismail, En. Mohd Faizal bin Hassan", "Ustaz Mohd Syakir bin Othman", "award", "#0284c7", "Melatih murid berdikari, berdisiplin dan berkhidmat kepada masyarakat.", "Rabu", "2:00 PM - 3:30 PM", "Dewan Terbuka"),
        (6, "Bulan Sabit Merah Malaysia (BSMM)", "Unit Beruniform", "UB-BSMM", "Pn. Salmiah binti Yusof, En. Azman bin Hashim", "Ustaz Mohd Syakir bin Othman", "heart-pulse", "#dc2626", "Menyemai rasa perikemanusiaan, pertolongan cemas dan kesukarelawanan.", "Rabu", "2:00 PM - 3:30 PM", "Bilik Kesihatan & APD"),
        (7, "Tunas Kadet Remaja Sekolah (TKRS)", "Unit Beruniform", "UB-TKRS", "En. Kamal Ariffin bin Bakar, En. Zulkifli bin Daud", "Ustaz Mohd Syakir bin Othman", "shield-check", "#15803d", "Membentuk generasi murid berjiwa patriotik dan berketrampilan mulia.", "Rabu", "2:00 PM - 3:30 PM", "Dataran Perhimpunan"),
        (8, "Pergerakan Pandu Puteri Tunas (PPT)", "Unit Beruniform", "UB-PPT", "Pn. Faridah binti Kassim, Pn. Hasnah binti Salleh", "Ustaz Mohd Syakir bin Othman", "sparkles", "#6366f1", "Memperkasa sahsiah dan kepimpinan murid perempuan.", "Rabu", "2:00 PM - 3:30 PM", "Pusat Sumber Sekolah"),
        (9, "Pergerakan Puteri Islam Malaysia (PPIM)", "Unit Beruniform", "UB-PPIM", "Pn. Norliza binti Zakaria, Pn. Rosnah binti Abdul Wahab", "Ustaz Mohd Syakir bin Othman", "moon", "#ec4899", "Membimbing puteri yang berilmu, bertakwa dan beramal soleh.", "Rabu", "2:00 PM - 3:30 PM", "Surau Al-Falah"),

        # Kelab & Persatuan (IDs 10-15)
        (10, "Persatuan Bahasa Melayu", "Kelab & Persatuan", "KP-PBM", "Cikgu Norhafizah binti Ismail, Pn. Salmiah binti Yusof", "Pn. Rosnah binti Abdul Wahab", "book-open", "#d97706", "Memartabatkan bahasa kebangsaan melalui pengucapan awam dan penulisan kreatif.", "Rabu", "3:30 PM - 5:00 PM", "Bilik Bahasa 1"),
        (11, "English Language Society (Kelab Bahasa Inggeris)", "Kelab & Persatuan", "KP-ELS", "Pn. Faridah binti Kassim, En. Khairul Azhar bin Ramli", "Pn. Rosnah binti Abdul Wahab", "globe", "#2563eb", "Enhancing communicative proficiency and public speaking in English.", "Rabu", "3:30 PM - 5:00 PM", "Makmal Bahasa"),
        (12, "Kelab STEM & Robotik", "Kelab & Persatuan", "KP-STEM", "Pn. Hasnah binti Salleh, En. Mohd Faizal bin Hassan", "Pn. Rosnah binti Abdul Wahab", "cpu", "#0891b2", "Meneroka inovasi sains, pengaturcaraan awal dan reka cipta teknologi.", "Rabu", "3:30 PM - 5:00 PM", "Makmal Komputer & Bilik STEM"),
        (13, "Persatuan Agama Islam & Bahasa Arab", "Kelab & Persatuan", "KP-PAI", "Ustaz Mohd Syakir bin Othman, Pn. Norliza binti Zakaria", "Pn. Rosnah binti Abdul Wahab", "star", "#059669", "Memperkukuh kefahaman Islam, khat jawi dan tilawah Al-Quran.", "Rabu", "3:30 PM - 5:00 PM", "Surau Al-Falah"),
        (14, "Kelab Seni & Kebudayaan", "Kelab & Persatuan", "KP-SENI", "Pn. Rosnah binti Abdul Wahab, En. Shahril bin Mansor", "Pn. Rosnah binti Abdul Wahab", "palette", "#8b5cf6", "Mencungkil bakat seni visual, muzik tradisional dan seni teater.", "Rabu", "3:30 PM - 5:00 PM", "Bilik Seni Visual"),
        (15, "Kelab Doktor Muda & Kesihatan", "Kelab & Persatuan", "KP-DOKTOR", "En. Azman bin Hashim, Pn. Siti Zaleha binti Mohd Nor", "Pn. Rosnah binti Abdul Wahab", "activity", "#e11d48", "Mendidik amalan hidup sihat dan kebersihan persekitaran sekolah.", "Rabu", "3:30 PM - 5:00 PM", "Bilik Kesihatan"),

        # Sukan & Permainan (IDs 16-21)
        (16, "Kelab Bola Jaring", "Sukan & Permainan", "SP-BJ", "Pn. Faridah binti Kassim, Cikgu Norhafizah binti Ismail", "En. Zulkifli bin Daud", "target", "#ec4899", "Membangunkan kemahiran asas hantaran, posisi dan strategi perlawanan.", "Khamis", "4:30 PM - 6:00 PM", "Gelanggang Bola Jaring"),
        (17, "Kelab Bola Sepak", "Sukan & Permainan", "SP-BS", "En. Shahril bin Mansor, En. Zulkifli bin Daud", "En. Zulkifli bin Daud", "trophy", "#16a34a", "Memupuk kemahiran kawalan bola, taktikal permainan dan disiplin pasukan.", "Selasa", "4:30 PM - 6:00 PM", "Padang Bola Sepak Utama"),
        (18, "Kelab Badminton", "Sukan & Permainan", "SP-BAD", "En. Azman bin Hashim, Pn. Salmiah binti Yusof", "En. Zulkifli bin Daud", "zap", "#f59e0b", "Menguasai teknik pukulan servis, lob, smash dan gerak kaki pantas.", "Rabu", "4:30 PM - 6:00 PM", "Dewan Serbaguna"),
        (19, "Kelab Sepak Takraw", "Sukan & Permainan", "SP-TAKRAW", "En. Kamal Ariffin bin Bakar, Ustaz Mohd Syakir bin Othman", "En. Zulkifli bin Daud", "crosshair", "#ea580c", "Melatih teknik servis kuda/sila, apit kanan, apit kiri dan rejaman.", "Selasa", "4:30 PM - 6:00 PM", "Gelanggang Sepak Takraw"),
        (20, "Kelab Olahraga & Merentas Desa", "Sukan & Permainan", "SP-OLAHRAGA", "En. Khairul Azhar bin Ramli, Pn. Norliza binti Zakaria", "En. Zulkifli bin Daud", "flame", "#dc2626", "Latihan lari pecut, lompat jauh, lontar peluru dan ketahanan jarak jauh.", "Khamis", "4:30 PM - 6:00 PM", "Trek Olahraga Padang"),
        (21, "Kelab Catur & Permainan Dalaman", "Sukan & Permainan", "SP-CATUR", "Pn. Hasnah binti Salleh, En. Mohd Faizal bin Hassan", "En. Zulkifli bin Daud", "layout-grid", "#475569", "Mengasah pemikiran kritikal, analisis strategi dan konsentrasi minda.", "Rabu", "4:30 PM - 6:00 PM", "Pusat Sumber Sekolah")
    ]
    cursor.executemany("""
    INSERT INTO organizations (
        id, name, category, code, advisor_teachers, coordinator_name,
        logo_icon, color_code, vision_mission, meeting_day, meeting_time, meeting_venue
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, organizations_data)

    # 6. Students Data (40 students across Grades 1-6)
    raw_students = [
        # Grade 6
        ("MUHAMMAD DANISH IRFAN BIN ZULKIFLI", "140515085123", "2014-05-15", "Lelaki", 6, "6 UITM", "Zulkifli bin Daud", "012-5881234", "No 12, Kg Sungai Dendang, 34140 Selama, Perak", "Tiada", 1, 5, 12, 17),
        ("NUR AISYAH HUMAIRA BINTI AHMAD", "140820086244", "2014-08-20", "Perempuan", 6, "6 UITM", "Ahmad bin Abdullah", "013-4885678", "No 45, Lorong Mawar, Rantau Panjang, Selama", "Alahan Udang", 2, 8, 10, 16),
        ("ADAM HARITH BIN MOHD FAIZAL", "140310085431", "2014-03-10", "Lelaki", 6, "6 UITM", "Mohd Faizal bin Hassan", "019-5551103", "Kuarters Guru SK Sungai Dendang, Selama", "Tiada", 3, 7, 12, 18),
        ("SITI NURHALIZA BINTI KHAIRUL", "141125086782", "2014-11-25", "Perempuan", 6, "6 UITM", "Khairul Azhar bin Ramli", "017-6229988", "No 8, Jalan Melati, Kg Sungai Dendang", "Asma ringan (Bawa inhaler)", 4, 9, 13, 16),
        ("MUHAMMAD AMIRUL HAKIM BIN AZMAN", "140204085519", "2014-02-04", "Lelaki", 6, "6 UITM", "Azman bin Hashim", "012-3334411", "No 23, Kg Sungai Dendang Luar, Selama", "Tiada", 1, 5, 11, 19),
        
        ("NUR DAMIA BATRISYIA BINTI ROSLAN", "140718086390", "2014-07-18", "Perempuan", 6, "6 UITM", "Roslan bin Che Din", "014-9988112", "No 19, Kg Tebing Tinggi, Selama", "Tiada", 2, 6, 14, 16),
        ("MUHAMMAD FARIS HAZIQ BIN KAMAL", "140909085877", "2014-09-09", "Lelaki", 6, "6 UITM", "Kamal Ariffin bin Bakar", "019-5551115", "No 5, Kg Sungai Dendang, Selama", "Tiada", 3, 5, 10, 17),
        ("NURUL IMAN BINTI MOHD SYAKIR", "140412086118", "2014-04-12", "Perempuan", 6, "6 UITM", "Mohd Syakir bin Othman", "019-5551104", "Kuarters Guru SK Sungai Dendang", "Tiada", 4, 9, 13, 21),
        ("MUHAMMAD RAYYAN MIKAIL BIN SHAHRIL", "141201085003", "2014-12-01", "Lelaki", 6, "6 UITM", "Shahril bin Mansor", "019-5551110", "No 31, Jalan Mesra, Rantau Panjang", "Tiada", 1, 7, 12, 17),
        ("PUTERI NUR JANNAH BINTI ZAKARIA", "140630086554", "2014-06-30", "Perempuan", 6, "6 UITM", "Zakaria bin Idris", "013-7744332", "No 7, Kg Pondok Lalang, Selama", "Tiada", 2, 8, 15, 16),

        # Grade 5
        ("AHMAD SYAMIL BIN ZULKIFLI", "150119085443", "2015-01-19", "Lelaki", 5, "5 UTM", "Zulkifli bin Daud", "012-5881234", "No 12, Kg Sungai Dendang, Selama", "Tiada", 3, 5, 12, 17),
        ("NUR AFRINA BALQIS BINTI HASSAN", "150522086338", "2015-05-22", "Perempuan", 5, "5 UTM", "Hassan bin Basri", "011-23456789", "No 88, Kg Sungai Dendang", "Tiada", 4, 6, 10, 16),
        ("MUHAMMAD HAFIZUDDIN BIN SALLEH", "150314085711", "2015-03-14", "Lelaki", 5, "5 UTM", "Salleh bin Mat", "016-5544332", "No 14, Lorong Kenanga, Selama", "Tiada", 1, 7, 11, 20),
        ("NUR ZULAIKHA BINTI FAIZAL", "150910086992", "2015-09-10", "Perempuan", 5, "5 UTM", "Mohd Faizal bin Hassan", "019-5551103", "Kuarters Guru SK Sungai Dendang", "Tiada", 2, 8, 13, 21),
        ("MUHAMMAD IRFAN NAJMI BIN ISMAIL", "151108085227", "2015-11-08", "Lelaki", 5, "5 UTM", "Ismail bin Ibrahim", "017-8899001", "No 67, Kg Tebing Tinggi, Selama", "Alahan Kacang", 3, 5, 14, 18),

        ("NUR SYAZWANI BINTI AZHAR", "150403086446", "2015-04-03", "Perempuan", 5, "5 UTM", "Khairul Azhar bin Ramli", "017-6229988", "No 8, Jalan Melati, Kg Sungai Dendang", "Tiada", 4, 9, 10, 16),
        ("MUHAMMAD HARRAZ BIN SHAHRIZAL", "150827085335", "2015-08-27", "Lelaki", 5, "5 UTM", "Shahrizal bin Othman", "018-9900112", "No 3, Kg Bukit Selambau, Selama", "Tiada", 1, 7, 12, 17),
        ("NUR QISTINA ALYA BINTI NORAZAM", "151015086884", "2015-10-15", "Perempuan", 5, "5 UTM", "Norazam bin Ariffin", "013-6655443", "No 29, Kg Sungai Dendang Hilir", "Tiada", 2, 6, 15, 21),
        ("MUHAMMAD AQIL AQASHA BIN HAMDAN", "150606085669", "2015-06-06", "Lelaki", 5, "5 UTM", "Hamdan bin Kassim", "019-4455667", "No 51, Jalan Besar, Selama", "Tiada", 3, 5, 11, 19),
        ("NUR HIDAYAH BINTI MANSOR", "151219086110", "2015-12-19", "Perempuan", 5, "5 UTM", "Mansor bin Che Mat", "012-7788990", "No 18, Kg Sungai Dendang Luar", "Tiada", 4, 8, 14, 16),

        # Grade 4
        ("MUHAMMAD LUQMAN HAKIM BIN RADZI", "160211085113", "2016-02-11", "Lelaki", 4, "4 USM", "Radzi bin Mahamud", "019-7711223", "No 10, Kg Sungai Dendang", "Tiada", 1, 5, 12, 17),
        ("NUR AMALINA BINTI ZAINAL", "160429086552", "2016-04-29", "Perempuan", 4, "4 USM", "Zainal bin Abidin", "013-3344556", "No 92, Lorong Cempaka, Selama", "Tiada", 2, 8, 10, 16),
        ("MUHAMMAD AMMAR BIN ZULKIFLI", "160714085885", "2016-07-14", "Lelaki", 4, "4 USM", "Zulkifli bin Daud", "012-5881234", "No 12, Kg Sungai Dendang", "Tiada", 3, 7, 11, 18),
        ("NUR INSYIRAH BINTI SYAKIR", "160905086228", "2016-09-05", "Perempuan", 4, "4 USM", "Mohd Syakir bin Othman", "019-5551104", "Kuarters Guru SK Sungai Dendang", "Tiada", 4, 9, 13, 21),
        ("MUHAMMAD ZAFRAN BIN KHAIRUL", "161120085447", "2016-11-20", "Lelaki", 4, "4 USM", "Khairul Azhar bin Ramli", "017-6229988", "No 8, Jalan Melati, Selama", "Tiada", 1, 5, 14, 20),

        ("NUR FARHANA BINTI SHUKOR", "160130086774", "2016-01-30", "Perempuan", 4, "4 USM", "Shukor bin Jamil", "011-99887766", "No 41, Kg Tebing Tinggi", "Tiada", 2, 6, 10, 16),
        ("MUHAMMAD ADAM DANIAL BIN FAUZI", "160325085991", "2016-03-25", "Lelaki", 4, "4 USM", "Fauzi bin Hassan", "018-7766554", "No 25, Kg Sungai Dendang", "Tiada", 3, 7, 12, 17),
        ("NUR HANNANI BINTI AZIZ", "160618086336", "2016-06-18", "Perempuan", 4, "4 USM", "Aziz bin Yusof", "014-5566778", "No 16, Jalan Mawar, Selama", "Tiada", 4, 8, 15, 18),
        ("MUHAMMAD ARIF FAIZ BIN SAIFUL", "160809085663", "2016-08-09", "Lelaki", 4, "4 USM", "Saiful bin Bahari", "019-3322110", "No 34, Kg Pondok Lalang", "Tiada", 1, 5, 11, 19),
        ("NUR AUNI MAISARAH BINTI RAZALI", "161022086448", "2016-10-22", "Perempuan", 4, "4 USM", "Razali bin Daud", "012-6655441", "No 59, Kg Sungai Dendang", "Tiada", 2, 9, 13, 21),

        # Grade 3, 2, 1 (Tahap 1)
        ("MUHAMMAD AQIL BIN ZULKIFLI", "170312085331", "2017-03-12", "Lelaki", 3, "3 UPM", "Zulkifli bin Daud", "012-5881234", "No 12, Kg Sungai Dendang", "Tiada", 1, None, None, None),
        ("NUR JANNAH BINTI AHMAD", "170725086882", "2017-07-25", "Perempuan", 3, "3 UPM", "Ahmad bin Abdullah", "013-4885678", "No 45, Lorong Mawar", "Tiada", 2, None, None, None),
        ("MUHAMMAD HAZIQ BIN AZMAN", "170918085223", "2017-09-18", "Lelaki", 3, "3 UPM", "Azman bin Hashim", "012-3334411", "No 23, Kg Sungai Dendang Luar", "Tiada", 3, None, None, None),
        ("NUR ALEEYA BINTI MOHD FAIZAL", "180215086446", "2018-02-15", "Perempuan", 2, "2 UKM", "Mohd Faizal bin Hassan", "019-5551103", "Kuarters Guru SK Sungai Dendang", "Tiada", 4, None, None, None),
        ("MUHAMMAD AMIN BIN SHAHRIL", "180830085779", "2018-08-30", "Lelaki", 2, "2 UKM", "Shahril bin Mansor", "019-5551110", "No 31, Jalan Mesra", "Tiada", 1, None, None, None),
        ("NUR MEDINA BINTI SYAKIR", "190510086224", "2019-05-10", "Perempuan", 1, "1 UM", "Mohd Syakir bin Othman", "019-5551104", "Kuarters Guru SK Sungai Dendang", "Tiada", 2, None, None, None),
        ("MUHAMMAD FATEH BIN KHAIRUL", "191112085887", "2019-11-12", "Lelaki", 1, "1 UM", "Khairul Azhar bin Ramli", "017-6229988", "No 8, Jalan Melati, Selama", "Tiada", 3, None, None, None)
    ]

    for st in raw_students:
        cursor.execute("""
        INSERT INTO students (
            full_name, ic_number, birth_date, gender, grade, class_name,
            guardian_name, guardian_phone, address, health_info,
            sport_house_id, uniform_unit_id, club_society_id, sports_game_id,
            status, academic_year
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Aktif', '2026/2027')
        """, st)
        student_id = cursor.lastrowid

        # Insert to organization_members
        for org_id in [st[10], st[11], st[12], st[13]]:
            if org_id:
                cursor.execute("""
                INSERT OR IGNORE INTO organization_members (organization_id, student_id, academic_year)
                VALUES (?, ?, '2026/2027')
                """, (org_id, student_id))

    # 7. Student Committees
    committees_data = [
        # Pengakap (Org ID 5)
        (5, 1, "Pengerusi", "2026/2027", "Dilantik sebulat suara mesyuarat agung"),
        (5, 7, "Naib Pengerusi", "2026/2027", "Membantu pengerusi menguruskan aktiviti"),
        (5, 5, "Setiausaha", "2026/2027", "Mencatat kehadiran dan minit"),
        (5, 21, "Bendahari", "2026/2027", "Mengurus tabung kebajikan pengakap"),
        (5, 11, "Ahli Jawatankuasa", "2026/2027", "Wakil Tahun 5"),
        (5, 25, "Ahli Jawatankuasa", "2026/2027", "Wakil Tahun 4"),

        # BSMM (Org ID 6)
        (6, 6, "Pengerusi", "2026/2027", "Pengerusi BSMM"),
        (6, 12, "Naib Pengerusi", "2026/2027", "Naib Pengerusi"),
        (6, 18, "Setiausaha", "2026/2027", "Setiausaha"),
        (6, 26, "Bendahari", "2026/2027", "Bendahari"),

        # Bola Sepak (Org ID 17)
        (17, 1, "Ketua Rumah / Ketua Pasukan", "2026/2027", "Kapten Pasukan Sekolah"),
        (17, 9, "Penolong Ketua", "2026/2027", "Penolong Kapten"),
        (17, 7, "Setiausaha", "2026/2027", "Setiausaha Pasukan"),
        (17, 11, "Bendahari", "2026/2027", "Bendahari Pasukan"),

        # Bola Jaring (Org ID 16)
        (16, 2, "Ketua Rumah / Ketua Pasukan", "2026/2027", "Kapten Pasukan Bola Jaring"),
        (16, 4, "Penolong Ketua", "2026/2027", "Penolong Kapten"),
        (16, 6, "Setiausaha", "2026/2027", "Setiausaha Pasukan"),
        (16, 10, "Bendahari", "2026/2027", "Bendahari"),

        # STEM & Robotik (Org ID 12)
        (12, 3, "Pengerusi", "2026/2027", "Pengerusi Kelab STEM"),
        (12, 1, "Naib Pengerusi", "2026/2027", "Naib Pengerusi"),
        (12, 9, "Setiausaha", "2026/2027", "Setiausaha Kelab"),
        (12, 11, "Bendahari", "2026/2027", "Bendahari Kelab"),

        # Rumah Bendahara (Org ID 1)
        (1, 1, "Ketua Rumah / Ketua Pasukan", "2026/2027", "Ketua Rumah Merah"),
        (1, 5, "Penolong Ketua", "2026/2027", "Penolong Ketua Rumah Merah"),
        (1, 9, "Setiausaha", "2026/2027", "Setiausaha Rumah"),
        (1, 21, "Bendahari", "2026/2027", "Bendahari Rumah")
    ]
    cursor.executemany("""
    INSERT INTO student_committees (organization_id, student_id, position, academic_year, notes)
    VALUES (?, ?, ?, ?, ?)
    """, committees_data)

    # 8. Attendance Sessions & Records
    cursor.execute("""
    INSERT INTO attendance_sessions (
        organization_id, session_date, start_time, end_time, venue,
        activity_title, advisor_teacher, academic_year,
        total_enrolled, total_present, total_absent, total_late, total_excused,
        notes, created_by
    ) VALUES (
        5, '2026-08-12', '14:00', '16:00', 'Dewan Terbuka',
        'Perjumpaan Mingguan 1: Latihan Kawad Kaki Asas & Ikatan Buku Sila',
        'Cikgu Norhafizah binti Ismail', '2026/2027',
        9, 9, 0, 0, 0,
        'Semua ahli hadir tepat pada masanya dengan pakaian seragam lengkap.', 'guru_penasihat'
    )
    """)
    s1_id = cursor.lastrowid
    for s_id in [1, 5, 7, 11, 15, 19, 21, 25, 29]:
        cursor.execute("INSERT OR IGNORE INTO attendance_records (session_id, student_id, status, remarks) VALUES (?, ?, 'Hadir', 'Pakaian seragam lengkap')", (s1_id, s_id))

    cursor.execute("""
    INSERT INTO attendance_sessions (
        organization_id, session_date, start_time, end_time, venue,
        activity_title, advisor_teacher, academic_year,
        total_enrolled, total_present, total_absent, total_late, total_excused,
        notes, created_by
    ) VALUES (
        17, '2026-08-11', '16:30', '18:00', 'Padang Bola Sepak Utama',
        'Latihan Kemahiran Sepakan & Kawalan Bola',
        'En. Shahril bin Mansor', '2026/2027',
        7, 6, 1, 0, 0,
        'Latihan intensif persediaan perlawanan persahabatan.', 'admin'
    )
    """)
    s2_id = cursor.lastrowid
    for s_id in [1, 7, 9, 11, 17, 21, 27]:
        st_status = "Tidak Hadir" if s_id == 27 else "Hadir"
        st_remark = "Demam (Surat cuti sakit)" if s_id == 27 else "Cergas dan berdisiplin"
        cursor.execute("INSERT OR IGNORE INTO attendance_records (session_id, student_id, status, remarks) VALUES (?, ?, ?, ?)", (s2_id, s_id, st_status, st_remark))

    # 9. Weekly Activities & Reports
    activities_data = [
        (
            5, '2026-08-12', '14:00', '16:00', 'Dewan Terbuka',
            'Perjumpaan Mingguan 1: Latihan Kawad Kaki & Asas Ikatan Tali',
            '1. Murid dapat melakukan pergerakan kawad kaki statik dengan betul.\n2. Murid dapat mengikat simpulan buku sila dan bunga geti.',
            '1. Nyanyian Lagu Negaraku, Lagu Pengakap dan bacaan Persetiaan Pengakap.\n2. Latihan kawad kaki statik dibimbing oleh guru penasihat dan ketua patrol.\n3. Praktikal ikatan tali secara berpasangan.\n4. Ujian amali ikatan dan sesi refleksi.',
            'Cikgu Norhafizah binti Ismail, En. Mohd Faizal bin Hassan',
            9,
            'Murid menunjukkan minat yang sangat tinggi dan berjaya menguasai ikatan asas dalam masa yang ditetapkan.',
            'Menambah bilangan tali pengakap untuk sesi amali seterusnya supaya setiap murid mempunyai peralatan sendiri.',
            'Disahkan',
            'Laporan sangat lengkap dan aktiviti menepati takwim tahunan unit pengakap.',
            'guru_penasihat', '2026-08-12 16:30:00',
            'penyelaras_uniform', '2026-08-13 09:15:00',
            'gpk_koko', '2026-08-14 11:00:00'
        ),
        (
            17, '2026-08-11', '16:30', '18:00', 'Padang Bola Sepak Utama',
            'Latihan Kemahiran Asas Sepakan & Kawalan Bola',
            '1. Menguasai kemahiran hantaran leret menggunakan bahagian dalam kaki.\n2. Meningkatkan tahap kecergasan kardiovaskular.',
            '1. Memanaskan badan dan regangan otot dinamik.\n2. Latih tubi hantaran 2 sentuhan secara berpasangan.\n3. Mini game 5 lawan 5 bagi mengaplikasi taktikal hantaran ruang.\n4. Menyejukkan badan dan perbincangan taktikal.',
            'En. Shahril bin Mansor, En. Zulkifli bin Daud',
            7,
            'Tahap stamina murid semakin meningkat berbanding minggu lalu.',
            'Perlu perbanyakkan kon dan bola saiz 4 untuk latihan hantaran.',
            'Disemak',
            'Disemak oleh penyelaras sukan. Menunggu pengesahan GPK Koko.',
            'admin', '2026-08-11 18:30:00',
            'penyelaras_uniform', '2026-08-12 10:00:00',
            None, None
        ),
        (
            12, '2026-08-12', '15:30', '17:00', 'Makmal STEM',
            'Pengenalan Mikropengawal Micro:bit & Pengekodan Blok',
            '1. Memahami fungsi sensor dan paparan LED pada papan Micro:bit.\n2. Membina animasi ringkas menggunakan MakeCode.',
            '1. Penerangan komponen perkakasan Micro:bit.\n2. Bengkel pengaturcaraan MakeCode.\n3. Memuat naik kod ke perkakasan dan ujian kefungsian.',
            'Pn. Hasnah binti Salleh, En. Mohd Faizal bin Hassan',
            8,
            'Murid sangat teruja melihat kod yang diprogramkan berfungsi pada perkakasan sebenar.',
            'Mencadangkan pembelian bateri tambahan untuk modul projek bergerak.',
            'Dihantar',
            None,
            'su_koko', '2026-08-12 17:30:00',
            None, None,
            None, None
        ),
        (
            16, '2026-08-13', '16:30', '18:00', 'Gelanggang Bola Jaring',
            'Latihan Posisi Penjaring (GS) dan Penyerang Gol (GA)',
            '1. Melatih teknik tolakan bola ke dalam jaring dari pelbagai sudut.\n2. Memperkemas pergerakan stepping dalam bulatan gol.',
            '1. Lari ulang-alik dan regangan khusus sendi bahu.\n2. Latihan balingan tepat ke sasaran 50 cubaan setiap pemain.\n3. Simulasi tekanan pertahanan oleh pemain GD/GK.',
            'Pn. Faridah binti Kassim, Cikgu Norhafizah binti Ismail',
            8,
            'Ketepatan jaringan mencapai 70% dalam kalangan pemain utama.',
            'Membaiki jaring gol yang sedikit longgar di tiang utama.',
            'Draf',
            None,
            'guru_penasihat', '2026-08-13 18:30:00',
            None, None,
            None, None
        )
    ]

    for act in activities_data:
        cursor.execute("""
        INSERT INTO weekly_activities (
            organization_id, activity_date, start_time, end_time, venue,
            title, objectives, description_rundown, teachers_involved,
            attendees_count, reflection, suggestions, status,
            review_remarks, submitted_by, submitted_at,
            reviewed_by, reviewed_at, approved_by, approved_at,
            academic_year
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, '2026/2027')
        """, act)

    # 10. Permission Letters
    cursor.execute("""
    INSERT INTO permission_letters (
        id, letter_no, program_name, destination_venue,
        start_datetime, end_datetime, organizer, transportation,
        accompanying_teachers, fee_amount, contact_person, contact_phone,
        special_instructions, academic_year, created_by
    ) VALUES (
        1,
        'SKSD/KOKO/2026/08-01',
        'Kejohanan Bola Sepak Bawah 12 Tahun MSSD Larut Matang & Selama',
        'Padang SMK Dato Haji Hussein, Selama',
        '2026-08-25 07:30',
        '2026-08-25 17:00',
        'Pejabat Pendidikan Daerah Larut Matang & Selama (PPD LMS)',
        'Bas Sekolah Khas (Dibiayai Pihak Sekolah)',
        'En. Shahril bin Mansor (019-5551110), En. Zulkifli bin Daud (019-5551106)',
        0.0,
        'En. Mohd Faizal bin Hassan',
        '019-5551103',
        'Murid wajib membawa kasut bola, pelindung kaki (shin guard) dan pakaian sukan lengkap.',
        '2026/2027',
        'su_koko'
    )
    """)
    let_id = cursor.lastrowid
    letter_students = [
        (let_id, 1, "Dibenarkan", "Penjaga membenarkan dan akan ambil murid di sekolah jam 5:30 petang", "2026-08-18"),
        (let_id, 7, "Dibenarkan", "Ibu bapa telah menandatangani surat kebenaran", "2026-08-18"),
        (let_id, 9, "Dibenarkan", "Dibenarkan", "2026-08-19"),
        (let_id, 11, "Diterima", "Menunggu pengesahan tandatangan bapa", "2026-08-19"),
        (let_id, 17, "Dibenarkan", "Dibenarkan menyertai kontinjen sekolah", "2026-08-19"),
        (let_id, 21, "Belum Diedarkan", None, None),
    ]
    cursor.executemany("""
    INSERT INTO permission_letter_students (letter_id, student_id, permission_status, parent_notes, response_date)
    VALUES (?, ?, ?, ?, ?)
    """, letter_students)

    # 11. External Participations & PAJSK
    external_events = [
        (
            1,
            'Kejohanan Catur Majlis Sukan Sekolah Daerah (MSSD) Selama',
            '2026-07-15',
            'Dewan SMK Selama, Perak',
            'PPD Larut Matang & Selama',
            'Sukan & Permainan',
            'Daerah',
            21,
            'Penyertaan cemerlang wakil sekolah dalam kategori Bawah 12 Tahun.',
            'su_koko',
            'Pn. Siti Zaleha binti Mohd Nor',
            '2026-07-20 10:00:00',
            'Disahkan'
        ),
        (
            2,
            'Pertandingan Inovasi STEM & Robotik Sekolah Rendah Peringkat Negeri Perak',
            '2026-08-05',
            'Pusat Sains Negara Cawangan Wilayah Utara / UPSI',
            'Jabatan Pendidikan Negeri Perak (JPN Perak)',
            'Kelab & Persatuan',
            'Negeri',
            12,
            'Mewakili daerah ke peringkat negeri dalam projek Inovasi Pintar Pengairan Automatik.',
            'su_koko',
            'Pn. Siti Zaleha binti Mohd Nor',
            '2026-08-10 14:30:00',
            'Disahkan'
        ),
        (
            3,
            'Perkhemahan Ujian Lencana Keris Emas Pengakap Kanak-kanak Peringkat Kebangsaan',
            '2026-06-20',
            'Kem Bina Negara Ulu Kenas, Kuala Kangsar, Perak',
            'Persekutuan Pengakap Malaysia & KPM',
            'Unit Beruniform',
            'Kebangsaan',
            5,
            'Ujian kelayakan penerima Rambu Pengakap Kanak-kanak Kebangsaan.',
            'guru_penasihat',
            'En. Mohd Faizal bin Hassan',
            '2026-06-25 09:00:00',
            'Disahkan'
        )
    ]

    for ev in external_events:
        cursor.execute("""
        INSERT INTO external_participations (
            id, program_name, event_date, venue, organizer,
            activity_category, participation_level, represented_org_id,
            academic_year, notes, created_by, verified_by, verified_at, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, '2026/2027', ?, ?, ?, ?, ?)
        """, ev)

    external_students = [
        # Event 1: Catur Daerah
        (1, 8, "Peserta", "Johan", 17.0, "Juara Kategori Perempuan B12 Daerah"),
        (1, 14, "Peserta", "Tempat Ketiga", 14.0, "Tempat Ke-3 Individu"),
        (1, 4, "Peserta", "Penyertaan", 11.0, "Peringkat suku akhir"),

        # Event 2: STEM Negeri
        (2, 3, "Peserta", "Naib Johan", 18.0, "Pingat Perak Inovasi STEM Negeri Perak"),
        (2, 1, "Peserta", "Naib Johan", 18.0, "Pingat Perak Inovasi STEM Negeri Perak"),
        (2, 9, "Peserta", "Naib Johan", 18.0, "Pingat Perak Inovasi STEM Negeri Perak"),

        # Event 3: Pengakap Kebangsaan
        (3, 1, "Peserta", "Johan", 20.0, "Penerima Rambu Pengakap Emas Kebangsaan"),
        (3, 7, "Peserta", "Penyertaan", 16.0, "Berjaya menamatkan semua ujian lencana")
    ]
    cursor.executemany("""
    INSERT INTO external_participation_students (
        participation_id, student_id, role, achievement, pajsk_score, remarks
    ) VALUES (?, ?, ?, ?, ?, ?)
    """, external_students)

    # 12. Audit Logs
    cursor.execute("""
    INSERT INTO audit_logs (
        user_id, username, user_role, action, module, description, target_id
    ) VALUES (
        3, 'su_koko', 'Setiausaha Kokurikulum', 'VERIFY', 'PAJSK',
        'Mengesahkan rekod skor PAJSK Pertandingan Inovasi STEM Peringkat Negeri Perak', 2
    )
    """)

    conn.commit()
    conn.close()
    print("Selesai menyemai data demo kokurikulum!")

if __name__ == "__main__":
    seed_demo_data(force=True)
