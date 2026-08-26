from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from app.database import get_db_connection, log_audit
from app.auth import get_current_user, require_roles
from app.models import PermissionLetterCreate, PermissionStatusUpdate

router = APIRouter(prefix="/api/permission-letters", tags=["Surat Kebenaran Murid"])

class AddStudentsToLetter(BaseModel):
    student_ids: List[int]

@router.get("")
async def list_permission_letters(
    search: Optional[str] = None,
    user: Dict[str, Any] = Depends(get_current_user)
):
    conn = get_db_connection()
    query = """
    SELECT 
        pl.*,
        COUNT(pls.student_id) as total_students,
        SUM(CASE WHEN pls.permission_status = 'Dibenarkan' THEN 1 ELSE 0 END) as allowed_count,
        SUM(CASE WHEN pls.permission_status = 'Tidak Dibenarkan' THEN 1 ELSE 0 END) as rejected_count,
        SUM(CASE WHEN pls.permission_status = 'Diterima' THEN 1 ELSE 0 END) as pending_count,
        SUM(CASE WHEN pls.permission_status = 'Belum Diedarkan' THEN 1 ELSE 0 END) as unissued_count
    FROM permission_letters pl
    LEFT JOIN permission_letter_students pls ON pl.id = pls.letter_id
    WHERE 1=1
    """
    params = []

    if search:
        s_term = f"%{search.strip()}%"
        query += " AND (pl.program_name LIKE ? OR pl.destination_venue LIKE ? OR pl.organizer LIKE ?)"
        params.extend([s_term, s_term, s_term])

    query += " GROUP BY pl.id ORDER BY pl.id DESC"
    rows = conn.execute(query, tuple(params)).fetchall()
    conn.close()

    return [dict(r) for r in rows]

@router.get("/{letter_id}")
async def get_permission_letter(letter_id: int, user: Dict[str, Any] = Depends(get_current_user)):
    conn = get_db_connection()
    letter = conn.execute("SELECT * FROM permission_letters WHERE id = ?", (letter_id,)).fetchone()
    if not letter:
        conn.close()
        raise HTTPException(status_code=404, detail="Surat kebenaran tidak dijumpai.")

    let_dict = dict(letter)

    # Students with consent status
    students = conn.execute("""
    SELECT 
        pls.*,
        s.full_name as student_name, s.ic_number, s.grade, s.class_name, s.gender,
        s.guardian_name, s.guardian_phone, s.address, s.health_info
    FROM permission_letter_students pls
    JOIN students s ON pls.student_id = s.id
    WHERE pls.letter_id = ?
    ORDER BY s.grade ASC, s.class_name ASC, s.full_name ASC
    """, (letter_id,)).fetchall()
    let_dict["students"] = [dict(st) for st in students]

    # School settings for official letterhead
    school = conn.execute("SELECT * FROM school_settings WHERE id = 1").fetchone()
    let_dict["school"] = dict(school) if school else None

    conn.close()
    return let_dict

@router.post("")
async def create_permission_letter(
    data: PermissionLetterCreate,
    user: Dict[str, Any] = Depends(require_roles("Admin", "GPK Kokurikulum", "Setiausaha Kokurikulum", "Penyelaras Kokurikulum", "Guru Penasihat"))
):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Generate letter reference number if not provided
    letter_no = data.letter_no
    if not letter_no:
        import datetime
        now = datetime.datetime.now()
        letter_no = f"SKSD/KOKO/{now.year}/{now.strftime('%m%d%H%M')}"

    cursor.execute("""
    INSERT INTO permission_letters (
        letter_no, program_name, destination_venue, start_datetime, end_datetime,
        organizer, transportation, accompanying_teachers, fee_amount,
        contact_person, contact_phone, special_instructions,
        academic_year, created_by
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, '2026/2027', ?)
    """, (
        letter_no,
        data.program_name.strip(),
        data.destination_venue.strip(),
        data.start_datetime,
        data.end_datetime,
        data.organizer.strip(),
        data.transportation,
        data.accompanying_teachers,
        data.fee_amount or 0.0,
        data.contact_person,
        data.contact_phone,
        data.special_instructions,
        user.get("username")
    ))
    letter_id = cursor.lastrowid

    # Add students
    for s_id in data.student_ids:
        cursor.execute("""
        INSERT INTO permission_letter_students (letter_id, student_id, permission_status)
        VALUES (?, ?, 'Belum Diedarkan')
        """, (letter_id, s_id))

    conn.commit()
    conn.close()

    log_audit(user.get("id"), user.get("username"), user.get("role"), "CREATE", "PERMISSION_LETTERS", f"Cipta surat kebenaran: {data.program_name} ({len(data.student_ids)} murid)", target_id=letter_id)
    return {"status": "success", "message": "Surat kebenaran berjaya dijana.", "id": letter_id}

@router.put("/{letter_id}")
async def update_permission_letter(
    letter_id: int,
    data: PermissionLetterCreate,
    user: Dict[str, Any] = Depends(require_roles("Admin", "GPK Kokurikulum", "Setiausaha Kokurikulum", "Penyelaras Kokurikulum", "Guru Penasihat"))
):
    conn = get_db_connection()
    existing = conn.execute("SELECT * FROM permission_letters WHERE id = ?", (letter_id,)).fetchone()
    if not existing:
        conn.close()
        raise HTTPException(status_code=404, detail="Surat kebenaran tidak dijumpai.")

    ex_dict = dict(existing)
    letter_no = data.letter_no or ex_dict["letter_no"]

    cursor = conn.cursor()
    cursor.execute("""
    UPDATE permission_letters SET
        letter_no = ?, program_name = ?, destination_venue = ?, start_datetime = ?, end_datetime = ?,
        organizer = ?, transportation = ?, accompanying_teachers = ?, fee_amount = ?,
        contact_person = ?, contact_phone = ?, special_instructions = ?
    WHERE id = ?
    """, (
        letter_no,
        data.program_name.strip(),
        data.destination_venue.strip(),
        data.start_datetime,
        data.end_datetime,
        data.organizer.strip(),
        data.transportation,
        data.accompanying_teachers,
        data.fee_amount or 0.0,
        data.contact_person,
        data.contact_phone,
        data.special_instructions,
        letter_id
    ))

    # Synchronize student list
    if data.student_ids is not None:
        existing_statuses = {
            r["student_id"]: r["permission_status"]
            for r in conn.execute("SELECT student_id, permission_status FROM permission_letter_students WHERE letter_id = ?", (letter_id,)).fetchall()
        }
        cursor.execute("DELETE FROM permission_letter_students WHERE letter_id = ?", (letter_id,))
        for s_id in data.student_ids:
            st = existing_statuses.get(s_id, 'Belum Diedarkan')
            cursor.execute("""
            INSERT INTO permission_letter_students (letter_id, student_id, permission_status)
            VALUES (?, ?, ?)
            """, (letter_id, s_id, st))

    conn.commit()
    conn.close()

    log_audit(user.get("id"), user.get("username"), user.get("role"), "UPDATE", "PERMISSION_LETTERS", f"Kemas kini surat kebenaran ID: {letter_id} ({len(data.student_ids)} murid)", target_id=letter_id)
    return {"status": "success", "message": "Surat kebenaran dan senarai murid berjaya dikemas kini."}

@router.delete("/{letter_id}")
async def delete_permission_letter(
    letter_id: int,
    user: Dict[str, Any] = Depends(require_roles("Admin", "GPK Kokurikulum", "Setiausaha Kokurikulum", "Penyelaras Kokurikulum", "Guru Penasihat"))
):
    conn = get_db_connection()
    target = conn.execute("SELECT program_name FROM permission_letters WHERE id = ?", (letter_id,)).fetchone()
    if not target:
        conn.close()
        raise HTTPException(status_code=404, detail="Surat kebenaran tidak dijumpai.")

    target_name = dict(target)['program_name']
    conn.execute("DELETE FROM permission_letter_students WHERE letter_id = ?", (letter_id,))
    conn.execute("DELETE FROM permission_letters WHERE id = ?", (letter_id,))
    conn.commit()
    conn.close()

    log_audit(user.get("id"), user.get("username"), user.get("role"), "DELETE", "PERMISSION_LETTERS", f"Padam surat kebenaran: {target_name}", target_id=letter_id)
    return {"status": "success", "message": "Surat kebenaran berjaya dipadam."}

@router.put("/{letter_id}/students/{student_id}")
async def update_student_consent_status(
    letter_id: int,
    student_id: int,
    data: PermissionStatusUpdate,
    user: Dict[str, Any] = Depends(get_current_user)
):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE permission_letter_students SET
        permission_status = ?,
        parent_notes = ?,
        response_date = CURRENT_DATE
    WHERE letter_id = ? AND student_id = ?
    """, (data.permission_status, data.parent_notes, letter_id, student_id))
    conn.commit()
    conn.close()

    log_audit(user.get("id"), user.get("username"), user.get("role"), "UPDATE_STATUS", "PERMISSION_LETTERS", f"Kemas kini status kebenaran murid ID {student_id} kepada '{data.permission_status}'", target_id=letter_id)
    return {"status": "success", "message": "Status kebenaran murid berjaya dikemas kini."}

@router.post("/{letter_id}/add-students")
async def add_students_to_letter(
    letter_id: int,
    data: AddStudentsToLetter,
    user: Dict[str, Any] = Depends(get_current_user)
):
    conn = get_db_connection()
    cursor = conn.cursor()
    added = 0
    for s_id in data.student_ids:
        cursor.execute("""
        INSERT OR IGNORE INTO permission_letter_students (letter_id, student_id, permission_status)
        VALUES (?, ?, 'Belum Diedarkan')
        """, (letter_id, s_id))
        added += 1
    conn.commit()
    conn.close()

    log_audit(user.get("id"), user.get("username"), user.get("role"), "ADD_STUDENTS", "PERMISSION_LETTERS", f"Tambah {added} murid ke surat ID {letter_id}", target_id=letter_id)
    return {"status": "success", "message": f"{added} murid berjaya ditambah ke dalam surat kebenaran."}

@router.delete("/{letter_id}/students/{student_id}")
async def remove_student_from_letter(
    letter_id: int,
    student_id: int,
    user: Dict[str, Any] = Depends(get_current_user)
):
    conn = get_db_connection()
    conn.execute("DELETE FROM permission_letter_students WHERE letter_id = ? AND student_id = ?", (letter_id, student_id))
    conn.commit()
    conn.close()

    log_audit(user.get("id"), user.get("username"), user.get("role"), "REMOVE_STUDENT", "PERMISSION_LETTERS", f"Gugur murid ID {student_id} daripada surat ID {letter_id}", target_id=letter_id)
    return {"status": "success", "message": "Murid berjaya dikeluarkan daripada surat kebenaran."}
