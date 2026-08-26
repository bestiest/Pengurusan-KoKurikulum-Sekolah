import io
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from app.database import get_db_connection, log_audit
from app.auth import get_current_user, require_roles
from app.models import AttendanceSessionCreate, AttendanceRecordItem

router = APIRouter(prefix="/api/attendance", tags=["Kehadiran Kokurikulum"])

@router.get("/sessions")
async def list_sessions(
    org_id: Optional[int] = None,
    category: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    user: Dict[str, Any] = Depends(get_current_user)
):
    conn = get_db_connection()
    query = """
    SELECT 
        ases.*,
        o.name as org_name, o.category as org_category, o.color_code
    FROM attendance_sessions ases
    JOIN organizations o ON ases.organization_id = o.id
    WHERE 1=1
    """
    params = []

    if org_id:
        query += " AND ases.organization_id = ?"
        params.append(org_id)

    if category:
        query += " AND o.category = ?"
        params.append(category)

    if start_date:
        query += " AND ases.session_date >= ?"
        params.append(start_date)

    if end_date:
        query += " AND ases.session_date <= ?"
        params.append(end_date)

    query += " ORDER BY ases.session_date DESC, ases.id DESC"
    rows = conn.execute(query, tuple(params)).fetchall()
    conn.close()

    results = []
    for r in rows:
        d = dict(r)
        total = d.get("total_enrolled", 0) or 0
        present = d.get("total_present", 0) or 0
        d["attendance_rate"] = round((present / total * 100), 1) if total > 0 else 0.0
        results.append(d)

    return results

@router.get("/sessions/{session_id}")
async def get_session_details(session_id: int, user: Dict[str, Any] = Depends(get_current_user)):
    conn = get_db_connection()
    session = conn.execute("""
    SELECT 
        ases.*,
        o.name as org_name, o.category as org_category, o.color_code, o.meeting_day, o.meeting_time
    FROM attendance_sessions ases
    JOIN organizations o ON ases.organization_id = o.id
    WHERE ases.id = ?
    """, (session_id,)).fetchone()

    if not session:
        conn.close()
        raise HTTPException(status_code=404, detail="Sesi kehadiran tidak dijumpai.")

    s_dict = dict(session)

    # Get records
    records = conn.execute("""
    SELECT 
        ar.*,
        s.full_name as student_name, s.ic_number, s.grade, s.class_name, s.gender, s.guardian_phone,
        sc.position as committee_position
    FROM attendance_records ar
    JOIN students s ON ar.student_id = s.id
    LEFT JOIN student_committees sc ON sc.organization_id = ? AND sc.student_id = s.id
    WHERE ar.session_id = ?
    ORDER BY s.grade ASC, s.class_name ASC, s.full_name ASC
    """, (s_dict["organization_id"], session_id)).fetchall()

    s_dict["records"] = [dict(r) for r in records]

    # School details for print
    school = conn.execute("SELECT * FROM school_settings WHERE id = 1").fetchone()
    s_dict["school"] = dict(school) if school else None

    conn.close()
    return s_dict

@router.post("/sessions")
async def create_attendance_session(
    data: AttendanceSessionCreate,
    user: Dict[str, Any] = Depends(require_roles("Admin", "GPK Kokurikulum", "Setiausaha Kokurikulum", "Penyelaras Kokurikulum", "Guru Penasihat"))
):
    conn = get_db_connection()
    cursor = conn.cursor()

    total_enrolled = len(data.records)
    total_present = sum(1 for r in data.records if r.status == "Hadir")
    total_absent = sum(1 for r in data.records if r.status == "Tidak Hadir")
    total_late = sum(1 for r in data.records if r.status == "Lewat")
    total_excused = sum(1 for r in data.records if r.status == "Bersebab")

    cursor.execute("""
    INSERT INTO attendance_sessions (
        organization_id, session_date, start_time, end_time, venue,
        activity_title, advisor_teacher, academic_year,
        total_enrolled, total_present, total_absent, total_late, total_excused,
        notes, created_by
    ) VALUES (?, ?, ?, ?, ?, ?, ?, '2026/2027', ?, ?, ?, ?, ?, ?, ?)
    """, (
        data.organization_id,
        data.session_date,
        data.start_time,
        data.end_time,
        data.venue,
        data.activity_title.strip(),
        data.advisor_teacher or user.get("full_name"),
        total_enrolled,
        total_present,
        total_absent,
        total_late,
        total_excused,
        data.notes,
        user.get("username")
    ))
    session_id = cursor.lastrowid

    # Insert individual records
    for r in data.records:
        cursor.execute("""
        INSERT INTO attendance_records (session_id, student_id, status, remarks)
        VALUES (?, ?, ?, ?)
        """, (session_id, r.student_id, r.status, r.remarks))

    conn.commit()

    # Also automatically create a draft weekly activity report if one doesn't exist for this date & org
    existing_act = conn.execute("SELECT id FROM weekly_activities WHERE organization_id = ? AND activity_date = ?", (data.organization_id, data.session_date)).fetchone()
    if not existing_act:
        cursor.execute("""
        INSERT INTO weekly_activities (
            organization_id, activity_date, start_time, end_time, venue,
            title, description_rundown, teachers_involved, attendees_count,
            status, submitted_by, submitted_at, academic_year
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'Draf', ?, CURRENT_TIMESTAMP, '2026/2027')
        """, (
            data.organization_id,
            data.session_date,
            data.start_time,
            data.end_time,
            data.venue,
            data.activity_title,
            f"Perjumpaan mingguan dijalankan. Seramai {total_present} orang murid hadir.",
            data.advisor_teacher or user.get("full_name"),
            total_present,
            user.get("username")
        ))
        conn.commit()

    conn.close()

    log_audit(user.get("id"), user.get("username"), user.get("role"), "CREATE", "ATTENDANCE", f"Rekod kehadiran: {data.activity_title} ({total_present}/{total_enrolled} hadir)", target_id=session_id)
    return {"status": "success", "message": "Kehadiran berjaya disimpan.", "id": session_id}

@router.put("/sessions/{session_id}")
async def update_attendance_session(
    session_id: int,
    data: AttendanceSessionCreate,
    user: Dict[str, Any] = Depends(require_roles("Admin", "GPK Kokurikulum", "Setiausaha Kokurikulum", "Penyelaras Kokurikulum", "Guru Penasihat"))
):
    conn = get_db_connection()
    existing = conn.execute("SELECT id FROM attendance_sessions WHERE id = ?", (session_id,)).fetchone()
    if not existing:
        conn.close()
        raise HTTPException(status_code=404, detail="Sesi kehadiran tidak dijumpai.")

    total_enrolled = len(data.records)
    total_present = sum(1 for r in data.records if r.status == "Hadir")
    total_absent = sum(1 for r in data.records if r.status == "Tidak Hadir")
    total_late = sum(1 for r in data.records if r.status == "Lewat")
    total_excused = sum(1 for r in data.records if r.status == "Bersebab")

    cursor = conn.cursor()
    cursor.execute("""
    UPDATE attendance_sessions SET
        organization_id = ?, session_date = ?, start_time = ?, end_time = ?, venue = ?,
        activity_title = ?, advisor_teacher = ?,
        total_enrolled = ?, total_present = ?, total_absent = ?, total_late = ?, total_excused = ?,
        notes = ?
    WHERE id = ?
    """, (
        data.organization_id,
        data.session_date,
        data.start_time,
        data.end_time,
        data.venue,
        data.activity_title.strip(),
        data.advisor_teacher,
        total_enrolled,
        total_present,
        total_absent,
        total_late,
        total_excused,
        data.notes,
        session_id
    ))

    # Update or insert records
    for r in data.records:
        cursor.execute("""
        INSERT INTO attendance_records (session_id, student_id, status, remarks)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(session_id, student_id) DO UPDATE SET
            status = excluded.status,
            remarks = excluded.remarks,
            recorded_at = CURRENT_TIMESTAMP
        """, (session_id, r.student_id, r.status, r.remarks))

    conn.commit()
    conn.close()

    log_audit(user.get("id"), user.get("username"), user.get("role"), "UPDATE", "ATTENDANCE", f"Kemas kini kehadiran sesi ID: {session_id}", target_id=session_id)
    return {"status": "success", "message": "Rekod kehadiran berjaya dikemas kini."}

@router.delete("/sessions/{session_id}")
async def delete_attendance_session(
    session_id: int,
    user: Dict[str, Any] = Depends(require_roles("Admin", "GPK Kokurikulum", "Setiausaha Kokurikulum"))
):
    conn = get_db_connection()
    target = conn.execute("SELECT activity_title FROM attendance_sessions WHERE id = ?", (session_id,)).fetchone()
    if not target:
        conn.close()
        raise HTTPException(status_code=404, detail="Sesi kehadiran tidak dijumpai.")

    conn.execute("DELETE FROM attendance_sessions WHERE id = ?", (session_id,))
    conn.commit()
    conn.close()

    log_audit(user.get("id"), user.get("username"), user.get("role"), "DELETE", "ATTENDANCE", f"Padam sesi kehadiran: {dict(target)['activity_title']}", target_id=session_id)
    return {"status": "success", "message": "Sesi kehadiran berjaya dipadam."}

@router.get("/export/excel/{session_id}")
async def export_session_attendance_excel(
    session_id: int,
    user: Dict[str, Any] = Depends(get_current_user)
):
    conn = get_db_connection()
    session = conn.execute("""
    SELECT ases.*, o.name as org_name, o.category as org_category
    FROM attendance_sessions ases
    JOIN organizations o ON ases.organization_id = o.id
    WHERE ases.id = ?
    """, (session_id,)).fetchone()

    if not session:
        conn.close()
        raise HTTPException(status_code=404, detail="Sesi kehadiran tidak dijumpai.")

    records = conn.execute("""
    SELECT 
        ar.*,
        s.full_name as student_name, s.ic_number, s.grade, s.class_name, s.gender,
        sc.position as committee_position
    FROM attendance_records ar
    JOIN students s ON ar.student_id = s.id
    LEFT JOIN student_committees sc ON sc.organization_id = ? AND sc.student_id = s.id
    WHERE ar.session_id = ?
    ORDER BY s.grade ASC, s.class_name ASC, s.full_name ASC
    """, (session["organization_id"], session_id)).fetchall()
    conn.close()

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Rekod_Kehadiran"

    # Letterhead Info
    ws.merge_cells("A1:G1")
    ws["A1"] = "SEKOLAH KEBANGSAAN SUNGAI DENDANG"
    ws["A1"].font = Font(name="Calibri", size=14, bold=True, color="1E3A8A")
    ws["A1"].alignment = Alignment(horizontal="center")

    ws.merge_cells("A2:G2")
    ws["A2"] = f"REKOD KEHADIRAN AKTIVITI KOKURIKULUM ({session['org_name']})"
    ws["A2"].font = Font(name="Calibri", size=12, bold=True)
    ws["A2"].alignment = Alignment(horizontal="center")

    ws["A4"] = f"Tajuk Aktiviti: {session['activity_title']}"
    ws["A5"] = f"Tarikh & Masa: {session['session_date']} ({session['start_time']} - {session['end_time']})"
    ws["E4"] = f"Tempat: {session['venue']}"
    ws["E5"] = f"Guru Penasihat: {session['advisor_teacher']}"

    headers = ["Bil", "Nama Murid", "No KP", "Tahun / Kelas", "Jawatan AJK", "Status Kehadiran", "Catatan Guru"]
    header_row = 7

    for col_idx, h in enumerate(headers, 1):
        c = ws.cell(row=header_row, column=col_idx, value=h)
        c.font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        c.fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
        c.alignment = Alignment(horizontal="center", vertical="center")

    for idx, r in enumerate(records, 1):
        curr_row = header_row + idx
        ws.cell(row=curr_row, column=1, value=idx)
        ws.cell(row=curr_row, column=2, value=r["student_name"])
        ws.cell(row=curr_row, column=3, value=r["ic_number"])
        ws.cell(row=curr_row, column=4, value=r["class_name"])
        ws.cell(row=curr_row, column=5, value=r["committee_position"] or "-")
        
        status_cell = ws.cell(row=curr_row, column=6, value=r["status"])
        if r["status"] == "Hadir":
            status_cell.font = Font(bold=True, color="15803D")
        else:
            status_cell.font = Font(bold=True, color="DC2626")

        ws.cell(row=curr_row, column=7, value=r["remarks"] or "-")

    for col in ws.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        col_letter = openpyxl.utils.get_column_letter(col[0].column)
        ws.column_dimensions[col_letter].width = max(max_len + 3, 12)

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    filename = f"Kehadiran_{session['org_name']}_{session['session_date']}.xlsx".replace(" ", "_")
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
