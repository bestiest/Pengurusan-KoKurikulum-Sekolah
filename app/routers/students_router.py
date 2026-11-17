import io
import csv
import re
import datetime
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Response, Query
from fastapi.responses import StreamingResponse
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from app.database import get_db_connection, log_audit
from app.auth import get_current_user, require_roles, require_deletion_roles
from app.models import StudentCreate, StudentUpdate, BulkAssignOrg

router = APIRouter(prefix="/api/students", tags=["Pengurusan Murid"])

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
    
    # Fallback to IC
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

    # If score is too low or missing both name and ic, fallback to positional mapping
    if best_score < 4 or ('full_name' not in best_map and 'ic_number' not in best_map):
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

def process_student_rows(rows, conn, cursor, org_lookup):
    if not rows or len(rows) < 2:
        return 0, 0, ["Fail tidak mempunyai data murid."]

    header_row_idx, col_map = detect_header_and_map(rows)

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
        if any(h in raw_vals[0].upper() for h in ['NAMA PENUH', 'NAMA MURID', 'KEMENTERIAN PENDIDIKAN', 'SENARAI NAMA']):
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

            # Check if columns might have been inverted
            if not full_name and raw_ic and not str(raw_ic).replace("-", "").isdigit():
                full_name = str(raw_ic).strip().upper()
                ic_number = clean_ic(raw_name)

            if not full_name or not ic_number:
                errors.append(f"Baris {row_idx}: Nama Penuh atau No KP / MyKid kosong atau tidak lengkap.")
                continue

            # Don't import if name is header text or Bil number
            if full_name.isdigit() or full_name in ("NAMA", "NAMA MURID", "NAMA PENUH", "BIL", "BIL."):
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
            errors.append(f"Baris {row_idx}: Ralat memproses - {str(ex)}")

    return imported_count, updated_count, errors

@router.get("")
async def list_students(
    search: Optional[str] = None,
    grade: Optional[int] = None,
    class_name: Optional[str] = None,
    gender: Optional[str] = None,
    status: Optional[str] = None,
    sport_house_id: Optional[int] = None,
    uniform_unit_id: Optional[int] = None,
    club_society_id: Optional[int] = None,
    sports_game_id: Optional[int] = None,
    category: Optional[str] = None,
    user: Dict[str, Any] = Depends(get_current_user)
):
    conn = get_db_connection()
    query = """
    SELECT 
        s.*,
        rh.name as sport_house_name,
        ub.name as uniform_unit_name,
        kp.name as club_society_name,
        sp.name as sports_game_name
    FROM students s
    LEFT JOIN organizations rh ON s.sport_house_id = rh.id
    LEFT JOIN organizations ub ON s.uniform_unit_id = ub.id
    LEFT JOIN organizations kp ON s.club_society_id = kp.id
    LEFT JOIN organizations sp ON s.sports_game_id = sp.id
    WHERE 1=1
    """
    params = []

    if search:
        search_term = f"%{search.strip()}%"
        query += " AND (s.full_name LIKE ? OR s.ic_number LIKE ? OR s.guardian_name LIKE ? OR s.guardian_phone LIKE ?)"
        params.extend([search_term, search_term, search_term, search_term])

    if grade:
        query += " AND s.grade = ?"
        params.append(grade)

    if class_name:
        query += " AND s.class_name = ?"
        params.append(class_name)

    if gender:
        query += " AND s.gender = ?"
        params.append(gender)

    if status:
        query += " AND s.status = ?"
        params.append(status)

    if sport_house_id:
        query += " AND s.sport_house_id = ?"
        params.append(sport_house_id)

    if uniform_unit_id:
        query += " AND s.uniform_unit_id = ?"
        params.append(uniform_unit_id)

    if club_society_id:
        query += " AND s.club_society_id = ?"
        params.append(club_society_id)

    if sports_game_id:
        query += " AND s.sports_game_id = ?"
        params.append(sports_game_id)

    if category and not (sport_house_id or uniform_unit_id or club_society_id or sports_game_id):
        if category == "Rumah Sukan":
            query += " AND s.sport_house_id IS NOT NULL"
        elif category == "Unit Beruniform":
            query += " AND s.uniform_unit_id IS NOT NULL"
        elif category in ("Kelab & Persatuan", "Kelab dan Persatuan"):
            query += " AND s.club_society_id IS NOT NULL"
        elif category in ("Sukan & Permainan", "Sukan dan Permainan"):
            query += " AND s.sports_game_id IS NOT NULL"

    query += " ORDER BY s.grade ASC, s.class_name ASC, s.full_name ASC"
    rows = conn.execute(query, tuple(params)).fetchall()
    conn.close()

    return [dict(r) for r in rows]

@router.get("/template/excel")
async def download_student_template():
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Templat_Import_Murid"

    # Header style
    headers = [
        "Nama Penuh", "No KP / MyKid", "Tarikh Lahir (YYYY-MM-DD)", "Jantina (Lelaki/Perempuan)",
        "Tahun (1-6)", "Nama Kelas", "Nama Penjaga", "No Telefon Penjaga",
        "Alamat", "Maklumat Kesihatan", "Rumah Sukan", "Unit Beruniform",
        "Kelab Persatuan", "Sukan Permainan"
    ]

    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
    center_align = Alignment(horizontal="center", vertical="center", wrap_text=True)

    for col_num, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_num, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center_align

    # Sample rows
    sample_data = [
        ["MUHAMMAD DANISH IRFAN BIN ZULKIFLI", "150101089991", "2015-01-01", "Lelaki", 5, "5 Cemerlang", "Zulkifli bin Daud", "012-5881234", "No 12, Kg Sungai Dendang, Selama", "Tiada", "Rumah Bendahara (Merah)", "Persekutuan Pengakap Malaysia (Pengakap)", "Kelab STEM & Robotik", "Kelab Bola Sepak"],
        ["NUR AISYAH HUMAIRA BINTI AHMAD", "150202089992", "2015-02-02", "Perempuan", 5, "5 Cemerlang", "Ahmad bin Abdullah", "013-4885678", "No 45, Lorong Mawar, Selama", "Alahan Kacang", "Rumah Temenggong (Kuning)", "Pergerakan Pandu Puteri Tunas (PPT)", "Persatuan Bahasa Melayu", "Kelab Bola Jaring"]
    ]

    for row_num, row_data in enumerate(sample_data, 2):
        for col_num, val in enumerate(row_data, 1):
            ws.cell(row=row_num, column=col_num, value=val)

    # Column widths
    for col in ws.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        col_letter = openpyxl.utils.get_column_letter(col[0].column)
        ws.column_dimensions[col_letter].width = max(max_len + 4, 14)

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=Templat_Import_Murid_SKSD.xlsx"}
    )

@router.post("/import")
async def import_students(
    file: UploadFile = File(...),
    user: Dict[str, Any] = Depends(require_roles("Admin", "GPK Kokurikulum", "Setiausaha Kokurikulum"))
):
    contents = await file.read()
    filename = file.filename.lower()
    
    conn = get_db_connection()
    cursor = conn.cursor()

    # Pre-fetch organizations by name for mapping
    org_rows = conn.execute("SELECT id, name, category FROM organizations").fetchall()
    org_lookup = build_org_lookup(org_rows)

    rows = []
    if filename.endswith(".xlsx"):
        try:
            wb = openpyxl.load_workbook(io.BytesIO(contents), data_only=True)
            ws = wb.active
            rows = list(ws.iter_rows(values_only=True))
        except Exception as e:
            conn.close()
            raise HTTPException(status_code=400, detail=f"Gagal membaca fail Excel (.xlsx): {str(e)}")
    elif filename.endswith(".csv"):
        try:
            csv_text = contents.decode("utf-8-sig", errors="ignore")
            # Auto-detect delimiter
            try:
                sniffer = csv.Sniffer()
                dialect = sniffer.sniff(csv_text[:2048])
                delim = dialect.delimiter
            except Exception:
                delim = ","
            reader = csv.reader(io.StringIO(csv_text), delimiter=delim)
            rows = list(reader)
        except Exception as e:
            conn.close()
            raise HTTPException(status_code=400, detail=f"Gagal membaca fail CSV (.csv): {str(e)}")
    else:
        conn.close()
        raise HTTPException(status_code=400, detail="Format fail tidak disokong. Sila gunakan format .xlsx atau .csv.")

    imported_count, updated_count, errors = process_student_rows(rows, conn, cursor, org_lookup)
    conn.commit()
    conn.close()

    log_audit(
        user.get("id"),
        user.get("username"),
        user.get("role"),
        "IMPORT",
        "STUDENTS",
        f"Import murid pukal: {imported_count} baharu, {updated_count} dikemas kini, {len(errors)} ralat"
    )

    total_proc = imported_count + updated_count
    msg = f"Berjaya memproses: {imported_count} murid baharu didaftarkan, {updated_count} rekod murid dikemas kini!" if total_proc > 0 else "Tiada murid baharu didaftarkan atau dikemas kini."

    return {
        "status": "success",
        "total_processed": total_proc,
        "total_imported": total_proc,
        "imported_count": imported_count,
        "updated_count": updated_count,
        "errors_count": len(errors),
        "errors": errors[:25],
        "message": msg
    }

@router.get("/export/excel")
async def export_students_excel(
    ids: Optional[str] = None,
    search: Optional[str] = None,
    grade: Optional[int] = None,
    class_name: Optional[str] = None,
    gender: Optional[str] = None,
    category: Optional[str] = None,
    sport_house_id: Optional[int] = None,
    uniform_unit_id: Optional[int] = None,
    club_society_id: Optional[int] = None,
    sports_game_id: Optional[int] = None,
    user: Dict[str, Any] = Depends(get_current_user)
):
    conn = get_db_connection()
    query = """
    SELECT 
        s.*,
        rh.name as sport_house_name,
        ub.name as uniform_unit_name,
        kp.name as club_society_name,
        sp.name as sports_game_name
    FROM students s
    LEFT JOIN organizations rh ON s.sport_house_id = rh.id
    LEFT JOIN organizations ub ON s.uniform_unit_id = ub.id
    LEFT JOIN organizations kp ON s.club_society_id = kp.id
    LEFT JOIN organizations sp ON s.sports_game_id = sp.id
    WHERE 1=1
    """
    params = []
    filter_desc = "Semua Murid"
    file_suffix = "Semua"

    if ids:
        id_list = [int(x.strip()) for x in ids.split(",") if x.strip().isdigit()]
        if id_list:
            placeholders = ",".join(["?"] * len(id_list))
            query += f" AND s.id IN ({placeholders})"
            params.extend(id_list)
            filter_desc = f"{len(id_list)} Murid Terpilih"
            file_suffix = "Terpilih"
    else:
        if search:
            query += " AND (s.full_name LIKE ? OR s.ic_number LIKE ?)"
            params.extend([f"%{search}%", f"%{search}%"])
            filter_desc = f"Carian: {search}"
            file_suffix = "Carian"
        if grade:
            query += " AND s.grade = ?"
            params.append(grade)
            filter_desc = f"Tahun {grade}"
            file_suffix = f"Tahun_{grade}"
        if class_name:
            query += " AND s.class_name = ?"
            params.append(class_name)
            filter_desc = f"Kelas {class_name}"
            file_suffix = class_name.replace(" ", "_")
        if gender:
            query += " AND s.gender = ?"
            params.append(gender)
            filter_desc += f" ({gender})"
        if sport_house_id:
            query += " AND s.sport_house_id = ?"
            params.append(sport_house_id)
            h = conn.execute("SELECT name FROM organizations WHERE id = ?", (sport_house_id,)).fetchone()
            if h:
                filter_desc = f"Rumah Sukan: {h['name']}"
                file_suffix = h['name'].replace(" ", "_")
        if uniform_unit_id:
            query += " AND s.uniform_unit_id = ?"
            params.append(uniform_unit_id)
            u = conn.execute("SELECT name FROM organizations WHERE id = ?", (uniform_unit_id,)).fetchone()
            if u:
                filter_desc = f"Unit: {u['name']}"
                file_suffix = u['name'].replace(" ", "_")
        if club_society_id:
            query += " AND s.club_society_id = ?"
            params.append(club_society_id)
            c = conn.execute("SELECT name FROM organizations WHERE id = ?", (club_society_id,)).fetchone()
            if c:
                filter_desc = f"Kelab: {c['name']}"
                file_suffix = c['name'].replace(" ", "_")
        if sports_game_id:
            query += " AND s.sports_game_id = ?"
            params.append(sports_game_id)
            sp = conn.execute("SELECT name FROM organizations WHERE id = ?", (sports_game_id,)).fetchone()
            if sp:
                filter_desc = f"Sukan: {sp['name']}"
                file_suffix = sp['name'].replace(" ", "_")
        if category and not (sport_house_id or uniform_unit_id or club_society_id or sports_game_id):
            if category == "Rumah Sukan":
                query += " AND s.sport_house_id IS NOT NULL"
                filter_desc = "Kategori: Rumah Sukan"
                file_suffix = "Rumah_Sukan"
            elif category == "Unit Beruniform":
                query += " AND s.uniform_unit_id IS NOT NULL"
                filter_desc = "Kategori: Unit Beruniform"
                file_suffix = "Unit_Beruniform"
            elif category in ("Kelab & Persatuan", "Kelab dan Persatuan"):
                query += " AND s.club_society_id IS NOT NULL"
                filter_desc = "Kategori: Kelab & Persatuan"
                file_suffix = "Kelab_Persatuan"
            elif category in ("Sukan & Permainan", "Sukan dan Permainan"):
                query += " AND s.sports_game_id IS NOT NULL"
                filter_desc = "Kategori: Sukan & Permainan"
                file_suffix = "Sukan_Permainan"
    
    query += " ORDER BY s.grade ASC, s.class_name ASC, s.full_name ASC"
    rows = conn.execute(query, tuple(params)).fetchall()

    school = conn.execute("SELECT * FROM school_settings WHERE id = 1").fetchone()
    school_name = school["school_name"] if school else "SEKOLAH KEBANGSAAN SUNGAI DENDANG"
    school_code = school["school_code"] if school else "ABA6034"
    conn.close()

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Senarai_Murid"

    # School title header rows in Excel
    ws.merge_cells("A1:P1")
    ws["A1"] = f"{school_name} ({school_code})"
    ws["A1"].font = Font(name="Calibri", size=14, bold=True, color="1E3A8A")
    ws["A1"].alignment = Alignment(horizontal="center", vertical="center")

    ws.merge_cells("A2:P2")
    ws["A2"] = f"SENARAI MAKLUMAT MURID KOKURIKULUM — {filter_desc.upper()} (JUMLAH: {len(rows)} ORANG)"
    ws["A2"].font = Font(name="Calibri", size=11, bold=True, color="475569")
    ws["A2"].alignment = Alignment(horizontal="center", vertical="center")

    headers = [
        "Bil", "Nama Penuh", "No KP / MyKid", "Tarikh Lahir", "Jantina",
        "Tahun", "Kelas", "Nama Penjaga", "No Telefon Penjaga", "Alamat",
        "Maklumat Kesihatan", "Rumah Sukan", "Unit Beruniform", "Kelab & Persatuan",
        "Sukan & Permainan", "Status"
    ]

    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
    thin_border = Border(
        left=Side(style='thin', color='CBD5E1'),
        right=Side(style='thin', color='CBD5E1'),
        top=Side(style='thin', color='CBD5E1'),
        bottom=Side(style='thin', color='CBD5E1')
    )

    for col_idx, h in enumerate(headers, 1):
        c = ws.cell(row=4, column=col_idx, value=h)
        c.font = header_font
        c.fill = header_fill
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        c.border = thin_border

    ws.row_dimensions[4].height = 25

    for row_offset, r in enumerate(rows, 1):
        row_idx = 4 + row_offset
        ws.row_dimensions[row_idx].height = 20
        
        cells_data = [
            (row_offset, "center"),
            (r["full_name"], "left"),
            (r["ic_number"], "center"),
            (r["birth_date"] or "-", "center"),
            (r["gender"], "center"),
            (r["grade"], "center"),
            (r["class_name"], "left"),
            (r["guardian_name"] or "-", "left"),
            (r["guardian_phone"] or "-", "center"),
            (r["address"] or "-", "left"),
            (r["health_info"] or "Tiada", "left"),
            (r["sport_house_name"] or "-", "left"),
            (r["uniform_unit_name"] or "-", "left"),
            (r["club_society_name"] or "-", "left"),
            (r["sports_game_name"] or "-", "left"),
            (r["status"], "center")
        ]

        # Zebra striping for readability
        row_fill = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid") if row_offset % 2 == 0 else PatternFill(fill_type=None)

        for col_idx, (val, align_h) in enumerate(cells_data, 1):
            cell = ws.cell(row=row_idx, column=col_idx, value=val)
            cell.alignment = Alignment(horizontal=align_h, vertical="center")
            cell.border = thin_border
            if row_offset % 2 == 0:
                cell.fill = row_fill

    for col in ws.columns:
        col_letter = openpyxl.utils.get_column_letter(col[0].column)
        max_len = 0
        for cell in col:
            if cell.row in [1, 2]: # skip title rows
                continue
            if cell.value:
                max_len = max(max_len, len(str(cell.value)))
        ws.column_dimensions[col_letter].width = max(max_len + 3, 11)

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    filename = f"Senarai_Murid_SKSD_{file_suffix}.xlsx"

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

FIXED_CLASSES = {
    1: "1 UM",
    2: "2 UKM",
    3: "3 UPM",
    4: "4 USM",
    5: "5 UTM",
    6: "6 UITM"
}

@router.post("")
async def create_student(data: StudentCreate, user: Dict[str, Any] = Depends(require_roles("Admin", "GPK Kokurikulum", "Setiausaha Kokurikulum"))):
    import time
    conn = get_db_connection()
    ic = (data.ic_number or "").strip()
    if not ic:
        # Generate temporary unique draft ID so incomplete records can still be saved
        ic = f"DRAFT-{int(time.time() * 1000)}"
    else:
        existing = conn.execute("SELECT id FROM students WHERE ic_number = ?", (ic,)).fetchone()
        if existing:
            conn.close()
            raise HTTPException(status_code=400, detail="Nombor Kad Pengenalan / Surat Beranak telah didaftarkan.")

    grade = data.grade or 1
    class_name = (data.class_name or "").strip() or FIXED_CLASSES.get(grade, f"{grade} UM")
    full_name = (data.full_name or "").strip().upper() or "MURID TANPA NAMA"
    gender = (data.gender or "").strip() or "Lelaki"

    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO students (
        full_name, ic_number, birth_date, gender, grade, class_name,
        guardian_name, guardian_phone, address, health_info,
        sport_house_id, uniform_unit_id, club_society_id, sports_game_id,
        status, academic_year
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        full_name,
        ic,
        data.birth_date,
        gender,
        grade,
        class_name,
        data.guardian_name,
        data.guardian_phone,
        data.address,
        data.health_info or "Tiada",
        data.sport_house_id,
        data.uniform_unit_id,
        data.club_society_id,
        data.sports_game_id,
        data.status or "Aktif",
        data.academic_year or "2026/2027"
    ))
    new_id = cursor.lastrowid

    # Register memberships
    for org_id in [data.sport_house_id, data.uniform_unit_id, data.club_society_id, data.sports_game_id]:
        if org_id:
            cursor.execute("INSERT OR IGNORE INTO organization_members (organization_id, student_id, academic_year) VALUES (?, ?, ?)", (org_id, new_id, data.academic_year or "2026/2027"))

    conn.commit()
    conn.close()

    log_audit(user.get("id"), user.get("username"), user.get("role"), "CREATE", "STUDENTS", f"Daftar murid baharu: {data.full_name}", target_id=new_id)
    return {"status": "success", "message": "Murid berjaya didaftarkan.", "id": new_id}

@router.get("/{student_id}")
async def get_student_profile(student_id: int, user: Dict[str, Any] = Depends(get_current_user)):
    conn = get_db_connection()
    student = conn.execute("""
    SELECT 
        s.*,
        rh.name as sport_house_name, rh.color_code as sport_house_color,
        ub.name as uniform_unit_name,
        kp.name as club_society_name,
        sp.name as sports_game_name
    FROM students s
    LEFT JOIN organizations rh ON s.sport_house_id = rh.id
    LEFT JOIN organizations ub ON s.uniform_unit_id = ub.id
    LEFT JOIN organizations kp ON s.club_society_id = kp.id
    LEFT JOIN organizations sp ON s.sports_game_id = sp.id
    WHERE s.id = ?
    """, (student_id,)).fetchone()

    if not student:
        conn.close()
        raise HTTPException(status_code=404, detail="Murid tidak dijumpai.")

    st_dict = dict(student)

    # 1. Committee positions held
    committees = conn.execute("""
    SELECT c.*, o.name as org_name, o.category as org_category
    FROM student_committees c
    JOIN organizations o ON c.organization_id = o.id
    WHERE c.student_id = ?
    ORDER BY c.academic_year DESC
    """, (student_id,)).fetchall()
    st_dict["committees"] = [dict(c) for c in committees]

    # 2. Attendance History & Stats
    attendance_records = conn.execute("""
    SELECT 
        ar.status, ar.remarks, ar.recorded_at,
        ases.session_date, ases.activity_title, ases.start_time, ases.end_time, ases.venue, ases.advisor_teacher,
        o.name as org_name, o.category as org_category
    FROM attendance_records ar
    JOIN attendance_sessions ases ON ar.session_id = ases.id
    JOIN organizations o ON ases.organization_id = o.id
    WHERE ar.student_id = ?
    ORDER BY ases.session_date DESC
    """, (student_id,)).fetchall()
    st_dict["attendance_history"] = [dict(a) for a in attendance_records]

    total_sessions = len(attendance_records)
    present_sessions = sum(1 for a in attendance_records if a["status"] == "Hadir")
    attendance_rate = round((present_sessions / total_sessions * 100), 1) if total_sessions > 0 else 100.0
    st_dict["total_sessions"] = total_sessions
    st_dict["present_sessions"] = present_sessions
    st_dict["attendance_rate"] = attendance_rate

    # 3. Weekly Activities Attended
    # Activities linked to student's orgs
    activities = conn.execute("""
    SELECT 
        wa.*, o.name as org_name, o.category as org_category
    FROM weekly_activities wa
    JOIN organizations o ON wa.organization_id = o.id
    WHERE wa.organization_id IN (?, ?, ?, ?)
    ORDER BY wa.activity_date DESC
    """, (st_dict["sport_house_id"], st_dict["uniform_unit_id"], st_dict["club_society_id"], st_dict["sports_game_id"])).fetchall()
    st_dict["activities"] = [dict(act) for act in activities]

    # 4. External Participations & Achievements & PAJSK
    external_records = conn.execute("""
    SELECT 
        eps.role, eps.achievement, eps.pajsk_score, eps.remarks as student_remarks,
        ep.program_name, ep.event_date, ep.venue, ep.organizer, ep.activity_category,
        ep.participation_level, ep.certificate_url, ep.evidence_url,
        o.name as represented_org_name
    FROM external_participation_students eps
    JOIN external_participations ep ON eps.participation_id = ep.id
    LEFT JOIN organizations o ON ep.represented_org_id = o.id
    WHERE eps.student_id = ?
    ORDER BY ep.event_date DESC
    """, (student_id,)).fetchall()
    st_dict["external_participations"] = [dict(e) for e in external_records]

    # Calculate Total PAJSK Estimate
    # Attendance score (max 40)
    attendance_pajsk = (attendance_rate / 100.0) * 40.0
    # Jawatan score (max 10)
    jawatan_scores = {
        "Pengerusi": 10.0, "Ketua Rumah / Ketua Pasukan": 10.0,
        "Naib Pengerusi": 8.0, "Penolong Ketua": 8.0,
        "Setiausaha": 7.0, "Bendahari": 7.0,
        "Penolong Setiausaha": 6.0, "Penolong Bendahari": 6.0,
        "Ahli Jawatankuasa": 5.0, "Ahli Aktif": 3.0
    }
    jawatan_pajsk = 0.0
    for c in st_dict["committees"]:
        score = jawatan_scores.get(c["position"], 3.0)
        if score > jawatan_pajsk:
            jawatan_pajsk = score

    # Penglibatan & Pencapaian Luar (max 40)
    pencapaian_pajsk = sum(e["pajsk_score"] or 0.0 for e in st_dict["external_participations"])
    pencapaian_pajsk = min(pencapaian_pajsk, 40.0)

    # Ekstra Kurikulum (default bonus max 10)
    ekstra_pajsk = 8.0 if len(st_dict["external_participations"]) > 0 else 5.0

    total_pajsk = round(attendance_pajsk + jawatan_pajsk + pencapaian_pajsk + ekstra_pajsk, 2)
    st_dict["pajsk_summary"] = {
        "kehadiran_score": round(attendance_pajsk, 2),
        "jawatan_score": round(jawatan_pajsk, 2),
        "pencapaian_score": round(pencapaian_pajsk, 2),
        "ekstra_score": round(ekstra_pajsk, 2),
        "total_score": min(total_pajsk, 100.0),
        "gred": "A" if total_pajsk >= 80 else ("B" if total_pajsk >= 60 else ("C" if total_pajsk >= 40 else "D"))
    }

    # 5. Permission letters status
    permission_letters = conn.execute("""
    SELECT 
        pls.permission_status, pls.parent_notes, pls.response_date,
        pl.program_name, pl.destination_venue, pl.start_datetime, pl.organizer
    FROM permission_letter_students pls
    JOIN permission_letters pl ON pls.letter_id = pl.id
    WHERE pls.student_id = ?
    ORDER BY pl.start_datetime DESC
    """, (student_id,)).fetchall()
    st_dict["permission_letters"] = [dict(p) for p in permission_letters]

    conn.close()
    return st_dict

@router.put("/{student_id}")
async def update_student(
    student_id: int,
    data: StudentUpdate,
    user: Dict[str, Any] = Depends(require_roles("Admin", "GPK Kokurikulum", "Setiausaha Kokurikulum"))
):
    conn = get_db_connection()
    existing = conn.execute("SELECT * FROM students WHERE id = ?", (student_id,)).fetchone()
    if not existing:
        conn.close()
        raise HTTPException(status_code=404, detail="Murid tidak dijumpai.")

    # Duplicate IC check only if changed and non-empty
    ic = data.ic_number.strip() if (data.ic_number and data.ic_number.strip()) else None
    if ic and ic != existing["ic_number"]:
        dup = conn.execute("SELECT id FROM students WHERE ic_number = ? AND id != ?", (ic, student_id)).fetchone()
        if dup:
            conn.close()
            raise HTTPException(status_code=400, detail="Nombor Kad Pengenalan / Surat Beranak telah didaftarkan untuk murid lain.")

    grade = data.grade if data.grade is not None else existing["grade"]
    class_name = data.class_name.strip() if (data.class_name and data.class_name.strip()) else FIXED_CLASSES.get(grade, existing["class_name"])

    update_fields = []
    values = []

    fields_map = {
        "full_name": data.full_name.strip().upper() if (data.full_name and data.full_name.strip()) else None,
        "ic_number": ic,
        "birth_date": data.birth_date,
        "gender": data.gender,
        "grade": grade,
        "class_name": class_name,
        "guardian_name": data.guardian_name,
        "guardian_phone": data.guardian_phone,
        "address": data.address,
        "health_info": data.health_info,
        "sport_house_id": data.sport_house_id,
        "uniform_unit_id": data.uniform_unit_id,
        "club_society_id": data.club_society_id,
        "sports_game_id": data.sports_game_id,
        "status": data.status,
        "academic_year": data.academic_year
    }

    for col, val in fields_map.items():
        if val is not None:
            update_fields.append(f"{col} = ?")
            values.append(val)

    if update_fields:
        values.append(student_id)
        conn.execute(f"UPDATE students SET {', '.join(update_fields)} WHERE id = ?", tuple(values))

        # Re-sync organization_members
        for org_id in [data.sport_house_id, data.uniform_unit_id, data.club_society_id, data.sports_game_id]:
            if org_id:
                conn.execute("INSERT OR IGNORE INTO organization_members (organization_id, student_id, academic_year) VALUES (?, ?, '2026/2027')", (org_id, student_id))

        conn.commit()

    conn.close()
    log_audit(user.get("id"), user.get("username"), user.get("role"), "UPDATE", "STUDENTS", f"Kemas kini maklumat murid ID: {student_id}", target_id=student_id)
    return {"status": "success", "message": "Maklumat murid berjaya dikemas kini."}

@router.delete("/{student_id}")
async def delete_student(student_id: int, user: Dict[str, Any] = Depends(require_deletion_roles())):
    conn = get_db_connection()
    st = conn.execute("SELECT full_name FROM students WHERE id = ?", (student_id,)).fetchone()
    if not st:
        conn.close()
        raise HTTPException(status_code=404, detail="Murid tidak dijumpai.")

    conn.execute("DELETE FROM students WHERE id = ?", (student_id,))
    conn.commit()
    conn.close()

    log_audit(user.get("id"), user.get("username"), user.get("role"), "DELETE", "STUDENTS", f"Padam murid: {dict(st)['full_name']}", target_id=student_id)
    return {"status": "success", "message": "Rekod murid berjaya dipadam."}

@router.post("/bulk-assign")
async def bulk_assign_organization(
    data: BulkAssignOrg,
    user: Dict[str, Any] = Depends(require_roles("Admin", "GPK Kokurikulum", "Setiausaha Kokurikulum", "Penyelaras Kokurikulum"))
):
    if not data.student_ids:
        raise HTTPException(status_code=400, detail="Sila pilih sekurang-kurangnya seorang murid.")

    category_col_map = {
        "Rumah Sukan": "sport_house_id",
        "Unit Beruniform": "uniform_unit_id",
        "Kelab & Persatuan": "club_society_id",
        "Kelab dan Persatuan": "club_society_id",
        "Sukan & Permainan": "sports_game_id",
        "Sukan dan Permainan": "sports_game_id"
    }

    col_name = category_col_map.get(data.category)
    if not col_name:
        raise HTTPException(status_code=400, detail=f"Kategori tidak sah: {data.category}")

    conn = get_db_connection()
    cursor = conn.cursor()

    for s_id in data.student_ids:
        cursor.execute(f"UPDATE students SET {col_name} = ? WHERE id = ?", (data.organization_id, s_id))
        cursor.execute("INSERT OR IGNORE INTO organization_members (organization_id, student_id, academic_year) VALUES (?, ?, '2026/2027')", (data.organization_id, s_id))

    conn.commit()
    conn.close()

    log_audit(user.get("id"), user.get("username"), user.get("role"), "BULK_ASSIGN", "STUDENTS", f"Kemas kini pukal {len(data.student_ids)} murid ke organisasi ID {data.organization_id}")
    return {"status": "success", "message": f"{len(data.student_ids)} murid berjaya ditetapkan ke organisasi yang dipilih."}
