import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from pydantic import BaseModel
from app.database import get_db_connection, log_audit
from app.auth import get_current_user, require_roles, require_deletion_roles
from app.models import SchoolSettingsUpdate, ClassCreate, TeacherCreate
from app.seed_data import seed_demo_data

router = APIRouter(prefix="/api/settings", tags=["Tetapan Sistem"])

UPLOAD_DIR = Path(__file__).resolve().parent.parent / "static" / "images"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

class ArchiveYearRequest(BaseModel):
    session_year: str
    notes: Optional[str] = None

@router.get("/school")
async def get_school_settings():
    conn = get_db_connection()
    row = conn.execute("SELECT * FROM school_settings WHERE id = 1").fetchone()
    conn.close()
    if not row:
        return {
            "school_name": "SEKOLAH KEBANGSAAN SUNGAI DENDANG",
            "school_code": "ABA6034",
            "address": "SK Sungai Dendang, 34140 Rantau Panjang, Selama, Perak Darul Ridzuan",
            "session_year": "2026/2027",
            "logo_url": "/static/images/school_logo.png"
        }
    return dict(row)

@router.put("/school")
async def update_school_settings(
    data: SchoolSettingsUpdate,
    user: Dict[str, Any] = Depends(require_roles("Admin", "GPK Kokurikulum"))
):
    conn = get_db_connection()
    update_fields = []
    values = []

    fields = {
        "school_name": data.school_name,
        "school_code": data.school_code,
        "address": data.address,
        "phone": data.phone,
        "email": data.email,
        "principal_name": data.principal_name,
        "gpk_koko_name": data.gpk_koko_name,
        "su_koko_name": data.su_koko_name,
        "session_year": data.session_year,
        "logo_url": data.logo_url,
        "letter_template": data.letter_template
    }

    for col, val in fields.items():
        if val is not None:
            update_fields.append(f"{col} = ?")
            values.append(val)

    if update_fields:
        update_fields.append("updated_at = CURRENT_TIMESTAMP")
        values.append(1)
        conn.execute(f"UPDATE school_settings SET {', '.join(update_fields)} WHERE id = ?", tuple(values))
        conn.commit()

    conn.close()
    log_audit(user.get("id"), user.get("username"), user.get("role"), "UPDATE", "SETTINGS", "Kemas kini maklumat profil sekolah")
    return {"status": "success", "message": "Maklumat sekolah berjaya dikemas kini."}

@router.get("/classes")
async def list_classes(user: Dict[str, Any] = Depends(get_current_user)):
    conn = get_db_connection()
    rows = conn.execute("""
    SELECT c.*, COUNT(s.id) as student_count
    FROM classes c
    LEFT JOIN students s ON c.grade = s.grade AND c.class_name = s.class_name AND s.status = 'Aktif'
    GROUP BY c.id
    ORDER BY c.grade ASC, c.class_name ASC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]

@router.post("/classes")
async def create_class(
    data: ClassCreate,
    user: Dict[str, Any] = Depends(require_roles("Admin"))
):
    conn = get_db_connection()
    existing = conn.execute("SELECT id FROM classes WHERE grade = ? AND class_name = ?", (data.grade, data.class_name.strip())).fetchone()
    if existing:
        conn.close()
        raise HTTPException(status_code=400, detail="Kelas ini telah wujud.")

    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO classes (grade, class_name, class_teacher, academic_year)
    VALUES (?, ?, ?, ?)
    """, (data.grade, data.class_name.strip(), data.class_teacher, data.academic_year or "2026/2027"))
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()

    log_audit(user.get("id"), user.get("username"), user.get("role"), "CREATE", "SETTINGS", f"Tambah kelas: {data.class_name}", target_id=new_id)
    return {"status": "success", "message": "Kelas berjaya ditambah.", "id": new_id}

@router.delete("/classes/{class_id}")
async def delete_class(class_id: int, user: Dict[str, Any] = Depends(require_roles("Admin"))):
    conn = get_db_connection()
    conn.execute("DELETE FROM classes WHERE id = ?", (class_id,))
    conn.commit()
    conn.close()

    log_audit(user.get("id"), user.get("username"), user.get("role"), "DELETE", "SETTINGS", f"Padam kelas ID {class_id}", target_id=class_id)
    return {"status": "success", "message": "Kelas berjaya dipadam."}

@router.get("/teachers")
async def list_teachers(user: Dict[str, Any] = Depends(get_current_user)):
    conn = get_db_connection()
    rows = conn.execute("SELECT * FROM teachers ORDER BY name ASC").fetchall()
    conn.close()
    return [dict(r) for r in rows]

@router.post("/teachers")
async def create_teacher(
    data: TeacherCreate,
    user: Dict[str, Any] = Depends(require_roles("Admin", "GPK Kokurikulum", "Setiausaha Kokurikulum"))
):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO teachers (name, ic_number, phone, email, designation)
    VALUES (?, ?, ?, ?, ?)
    """, (data.name.strip(), data.ic_number, data.phone, data.email, data.designation or "Guru Penolong"))
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()

    log_audit(user.get("id"), user.get("username"), user.get("role"), "CREATE", "SETTINGS", f"Tambah guru: {data.name}", target_id=new_id)
    return {"status": "success", "message": "Guru berjaya ditambah.", "id": new_id}

@router.delete("/teachers/{teacher_id}")
async def delete_teacher(teacher_id: int, user: Dict[str, Any] = Depends(require_deletion_roles())):
    conn = get_db_connection()
    conn.execute("DELETE FROM teachers WHERE id = ?", (teacher_id,))
    conn.commit()
    conn.close()

    log_audit(user.get("id"), user.get("username"), user.get("role"), "DELETE", "SETTINGS", f"Padam guru ID {teacher_id}", target_id=teacher_id)
    return {"status": "success", "message": "Guru berjaya dipadam."}

@router.get("/archives")
async def list_archives(user: Dict[str, Any] = Depends(get_current_user)):
    conn = get_db_connection()
    rows = conn.execute("SELECT * FROM yearly_archives ORDER BY session_year DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]

@router.post("/archive-year")
async def archive_current_year(
    data: ArchiveYearRequest,
    user: Dict[str, Any] = Depends(require_roles("Admin"))
):
    conn = get_db_connection()
    cursor = conn.cursor()

    total_students = conn.execute("SELECT COUNT(*) FROM students WHERE status = 'Aktif'").fetchone()[0]
    total_activities = conn.execute("SELECT COUNT(*) FROM weekly_activities").fetchone()[0]
    total_participations = conn.execute("SELECT COUNT(*) FROM external_participations").fetchone()[0]

    cursor.execute("""
    INSERT OR REPLACE INTO yearly_archives (session_year, archived_by, total_students, total_activities, total_participations, notes)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (data.session_year, user.get("full_name"), total_students, total_activities, total_participations, data.notes))

    conn.commit()
    conn.close()

    log_audit(user.get("id"), user.get("username"), user.get("role"), "ARCHIVE", "SETTINGS", f"Arkib data sesi persekolahan {data.session_year}")
    return {"status": "success", "message": f"Data sesi {data.session_year} berjaya diarkibkan."}

@router.post("/reset-demo")
async def reset_demo_data_endpoint(user: Dict[str, Any] = Depends(require_roles("Admin"))):
    seed_demo_data(force=True)
    log_audit(user.get("id"), user.get("username"), user.get("role"), "RESET_DEMO", "SETTINGS", "Set semula semua data kepada data demonstrasi SK Sungai Dendang")
    return {"status": "success", "message": "Pangkalan data telah berjaya diset semula kepada data demo SK Sungai Dendang!"}

@router.post("/upload-logo")
async def upload_school_logo(
    file: UploadFile = File(...),
    user: Dict[str, Any] = Depends(require_roles("Admin", "GPK Kokurikulum"))
):
    ext = file.filename.split(".")[-1].lower() if "." in file.filename else "svg"
    target_filename = f"school_logo_custom.{ext}"
    target_path = UPLOAD_DIR / target_filename

    with open(target_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    logo_url = f"/static/images/{target_filename}"

    conn = get_db_connection()
    conn.execute("UPDATE school_settings SET logo_url = ?, updated_at = CURRENT_TIMESTAMP WHERE id = 1", (logo_url,))
    conn.commit()
    conn.close()

    log_audit(user.get("id"), user.get("username"), user.get("role"), "UPLOAD_LOGO", "SETTINGS", "Muat naik logo baharu sekolah")
    return {"status": "success", "logo_url": logo_url}
