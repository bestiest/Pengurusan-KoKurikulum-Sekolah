import io
import re
import datetime
import sqlite3
import openpyxl

def clean_str(val):
    if val is None:
        return None
    s = str(val).strip()
    if not s or s.lower() in ("none", "null", "nan", "-", "tiada"):
        return None
    return s

def clean_ic(val):
    if val is None:
        return None
    if isinstance(val, (int, float)):
        val = f"{int(val)}"
    s = str(val).strip().replace("-", "").replace(" ", "").replace(".", "")
    if len(s) == 11 and s.isdigit():
        s = "0" + s
    return s.upper()

def clean_gender(val, ic_number=None):
    if val:
        v = str(val).strip().lower()
        if v.startswith(("l", "m")):
            return "Lelaki"
        if v.startswith(("p", "f", "w")):
            return "Perempuan"
    if ic_number and len(ic_number) == 12 and ic_number.isdigit():
        last_digit = int(ic_number[-1])
        return "Lelaki" if last_digit % 2 != 0 else "Perempuan"
    return "Lelaki"

def clean_birth_date(val, ic_number=None):
    if isinstance(val, (datetime.date, datetime.datetime)):
        return val.strftime("%Y-%m-%d")
    if val:
        s = str(val).strip().split(" ")[0]
        # YYYY-MM-DD
        m = re.match(r"^(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})$", s)
        if m:
            y, mo, d = m.groups()
            return f"{int(y):04d}-{int(mo):02d}-{int(d):02d}"
        # DD/MM/YYYY or DD-MM-YYYY
        m2 = re.match(r"^(\d{1,2})[-/.](\d{1,2})[-/.](\d{4})$", s)
        if m2:
            d, mo, y = m2.groups()
            return f"{int(y):04d}-{int(mo):02d}-{int(d):02d}"
    
    # Fallback from IC
    if ic_number and len(ic_number) == 12 and ic_number.isdigit():
        yy = int(ic_number[:2])
        mo = int(ic_number[2:4])
        dd = int(ic_number[4:6])
        if 1 <= mo <= 12 and 1 <= dd <= 31:
            year = 2000 + yy if yy < 30 else 1900 + yy
            return f"{year:04d}-{mo:02d}-{dd:02d}"
    return None

def clean_grade(val, class_name=None):
    if val is not None:
        try:
            v_int = int(float(str(val).strip()))
            if 1 <= v_int <= 6:
                return v_int
        except Exception:
            pass
        m = re.search(r"[1-6]", str(val))
        if m:
            return int(m.group(0))
    if class_name:
        m = re.search(r"[1-6]", str(class_name))
        if m:
            return int(m.group(0))
    return 1

def build_org_lookup(org_rows):
    lookup = {
        'Rumah Sukan': {},
        'Unit Beruniform': {},
        'Kelab & Persatuan': {},
        'Sukan & Permainan': {},
        'all': {}
    }
    for r in org_rows:
        org_id = r["id"]
        name = r["name"].strip()
        cat = r["category"]
        
        lookup['all'][name.lower()] = org_id
        if cat in lookup:
            lookup[cat][name.lower()] = org_id
            
        clean = re.sub(r'[^a-zA-Z0-9\s]', ' ', name).lower().split()
        for word in clean:
            if len(word) > 2 and word not in ('rumah', 'kelab', 'persatuan', 'unit', 'badan', 'dan'):
                if cat in lookup:
                    lookup[cat].setdefault(word, org_id)
                lookup['all'].setdefault(word, org_id)
                
    return lookup

def find_org_id(query_str, category, lookup):
    if not query_str:
        return None
    q = str(query_str).strip().lower()
    cat_dict = lookup.get(category, {})
    
    if q in cat_dict:
        return cat_dict[q]
    if q in lookup['all']:
        return lookup['all'][q]
        
    for name, org_id in cat_dict.items():
        if q in name or name in q:
            return org_id
            
    q_words = [w for w in re.sub(r'[^a-zA-Z0-9\s]', ' ', q).split() if len(w) > 2]
    for w in q_words:
        if w in cat_dict:
            return cat_dict[w]
    return None

def detect_header_and_map(rows):
    """
    Scans first 15 rows to find the actual header row.
    Returns: (header_row_index, field_map)
    """
    best_row_idx = 0
    best_score = -1
    best_map = {}

    for r_idx in range(min(15, len(rows))):
        row = rows[r_idx]
        if not row or not any(row):
            continue
        
        field_map = {}
        score = 0
        for c_idx, cell in enumerate(row):
            if cell is None:
                continue
            c = re.sub(r'[^a-z0-9]', '', str(cell).lower())
            if not c:
                continue
            
            if any(k in c for k in ['penjaga', 'bapa', 'ibu', 'guardian']):
                if any(k in c for k in ['tel', 'phone', 'bimbit', 'nombor', 'telefon', 'hp', 'notel']):
                    if 'guardian_phone' not in field_map:
                        field_map['guardian_phone'] = c_idx
                        score += 2
                else:
                    if 'guardian_name' not in field_map:
                        field_map['guardian_name'] = c_idx
                        score += 2
            elif any(k in c for k in ['nokp', 'mykid', 'kadpengenalan', 'suratberanak', 'sijillahir', 'icnumber', 'dokumen']) or c in ('ic', 'kp'):
                if 'ic_number' not in field_map:
                    field_map['ic_number'] = c_idx
                    score += 5
            elif 'nama' in c or 'name' in c or 'murid' in c or 'pelajar' in c:
                if 'kelas' in c:
                    if 'class_name' not in field_map:
                        field_map['class_name'] = c_idx
                        score += 2
                else:
                    if 'full_name' not in field_map:
                        field_map['full_name'] = c_idx
                        score += 5
            elif any(k in c for k in ['tarikh', 'lahir', 'dob', 'birth']):
                if 'birth_date' not in field_map:
                    field_map['birth_date'] = c_idx
                    score += 2
            elif any(k in c for k in ['jantina', 'gender', 'sex']):
                if 'gender' not in field_map:
                    field_map['gender'] = c_idx
                    score += 3
            elif any(k in c for k in ['tingkatan', 'tahun', 'darjah', 'grade', 'year']):
                if 'kelas' in c:
                    if 'class_name' not in field_map:
                        field_map['class_name'] = c_idx
                        score += 2
                else:
                    if 'grade' not in field_map:
                        field_map['grade'] = c_idx
                        score += 2
            elif any(k in c for k in ['kelas', 'class']):
                if 'class_name' not in field_map:
                    field_map['class_name'] = c_idx
                    score += 2
            elif any(k in c for k in ['alamat', 'address']):
                if 'address' not in field_map:
                    field_map['address'] = c_idx
                    score += 1
            elif any(k in c for k in ['kesihatan', 'alahan', 'health', 'penyakit']):
                if 'health_info' not in field_map:
                    field_map['health_info'] = c_idx
                    score += 1
            elif any(k in c for k in ['rumah', 'rumahsukan']):
                if 'sport_house' not in field_map:
                    field_map['sport_house'] = c_idx
                    score += 2
            elif any(k in c for k in ['uniform', 'badanberuniform', 'unitberuniform']):
                if 'uniform_unit' not in field_map:
                    field_map['uniform_unit'] = c_idx
                    score += 2
            elif any(k in c for k in ['kelab', 'persatuan']):
                if 'club_society' not in field_map:
                    field_map['club_society'] = c_idx
                    score += 2
            elif any(k in c for k in ['sukan', 'permainan']):
                if 'sports_game' not in field_map:
                    field_map['sports_game'] = c_idx
                    score += 2

        if score > best_score:
            best_score = score
            best_row_idx = r_idx
            best_map = field_map

    # If score is too low or missing both name and ic, check if fallback needed
    if best_score < 4 or ('full_name' not in best_map and 'ic_number' not in best_map):
        # Fallback to positional mapping
        best_row_idx = 0
        first_row = rows[0] if rows else []
        offset = 1 if (len(first_row) > 1 and str(first_row[0]).strip().lower() in ('bil', 'no', '1')) else 0
        best_map = {
            'full_name': offset + 0,
            'ic_number': offset + 1,
            'birth_date': offset + 2,
            'gender': offset + 3,
            'grade': offset + 4,
            'class_name': offset + 5,
            'guardian_name': offset + 6,
            'guardian_phone': offset + 7,
            'address': offset + 8,
            'health_info': offset + 9,
            'sport_house': offset + 10,
            'uniform_unit': offset + 11,
            'club_society': offset + 12,
            'sports_game': offset + 13
        }

    return best_row_idx, best_map

def process_student_import_rows(rows, conn, cursor, org_lookup):
    if not rows or len(rows) < 2:
        return 0, 0, ["Fail tidak mempunyai data murid."]

    header_row_idx, col_map = detect_header_and_map(rows)
    print(f"Detected Header at row {header_row_idx}: {col_map}")

    imported_count = 0
    updated_count = 0
    errors = []

    # Process all rows after the detected header row
    for row_idx, r in enumerate(rows[header_row_idx + 1:], start=header_row_idx + 2):
        if not r or not any(r):
            continue
        
        # Check if entire row is just whitespace or header repetition
        raw_vals = [str(c).strip() for c in r if c is not None and str(c).strip()]
        if not raw_vals:
            continue
        if any(h in raw_vals[0].upper() for h in ['NAMA PENUH', 'NAMA MURID', 'BIL.', 'KEMENTERIAN']):
            continue

        try:
            def get_col(field_name):
                idx = col_map.get(field_name)
                if idx is not None and idx < len(r):
                    return r[idx]
                return None

            raw_name = get_col('full_name')
            raw_ic = get_col('ic_number')

            full_name = clean_str(raw_name)
            if full_name:
                full_name = " ".join(full_name.split()).upper()

            ic_number = clean_ic(raw_ic)

            # If ic_number or full_name is missing, try detecting if swapped or in adjacent column
            if not full_name and raw_ic and not str(raw_ic).replace("-", "").isdigit():
                full_name = str(raw_ic).strip().upper()
                ic_number = clean_ic(raw_name)

            if not full_name or not ic_number:
                errors.append(f"Baris {row_idx}: Nama ({full_name or 'Kosong'}) atau No KP ({ic_number or 'Kosong'}) tidak lengkap.")
                continue

            # Don't import if name is header text or Bil number
            if full_name.isdigit() or full_name in ("NAMA", "NAMA MURID", "NAMA PENUH"):
                continue

            gender = clean_gender(get_col('gender'), ic_number)
            class_name = clean_str(get_col('class_name'))
            grade = clean_grade(get_col('grade'), class_name)
            if not class_name:
                class_name = f"{grade} Cemerlang"

            birth_date = clean_birth_date(get_col('birth_date'), ic_number)
            guardian_name = clean_str(get_col('guardian_name'))
            guardian_phone = clean_str(get_col('guardian_phone'))
            if guardian_phone:
                guardian_phone = guardian_phone.replace(" ", "").replace("-", "")
            address = clean_str(get_col('address'))
            health_info = clean_str(get_col('health_info')) or "Tiada"

            sport_house_id = find_org_id(get_col('sport_house'), 'Rumah Sukan', org_lookup)
            uniform_unit_id = find_org_id(get_col('uniform_unit'), 'Unit Beruniform', org_lookup)
            club_society_id = find_org_id(get_col('club_society'), 'Kelab & Persatuan', org_lookup)
            sports_game_id = find_org_id(get_col('sports_game'), 'Sukan & Permainan', org_lookup)

            # Insert or update
            existing = conn.execute("SELECT id FROM students WHERE ic_number = ?", (ic_number,)).fetchone()
            if existing:
                st_id = existing["id"]
                cursor.execute("""
                UPDATE students SET
                    full_name = ?, birth_date = COALESCE(?, birth_date), gender = ?, grade = ?, class_name = ?,
                    guardian_name = COALESCE(?, guardian_name), guardian_phone = COALESCE(?, guardian_phone),
                    address = COALESCE(?, address), health_info = COALESCE(?, health_info),
                    sport_house_id = COALESCE(?, sport_house_id),
                    uniform_unit_id = COALESCE(?, uniform_unit_id),
                    club_society_id = COALESCE(?, club_society_id),
                    sports_game_id = COALESCE(?, sports_game_id)
                WHERE id = ?
                """, (
                    full_name, birth_date, gender, grade, class_name,
                    guardian_name, guardian_phone, address, health_info,
                    sport_house_id, uniform_unit_id, club_society_id, sports_game_id, st_id
                ))
                updated_count += 1
            else:
                cursor.execute("""
                INSERT INTO students (
                    full_name, ic_number, birth_date, gender, grade, class_name,
                    guardian_name, guardian_phone, address, health_info,
                    sport_house_id, uniform_unit_id, club_society_id, sports_game_id,
                    status, academic_year
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Aktif', '2026/2027')
                """, (
                    full_name, ic_number, birth_date, gender, grade, class_name,
                    guardian_name, guardian_phone, address, health_info,
                    sport_house_id, uniform_unit_id, club_society_id, sports_game_id
                ))
                st_id = cursor.lastrowid
                imported_count += 1

            # Register memberships
            for org_id in [sport_house_id, uniform_unit_id, club_society_id, sports_game_id]:
                if org_id:
                    cursor.execute("""
                    INSERT OR IGNORE INTO organization_members (organization_id, student_id, academic_year)
                    VALUES (?, ?, '2026/2027')
                    """, (org_id, st_id))

        except Exception as ex:
            errors.append(f"Baris {row_idx}: {str(ex)}")

    return imported_count, updated_count, errors

# Test execution with in-memory DB
test_conn = sqlite3.connect(":memory:")
test_conn.row_factory = sqlite3.Row
test_cur = test_conn.cursor()
test_cur.execute("""
CREATE TABLE students (
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
    health_info TEXT DEFAULT 'Tiada',
    sport_house_id INTEGER,
    uniform_unit_id INTEGER,
    club_society_id INTEGER,
    sports_game_id INTEGER,
    status TEXT DEFAULT 'Aktif',
    academic_year TEXT DEFAULT '2026/2027',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")
test_cur.execute("""
CREATE TABLE organization_members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    organization_id INTEGER NOT NULL,
    student_id INTEGER NOT NULL,
    academic_year TEXT DEFAULT '2026/2027',
    joined_date TEXT DEFAULT CURRENT_DATE,
    status TEXT DEFAULT 'Aktif',
    UNIQUE(organization_id, student_id, academic_year)
)
""")

# Mock orgs
mock_orgs = [
    {"id": 1, "name": "Rumah Bendahara (Merah)", "category": "Rumah Sukan"},
    {"id": 5, "name": "Persekutuan Pengakap Malaysia (Pengakap)", "category": "Unit Beruniform"},
    {"id": 10, "name": "Persatuan Bahasa Melayu", "category": "Kelab & Persatuan"},
    {"id": 16, "name": "Kelab Bola Jaring", "category": "Sukan & Permainan"}
]
org_lookup = build_org_lookup(mock_orgs)

# Case A: Template format
rows_a = [
    ["Nama Penuh", "No KP / MyKid", "Tarikh Lahir (YYYY-MM-DD)", "Jantina (Lelaki/Perempuan)", "Tahun (1-6)", "Nama Kelas", "Nama Penjaga", "No Telefon Penjaga", "Alamat", "Maklumat Kesihatan", "Rumah Sukan", "Unit Beruniform", "Kelab Persatuan", "Sukan Permainan"],
    ["ALI BIN AHMAD", "150101081111", "2015-01-01", "Lelaki", 5, "5 Cemerlang", "Ahmad", "0123456789", "Alamat 1", "Tiada", "Merah", "Pengakap", "Bahasa Melayu", "Bola Jaring"],
    ["FATIMAH BINTI OMAR", "150202082222", "2015-02-02", "Perempuan", 5, "5 Cemerlang", "Omar", "0198765432", "Alamat 2", "Tiada", "Bendahara", "Pengakap", "Bahasa Melayu", "Bola Jaring"]
]
imp, upd, err = process_student_import_rows(rows_a, test_conn, test_cur, org_lookup)
print(f"Test A (Template): imported={imp}, updated={upd}, errors={err}")

# Case B: APDM format with title rows, Bil column, and dirty data
rows_b = [
    ["KEMENTERIAN PENDIDIKAN MALAYSIA"],
    ["SK SUNGAI DENDANG - SENARAI MURID 2026"],
    ["Bil", "Nama Murid", "No. Kad Pengenalan / MyKid", "Jantina", "Tingkatan / Kelas", "Tarikh Lahir", "Nama Bapa / Penjaga", "No. Tel Bimbit Penjaga"],
    [1, "ZAINAL BIN ABIDIN", "150303-08-3333", "L", "5 Cemerlang", "03/03/2015", "Abidin", "017-1234567"],
    [2, "SITI AISYAH", 150404084444.0, "P", "5 Cemerlang", None, "Hamid", "018-9998877"] # Float IC and auto birth date
]
imp, upd, err = process_student_import_rows(rows_b, test_conn, test_cur, org_lookup)
print(f"Test B (APDM with Bil & Banner): imported={imp}, updated={upd}, errors={err}")

# Case C: Update existing
rows_c = [
    ["Nama", "No KP", "Tahun", "Kelas"],
    ["ALI BIN AHMAD (UPDATED)", "150101081111", 6, "6 Cemerlang"]
]
imp, upd, err = process_student_import_rows(rows_c, test_conn, test_cur, org_lookup)
print(f"Test C (Update): imported={imp}, updated={upd}, errors={err}")

# Print final DB students
students = test_conn.execute("SELECT id, full_name, ic_number, birth_date, gender, grade, class_name, sport_house_id FROM students").fetchall()
print(f"\nFinal DB Students ({len(students)}):")
for s in students:
    print(dict(s))
