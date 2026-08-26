import io
import csv
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Response, Query
from fastapi.responses import StreamingResponse
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from app.database import get_db_connection, log_audit
from app.auth import get_current_user, require_roles
from app.models import StudentCreate, StudentUpdate, BulkAssignOrg

router = APIRouter(prefix="/api/students", tags=["Pengurusan Murid"])

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
        ["MUHAMMAD DANISH IRFAN BIN ZULKIFLI", "140515085123", "2014-05-15", "Lelaki", 6, "6 Cemerlang", "Zulkifli bin Daud", "012-5881234", "No 12, Kg Sungai Dendang, Selama", "Tiada", "Rumah Bendahara (Merah)", "Persekutuan Pengakap Malaysia (Pengakap)", "Kelab STEM & Robotik", "Kelab Bola Sepak"],
        ["NUR AISYAH HUMAIRA BINTI AHMAD", "140820086244", "2014-08-20", "Perempuan", 6, "6 Cemerlang", "Ahmad bin Abdullah", "013-4885678", "No 45, Lorong Mawar, Selama", "Alahan Kacang", "Rumah Temenggong (Kuning)", "Pergerakan Pandu Puteri Tunas (PPT)", "Persatuan Bahasa Melayu", "Kelab Bola Jaring"]
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
    org_map = {r["name"].strip().lower(): r["id"] for r in org_rows}

    imported_count = 0
    updated_count = 0
    errors = []

    if filename.endswith(".xlsx"):
        try:
            wb = openpyxl.load_workbook(io.BytesIO(contents), data_only=True)
            ws = wb.active
            rows = list(ws.iter_rows(values_only=True))
            if not rows or len(rows) < 2:
                raise HTTPException(status_code=400, detail="Fail Excel kosong atau tiada data.")

            header = [str(c).strip().lower() if c else "" for c in rows[0]]
            for idx, r in enumerate(rows[1:], start=2):
                if not r or not any(r):
                    continue
                try:
                    full_name = str(r[0]).strip().upper() if r[0] else None
                    ic_number = str(r[1]).strip().replace("-", "").replace(" ", "") if r[1] else None
                    birth_date = str(r[2]).strip() if len(r) > 2 and r[2] else None
                    gender = str(r[3]).strip().capitalize() if len(r) > 3 and r[3] else "Lelaki"
                    grade = int(r[4]) if len(r) > 4 and r[4] else 1
                    class_name = str(r[5]).strip() if len(r) > 5 and r[5] else f"{grade} Cemerlang"
                    guardian_name = str(r[6]).strip() if len(r) > 6 and r[6] else None
                    guardian_phone = str(r[7]).strip() if len(r) > 7 and r[7] else None
                    address = str(r[8]).strip() if len(r) > 8 and r[8] else None
                    health_info = str(r[9]).strip() if len(r) > 9 and r[9] else "Tiada"

                    sport_house_name = str(r[10]).strip().lower() if len(r) > 10 and r[10] else None
                    uniform_unit_name = str(r[11]).strip().lower() if len(r) > 11 and r[11] else None
                    club_society_name = str(r[12]).strip().lower() if len(r) > 12 and r[12] else None
                    sports_game_name = str(r[13]).strip().lower() if len(r) > 13 and r[13] else None

                    sport_house_id = org_map.get(sport_house_name)
                    uniform_unit_id = org_map.get(uniform_unit_name)
                    club_society_id = org_map.get(club_society_name)
                    sports_game_id = org_map.get(sports_game_name)

                    if not full_name or not ic_number:
                        errors.append(f"Baris {idx}: Nama Penuh atau No KP kosong.")
                        continue

                    # Insert or update
                    existing = conn.execute("SELECT id FROM students WHERE ic_number = ?", (ic_number,)).fetchone()
                    if existing:
                        st_id = existing["id"]
                        cursor.execute("""
                        UPDATE students SET
                            full_name = ?, birth_date = ?, gender = ?, grade = ?, class_name = ?,
                            guardian_name = ?, guardian_phone = ?, address = ?, health_info = ?,
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
                            cursor.execute("INSERT OR IGNORE INTO organization_members (organization_id, student_id, academic_year) VALUES (?, ?, '2026/2027')", (org_id, st_id))

                except Exception as ex:
                    errors.append(f"Baris {idx}: Ralat memproses - {str(ex)}")

            conn.commit()
        except Exception as e:
            conn.close()
            raise HTTPException(status_code=400, detail=f"Gagal membaca fail Excel: {str(e)}")

    elif filename.endswith(".csv"):
        try:
            csv_text = contents.decode("utf-8-sig", errors="ignore")
            reader = csv.reader(io.StringIO(csv_text))
            rows = list(reader)
            for idx, r in enumerate(rows[1:], start=2):
                if not r or not any(r):
                    continue
                try:
                    full_name = r[0].strip().upper() if len(r) > 0 and r[0] else None
                    ic_number = r[1].strip().replace("-", "").replace(" ", "") if len(r) > 1 and r[1] else None
                    gender = r[3].strip().capitalize() if len(r) > 3 and r[3] else "Lelaki"
                    grade = int(r[4]) if len(r) > 4 and r[4] else 1
                    class_name = r[5].strip() if len(r) > 5 and r[5] else f"{grade} Cemerlang"
                    guardian_name = r[6].strip() if len(r) > 6 and r[6] else None
                    guardian_phone = r[7].strip() if len(r) > 7 and r[7] else None

                    if not full_name or not ic_number:
                        continue

                    existing = conn.execute("SELECT id FROM students WHERE ic_number = ?", (ic_number,)).fetchone()
                    if existing:
                        cursor.execute("""
                        UPDATE students SET full_name = ?, gender = ?, grade = ?, class_name = ?, guardian_name = ?, guardian_phone = ? WHERE id = ?
                        """, (full_name, gender, grade, class_name, guardian_name, guardian_phone, existing["id"]))
                        updated_count += 1
                    else:
                        cursor.execute("""
                        INSERT INTO students (full_name, ic_number, gender, grade, class_name, guardian_name, guardian_phone, status, academic_year)
                        VALUES (?, ?, ?, ?, ?, ?, ?, 'Aktif', '2026/2027')
                        """, (full_name, ic_number, gender, grade, class_name, guardian_name, guardian_phone))
                        imported_count += 1
                except Exception as ex:
                    errors.append(f"Baris {idx}: {str(ex)}")
            conn.commit()
        except Exception as e:
            conn.close()
            raise HTTPException(status_code=400, detail=f"Gagal membaca fail CSV: {str(e)}")
    else:
        conn.close()
        raise HTTPException(status_code=400, detail="Format fail tidak disokong. Sila gunakan format .xlsx atau .csv.")

    conn.close()
    log_audit(user.get("id"), user.get("username"), user.get("role"), "IMPORT", "STUDENTS", f"Import murid pukal: {imported_count} baharu, {updated_count} dikemas kini")
    
    return {
        "status": "success",
        "imported_count": imported_count,
        "updated_count": updated_count,
        "errors": errors
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

@router.post("")
async def create_student(data: StudentCreate, user: Dict[str, Any] = Depends(require_roles("Admin", "GPK Kokurikulum", "Setiausaha Kokurikulum"))):
    conn = get_db_connection()
    existing = conn.execute("SELECT id FROM students WHERE ic_number = ?", (data.ic_number.strip(),)).fetchone()
    if existing:
        conn.close()
        raise HTTPException(status_code=400, detail="Nombor Kad Pengenalan / Surat Beranak telah didaftarkan.")

    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO students (
        full_name, ic_number, birth_date, gender, grade, class_name,
        guardian_name, guardian_phone, address, health_info,
        sport_house_id, uniform_unit_id, club_society_id, sports_game_id,
        status, academic_year
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data.full_name.strip().upper(),
        data.ic_number.strip(),
        data.birth_date,
        data.gender,
        data.grade,
        data.class_name,
        data.guardian_name,
        data.guardian_phone,
        data.address,
        data.health_info,
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

    update_fields = []
    values = []

    fields_map = {
        "full_name": data.full_name.strip().upper() if data.full_name else None,
        "ic_number": data.ic_number.strip() if data.ic_number else None,
        "birth_date": data.birth_date,
        "gender": data.gender,
        "grade": data.grade,
        "class_name": data.class_name,
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
async def delete_student(student_id: int, user: Dict[str, Any] = Depends(require_roles("Admin", "GPK Kokurikulum"))):
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
