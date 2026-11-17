import os
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, Query
from app.database import get_db_connection, log_audit
from app.auth import get_current_user, require_roles, require_deletion_roles
from app.models import ActivityCreate, ActivityUpdate, ActivityStatusAction

router = APIRouter(prefix="/api/activities", tags=["Aktiviti & Laporan Mingguan"])

UPLOAD_DIR = Path(__file__).resolve().parent.parent / "static" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

@router.get("")
async def list_activities(
    org_id: Optional[int] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    user: Dict[str, Any] = Depends(get_current_user)
):
    conn = get_db_connection()
    query = """
    SELECT 
        wa.*,
        o.name as org_name, o.category as org_category, o.color_code
    FROM weekly_activities wa
    JOIN organizations o ON wa.organization_id = o.id
    WHERE 1=1
    """
    params = []

    if org_id:
        query += " AND wa.organization_id = ?"
        params.append(org_id)

    if category:
        query += " AND o.category = ?"
        params.append(category)

    if status:
        query += " AND wa.status = ?"
        params.append(status)

    if search:
        s_term = f"%{search.strip()}%"
        query += " AND (wa.title LIKE ? OR wa.objectives LIKE ? OR wa.teachers_involved LIKE ?)"
        params.extend([s_term, s_term, s_term])

    if start_date:
        query += " AND wa.activity_date >= ?"
        params.append(start_date)

    if end_date:
        query += " AND wa.activity_date <= ?"
        params.append(end_date)

    query += " ORDER BY wa.activity_date DESC, wa.id DESC"
    rows = conn.execute(query, tuple(params)).fetchall()
    conn.close()

    return [dict(r) for r in rows]

@router.get("/{activity_id}")
async def get_activity(activity_id: int, user: Dict[str, Any] = Depends(get_current_user)):
    conn = get_db_connection()
    activity = conn.execute("""
    SELECT 
        wa.*,
        o.name as org_name, o.category as org_category, o.color_code, o.meeting_day, o.meeting_time
    FROM weekly_activities wa
    JOIN organizations o ON wa.organization_id = o.id
    WHERE wa.id = ?
    """, (activity_id,)).fetchone()

    if not activity:
        conn.close()
        raise HTTPException(status_code=404, detail="Laporan aktiviti tidak dijumpai.")

    act_dict = dict(activity)

    # Attach linked attendance session if any
    linked_session = conn.execute("""
    SELECT *
    FROM attendance_sessions
    WHERE organization_id = ? AND session_date = ?
    ORDER BY id DESC LIMIT 1
    """, (act_dict["organization_id"], act_dict["activity_date"])).fetchone()

    present_students = []
    absent_students = []
    all_attendance = []
    summary = {
        "total_enrolled": 0,
        "total_present": act_dict.get("attendees_count", 0),
        "total_absent": 0,
        "percentage": 0.0
    }

    if linked_session:
        sess_dict = dict(linked_session)
        act_dict["linked_session"] = sess_dict
        session_id = sess_dict["id"]

        records = conn.execute("""
        SELECT 
            ar.id as record_id, ar.status, ar.remarks,
            s.id as student_id, s.full_name, s.ic_number, s.class_name, s.gender
        FROM attendance_records ar
        JOIN students s ON ar.student_id = s.id
        WHERE ar.session_id = ?
        ORDER BY s.grade ASC, s.class_name ASC, s.full_name ASC
        """, (session_id,)).fetchall()

        for r in records:
            item = dict(r)
            all_attendance.append(item)
            if item["status"] in ["Hadir", "Lewat"]:
                present_students.append(item)
            else:
                absent_students.append(item)

        total_enrolled = len(records)
        total_present = len(present_students)
        total_absent = len(absent_students)
        pct = round((total_present / total_enrolled * 100), 1) if total_enrolled > 0 else 0.0

        summary = {
            "total_enrolled": total_enrolled,
            "total_present": total_present,
            "total_absent": total_absent,
            "percentage": pct
        }
    else:
        # Fallback to organization members if session not yet created
        members = conn.execute("""
        SELECT s.id as student_id, s.full_name, s.ic_number, s.class_name, s.gender
        FROM organization_members om
        JOIN students s ON om.student_id = s.id
        WHERE om.organization_id = ? AND s.status = 'Aktif'
        ORDER BY s.grade ASC, s.class_name ASC, s.full_name ASC
        """, (act_dict["organization_id"],)).fetchall()

        for m in members:
            item = dict(m)
            item["status"] = "Hadir" if len(present_students) < (act_dict.get("attendees_count") or 0) else "Tidak Hadir"
            item["remarks"] = ""
            all_attendance.append(item)
            if item["status"] == "Hadir":
                present_students.append(item)
            else:
                absent_students.append(item)

        tot = len(members)
        pres = len(present_students)
        summary = {
            "total_enrolled": tot,
            "total_present": pres,
            "total_absent": tot - pres,
            "percentage": round(pres / tot * 100, 1) if tot > 0 else 0.0
        }

    act_dict["present_students"] = present_students
    act_dict["absent_students"] = absent_students
    act_dict["attendance_records"] = all_attendance
    act_dict["attendance_summary"] = summary

    # School settings for official print
    school = conn.execute("SELECT * FROM school_settings WHERE id = 1").fetchone()
    act_dict["school"] = dict(school) if school else None

    conn.close()
    return act_dict

@router.post("")
async def create_activity(
    data: ActivityCreate,
    user: Dict[str, Any] = Depends(require_roles("Admin", "GPK Kokurikulum", "Setiausaha Kokurikulum", "Penyelaras Kokurikulum", "Guru Penasihat"))
):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Calculate attendance counts if records provided
    attendees_count = data.attendees_count or 0
    if data.attendance_records:
        attendees_count = sum(1 for r in data.attendance_records if r.status in ["Hadir", "Lewat"])

    cursor.execute("""
    INSERT INTO weekly_activities (
        organization_id, activity_date, start_time, end_time, venue,
        title, objectives, description_rundown, teachers_involved,
        attendees_count, reflection, suggestions,
        photo_1, photo_2, photo_3, photo_4, attachment_file,
        status, submitted_by, submitted_at, academic_year
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, '2026/2027')
    """, (
        data.organization_id,
        data.activity_date,
        data.start_time,
        data.end_time,
        data.venue,
        data.title.strip(),
        data.objectives,
        data.description_rundown,
        data.teachers_involved or user.get("full_name"),
        attendees_count,
        data.reflection,
        data.suggestions,
        data.photo_1,
        data.photo_2,
        data.photo_3,
        data.photo_4,
        data.attachment_file,
        data.status or "Draf",
        user.get("username")
    ))
    new_id = cursor.lastrowid

    # Create/Sync Attendance Session & Records
    if data.attendance_records:
        total_enrolled = len(data.attendance_records)
        total_present = sum(1 for r in data.attendance_records if r.status in ["Hadir", "Lewat"])
        total_absent = sum(1 for r in data.attendance_records if r.status in ["Tidak Hadir", "Tanpa Sebab", "Tidak"])
        total_excused = sum(1 for r in data.attendance_records if r.status in ["Kebenaran / Sakit", "Kebenaran", "Sakit"])
        total_late = sum(1 for r in data.attendance_records if r.status == "Lewat")

        # Check existing attendance session
        existing_sess = conn.execute("""
        SELECT id FROM attendance_sessions
        WHERE organization_id = ? AND session_date = ?
        """, (data.organization_id, data.activity_date)).fetchone()

        if existing_sess:
            sess_id = existing_sess["id"]
            cursor.execute("""
            UPDATE attendance_sessions SET
                activity_title = ?, venue = ?, start_time = ?, end_time = ?,
                advisor_teacher = ?, total_enrolled = ?, total_present = ?,
                total_absent = ?, total_late = ?, total_excused = ?
            WHERE id = ?
            """, (
                data.title.strip(), data.venue, data.start_time, data.end_time,
                data.teachers_involved or user.get("full_name"),
                total_enrolled, total_present, total_absent, total_late, total_excused, sess_id
            ))
            cursor.execute("DELETE FROM attendance_records WHERE session_id = ?", (sess_id,))
        else:
            cursor.execute("""
            INSERT INTO attendance_sessions (
                organization_id, session_date, start_time, end_time, venue,
                activity_title, advisor_teacher, academic_year,
                total_enrolled, total_present, total_absent, total_late, total_excused, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, '2026/2027', ?, ?, ?, ?, ?, ?)
            """, (
                data.organization_id, data.activity_date, data.start_time, data.end_time, data.venue,
                data.title.strip(), data.teachers_involved or user.get("full_name"),
                total_enrolled, total_present, total_absent, total_late, total_excused, user.get("username")
            ))
            sess_id = cursor.lastrowid

        # Insert student records
        for rec in data.attendance_records:
            cursor.execute("""
            INSERT INTO attendance_records (session_id, student_id, status, remarks)
            VALUES (?, ?, ?, ?)
            """, (sess_id, rec.student_id, rec.status, rec.remarks))

    conn.commit()
    conn.close()

    log_audit(user.get("id"), user.get("username"), user.get("role"), "CREATE", "ACTIVITIES", f"Cipta laporan aktiviti & kehadiran: {data.title} ({data.status})", target_id=new_id)
    return {"status": "success", "message": "Laporan aktiviti dan kehadiran murid berjaya disimpan.", "id": new_id}

@router.put("/{activity_id}")
async def update_activity(
    activity_id: int,
    data: ActivityUpdate,
    user: Dict[str, Any] = Depends(require_roles("Admin", "GPK Kokurikulum", "Setiausaha Kokurikulum", "Penyelaras Kokurikulum", "Guru Penasihat"))
):
    conn = get_db_connection()
    existing = conn.execute("SELECT * FROM weekly_activities WHERE id = ?", (activity_id,)).fetchone()
    if not existing:
        conn.close()
        raise HTTPException(status_code=404, detail="Laporan aktiviti tidak dijumpai.")

    ex_dict = dict(existing)
    org_id = data.organization_id or ex_dict["organization_id"]
    act_date = data.activity_date or ex_dict["activity_date"]
    act_title = (data.title.strip() if data.title else ex_dict["title"])
    act_venue = data.venue if data.venue is not None else ex_dict["venue"]
    act_start = data.start_time if data.start_time is not None else ex_dict["start_time"]
    act_end = data.end_time if data.end_time is not None else ex_dict["end_time"]
    act_teachers = data.teachers_involved if data.teachers_involved is not None else ex_dict["teachers_involved"]

    attendees_count = data.attendees_count
    if data.attendance_records is not None:
        attendees_count = sum(1 for r in data.attendance_records if r.status in ["Hadir", "Lewat"])

    update_fields = []
    values = []

    fields_map = {
        "organization_id": data.organization_id,
        "activity_date": data.activity_date,
        "start_time": data.start_time,
        "end_time": data.end_time,
        "venue": data.venue,
        "title": data.title.strip() if data.title else None,
        "objectives": data.objectives,
        "description_rundown": data.description_rundown,
        "teachers_involved": data.teachers_involved,
        "attendees_count": attendees_count,
        "reflection": data.reflection,
        "suggestions": data.suggestions,
        "photo_1": data.photo_1,
        "photo_2": data.photo_2,
        "photo_3": data.photo_3,
        "photo_4": data.photo_4,
        "attachment_file": data.attachment_file,
        "status": data.status,
        "review_remarks": data.review_remarks
    }

    for col, val in fields_map.items():
        if val is not None:
            update_fields.append(f"{col} = ?")
            values.append(val)

    cursor = conn.cursor()
    if update_fields:
        values.append(activity_id)
        cursor.execute(f"UPDATE weekly_activities SET {', '.join(update_fields)} WHERE id = ?", tuple(values))

    # Sync Attendance Session & Records if provided
    if data.attendance_records is not None:
        total_enrolled = len(data.attendance_records)
        total_present = sum(1 for r in data.attendance_records if r.status in ["Hadir", "Lewat"])
        total_absent = sum(1 for r in data.attendance_records if r.status in ["Tidak Hadir", "Tanpa Sebab", "Tidak"])
        total_excused = sum(1 for r in data.attendance_records if r.status in ["Kebenaran / Sakit", "Kebenaran", "Sakit"])
        total_late = sum(1 for r in data.attendance_records if r.status == "Lewat")

        existing_sess = conn.execute("""
        SELECT id FROM attendance_sessions
        WHERE organization_id = ? AND session_date = ?
        """, (org_id, act_date)).fetchone()

        if existing_sess:
            sess_id = existing_sess["id"]
            cursor.execute("""
            UPDATE attendance_sessions SET
                activity_title = ?, venue = ?, start_time = ?, end_time = ?,
                advisor_teacher = ?, total_enrolled = ?, total_present = ?,
                total_absent = ?, total_late = ?, total_excused = ?
            WHERE id = ?
            """, (
                act_title, act_venue, act_start, act_end,
                act_teachers or user.get("full_name"),
                total_enrolled, total_present, total_absent, total_late, total_excused, sess_id
            ))
            cursor.execute("DELETE FROM attendance_records WHERE session_id = ?", (sess_id,))
        else:
            cursor.execute("""
            INSERT INTO attendance_sessions (
                organization_id, session_date, start_time, end_time, venue,
                activity_title, advisor_teacher, academic_year,
                total_enrolled, total_present, total_absent, total_late, total_excused, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, '2026/2027', ?, ?, ?, ?, ?, ?)
            """, (
                org_id, act_date, act_start, act_end, act_venue,
                act_title, act_teachers or user.get("full_name"),
                total_enrolled, total_present, total_absent, total_late, total_excused, user.get("username")
            ))
            sess_id = cursor.lastrowid

        for rec in data.attendance_records:
            cursor.execute("""
            INSERT INTO attendance_records (session_id, student_id, status, remarks)
            VALUES (?, ?, ?, ?)
            """, (sess_id, rec.student_id, rec.status, rec.remarks))

    conn.commit()
    conn.close()
    log_audit(user.get("id"), user.get("username"), user.get("role"), "UPDATE", "ACTIVITIES", f"Kemas kini laporan & kehadiran ID: {activity_id}", target_id=activity_id)
    return {"status": "success", "message": "Laporan aktiviti dan kehadiran berjaya dikemas kini."}

@router.post("/{activity_id}/action")
async def process_activity_action(
    activity_id: int,
    data: ActivityStatusAction,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Approval Flow:
    1. Draf -> Dihantar (Guru Penasihat)
    2. Dihantar -> Disemak (Penyelaras Kokurikulum / SU / GPK / Admin)
    3. Disemak -> Disahkan (GPK Kokurikulum / SU / Admin)
    4. Any -> Perlu Pindaan (Penyelaras / GPK / SU / Admin with remarks)
    """
    conn = get_db_connection()
    existing = conn.execute("SELECT * FROM weekly_activities WHERE id = ?", (activity_id,)).fetchone()
    if not existing:
        conn.close()
        raise HTTPException(status_code=404, detail="Laporan aktiviti tidak dijumpai.")

    target_status = data.status
    remarks = data.remarks or ""

    user_role = user.get("role")
    username = user.get("username")

    cursor = conn.cursor()

    if target_status == "Dihantar":
        cursor.execute("""
        UPDATE weekly_activities SET
            status = 'Dihantar',
            submitted_by = ?,
            submitted_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """, (username, activity_id))

    elif target_status == "Disemak":
        if user_role not in ["Admin", "GPK Kokurikulum", "Setiausaha Kokurikulum", "Penyelaras Kokurikulum"]:
            conn.close()
            raise HTTPException(status_code=403, detail="Hanya Penyelaras, Setiausaha, GPK atau Admin boleh menyemak laporan.")
        cursor.execute("""
        UPDATE weekly_activities SET
            status = 'Disemak',
            reviewed_by = ?,
            reviewed_at = CURRENT_TIMESTAMP,
            review_remarks = ?
        WHERE id = ?
        """, (username, remarks, activity_id))

    elif target_status == "Disahkan":
        if user_role not in ["Admin", "GPK Kokurikulum", "Setiausaha Kokurikulum"]:
            conn.close()
            raise HTTPException(status_code=403, detail="Hanya GPK Kokurikulum, Setiausaha atau Admin boleh mengesahkan laporan.")
        cursor.execute("""
        UPDATE weekly_activities SET
            status = 'Disahkan',
            approved_by = ?,
            approved_at = CURRENT_TIMESTAMP,
            review_remarks = ?
        WHERE id = ?
        """, (username, remarks, activity_id))

    elif target_status == "Perlu Pindaan":
        cursor.execute("""
        UPDATE weekly_activities SET
            status = 'Perlu Pindaan',
            review_remarks = ?
        WHERE id = ?
        """, (remarks, activity_id))

    else:
        cursor.execute("UPDATE weekly_activities SET status = ?, review_remarks = ? WHERE id = ?", (target_status, remarks, activity_id))

    conn.commit()
    conn.close()

    log_audit(user.get("id"), username, user_role, "STATUS_CHANGE", "ACTIVITIES", f"Tukar status laporan ID {activity_id} kepada '{target_status}'. Catatan: {remarks}", target_id=activity_id)
    return {"status": "success", "message": f"Status laporan berjaya ditukar kepada '{target_status}'."}

@router.delete("/{activity_id}")
async def delete_activity(
    activity_id: int,
    user: Dict[str, Any] = Depends(require_deletion_roles())
):
    conn = get_db_connection()
    target = conn.execute("SELECT * FROM weekly_activities WHERE id = ?", (activity_id,)).fetchone()
    if not target:
        conn.close()
        raise HTTPException(status_code=404, detail="Laporan aktiviti tidak dijumpai.")

    target_dict = dict(target)
    # Also clean up associated attendance session if matched
    conn.execute("""
        DELETE FROM attendance_sessions 
        WHERE organization_id = ? AND session_date = ? AND (activity_title = ? OR activity_title LIKE ?)
    """, (target_dict["organization_id"], target_dict["activity_date"], target_dict["title"], f"%{target_dict['title']}%"))

    conn.execute("DELETE FROM weekly_activities WHERE id = ?", (activity_id,))
    conn.commit()
    conn.close()

    log_audit(user.get("id"), user.get("username"), user.get("role"), "DELETE", "ACTIVITIES", f"Padam laporan aktiviti: {target_dict['title']}", target_id=activity_id)
    return {"status": "success", "message": f"Laporan aktiviti '{target_dict['title']}' berjaya dipadam."}

@router.post("/upload-photo")
async def upload_activity_photo(
    file: UploadFile = File(...),
    user: Dict[str, Any] = Depends(get_current_user)
):
    ext = file.filename.split(".")[-1].lower() if "." in file.filename else "jpg"
    if ext not in ["jpg", "jpeg", "png", "webp", "gif", "svg", "pdf", "docx"]:
        raise HTTPException(status_code=400, detail="Format fail tidak disokong.")

    import uuid
    new_filename = f"act_{uuid.uuid4().hex[:12]}.{ext}"
    target_path = UPLOAD_DIR / new_filename

    with open(target_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    file_url = f"/static/uploads/{new_filename}"
    return {"status": "success", "url": file_url}
