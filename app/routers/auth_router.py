from fastapi import APIRouter, HTTPException, Depends, Response, Request
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from app.database import get_db_connection, log_audit
from app.auth import hash_password, verify_password, get_current_user, require_roles, require_deletion_roles
from app.models import UserLogin, UserCreate, UserUpdate

router = APIRouter(prefix="/api/auth", tags=["Autentikasi & Pengguna"])

class RoleSwitchRequest(BaseModel):
    role: str
    username: Optional[str] = None

class PublicTeacherRegister(BaseModel):
    username: str
    password: Optional[str] = "aba6038"
    full_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    assigned_category: Optional[str] = None

@router.get("/active-users")
async def get_active_users():
    """Returns active user accounts for login ID selection dropdown."""
    conn = get_db_connection()
    rows = conn.execute("""
        SELECT username, full_name, role 
        FROM users 
        WHERE is_active = 1 AND (approval_status IS NULL OR approval_status = 'approved')
        ORDER BY 
            CASE role 
                WHEN 'Admin' THEN 1 
                WHEN 'GPK Kokurikulum' THEN 2 
                WHEN 'Setiausaha Kokurikulum' THEN 3 
                ELSE 4 
            END, full_name ASC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]

@router.post("/register")
async def public_register_teacher(data: PublicTeacherRegister):
    """Allows new teachers to apply/register an ID. Pending until approved by Admin/GPK Koko."""
    username = data.username.strip()
    full_name = data.full_name.strip()
    
    if not username or not full_name:
        raise HTTPException(status_code=400, detail="Sila lengkapkan ID Pengguna (Username) dan Nama Penuh.")

    conn = get_db_connection()
    existing = conn.execute("SELECT id FROM users WHERE LOWER(username) = LOWER(?)", (username,)).fetchone()
    if existing:
        conn.close()
        raise HTTPException(status_code=400, detail=f"ID Pengguna '{username}' telah didaftarkan. Sila pilih ID lain.")

    raw_password = data.password.strip() if (data.password and data.password.strip()) else "aba6038"

    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO users (username, password_hash, full_name, role, email, phone, assigned_category, is_active, approval_status)
    VALUES (?, ?, ?, 'Guru Penasihat', ?, ?, ?, 0, 'pending')
    """, (
        username,
        hash_password(raw_password),
        full_name,
        data.email.strip() if data.email else None,
        data.phone.strip() if data.phone else None,
        data.assigned_category.strip() if data.assigned_category else None
    ))
    new_id = cursor.lastrowid

    # Add into teachers table as well (inactive until approved)
    t_exists = conn.execute("SELECT id FROM teachers WHERE LOWER(name) = LOWER(?)", (full_name,)).fetchone()
    if not t_exists:
        cursor.execute("""
        INSERT INTO teachers (name, phone, email, designation, is_active)
        VALUES (?, ?, ?, 'Guru Penasihat', 0)
        """, (full_name, data.phone.strip() if data.phone else None, data.email.strip() if data.email else None))

    conn.commit()
    conn.close()

    log_audit(None, username, "GUEST", "REGISTER_REQUEST", "USERS", f"Permohonan pendaftaran Guru Penasihat: {username} ({full_name})", target_id=new_id)

    return {
        "status": "success",
        "message": f"Pendaftaran berjaya dihantar! Akaun anda ({username}) kini sedang menunggu pengesahan dan kelulusan daripada Admin atau GPK Kokurikulum.",
        "id": new_id
    }

@router.post("/login")
async def login(data: UserLogin, response: Response):
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE LOWER(username) = LOWER(?)", (data.username.strip(),)).fetchone()
    conn.close()

    if not user:
        raise HTTPException(status_code=400, detail="ID Pengguna atau Kata Laluan tidak sah.")

    user_dict = dict(user)

    # Check approval / active status
    if user_dict.get("is_active") != 1 or user_dict.get("approval_status") == "pending":
        raise HTTPException(
            status_code=403, 
            detail="Akaun anda sedang menunggu pengesahan & kelulusan daripada Admin atau GPK Kokurikulum. Sila hubungi pihak pentadbir sekolah."
        )

    if not verify_password(data.password, user_dict["password_hash"]):
        raise HTTPException(status_code=400, detail="ID Pengguna atau Kata Laluan tidak sah.")

    response.set_cookie(
        key="koko_user_id",
        value=str(user_dict["id"]),
        max_age=60 * 60 * 24 * 7,
        httponly=False,
        samesite="lax"
    )

    log_audit(user_dict["id"], user_dict["username"], user_dict["role"], "LOGIN", "AUTH", f"Pengguna {user_dict['username']} berjaya log masuk.")

    del user_dict["password_hash"]
    return {"status": "success", "message": "Log masuk berjaya.", "user": user_dict}

@router.post("/switch-role")
async def switch_role(data: RoleSwitchRequest, response: Response):
    conn = get_db_connection()
    user = None
    if data.username:
        user = conn.execute("SELECT * FROM users WHERE username = ? AND is_active = 1", (data.username,)).fetchone()
    
    if not user:
        user = conn.execute("SELECT * FROM users WHERE role = ? AND is_active = 1 LIMIT 1", (data.role,)).fetchone()
    
    conn.close()

    if not user:
        raise HTTPException(status_code=404, detail=f"Akaun dengan peranan '{data.role}' tidak dijumpai.")

    user_dict = dict(user)
    response.set_cookie(
        key="koko_user_id",
        value=str(user_dict["id"]),
        max_age=60 * 60 * 24 * 7,
        httponly=False,
        samesite="lax"
    )

    log_audit(user_dict["id"], user_dict["username"], user_dict["role"], "SWITCH_ROLE", "AUTH", f"Tukar peranan aktif kepada {user_dict['role']}")

    del user_dict["password_hash"]
    return {"status": "success", "message": f"Peranan berjaya ditukar kepada {user_dict['role']}.", "user": user_dict}

@router.get("/me")
async def get_me(user: Dict[str, Any] = Depends(get_current_user)):
    user_copy = dict(user)
    if "password_hash" in user_copy:
        del user_copy["password_hash"]
    
    conn = get_db_connection()
    school = conn.execute("SELECT * FROM school_settings WHERE id = 1").fetchone()
    conn.close()

    return {
        "user": user_copy,
        "school": dict(school) if school else None
    }

class UpdateProfileRequest(BaseModel):
    username: Optional[str] = None
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    password: Optional[str] = None

@router.put("/profile")
async def update_my_profile(data: UpdateProfileRequest, user: Dict[str, Any] = Depends(get_current_user)):
    user_id = user["id"]
    conn = get_db_connection()
    
    if data.username and data.username.strip() and data.username.strip().lower() != user["username"].lower():
        existing = conn.execute("SELECT id FROM users WHERE LOWER(username) = LOWER(?) AND id != ?", (data.username.strip(), user_id)).fetchone()
        if existing:
            conn.close()
            raise HTTPException(status_code=400, detail="ID Pengguna (username) tersebut telah digunakan oleh akaun lain.")

    update_fields = []
    values = []

    if data.username and data.username.strip():
        update_fields.append("username = ?")
        values.append(data.username.strip())

    if data.full_name and data.full_name.strip():
        update_fields.append("full_name = ?")
        values.append(data.full_name.strip())

    if data.email is not None:
        update_fields.append("email = ?")
        values.append(data.email.strip() if data.email else None)

    if data.phone is not None:
        update_fields.append("phone = ?")
        values.append(data.phone.strip() if data.phone else None)

    if data.password and data.password.strip():
        update_fields.append("password_hash = ?")
        values.append(hash_password(data.password.strip()))

    if update_fields:
        values.append(user_id)
        query = f"UPDATE users SET {', '.join(update_fields)} WHERE id = ?"
        conn.execute(query, tuple(values))
        conn.commit()

    updated_user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()

    updated_dict = dict(updated_user)
    if "password_hash" in updated_dict:
        del updated_dict["password_hash"]

    log_audit(user_id, updated_dict["username"], updated_dict["role"], "UPDATE_PROFILE", "USERS", f"Pengguna {updated_dict['username']} mengemas kini ID/profil/kata laluan sendiri.", target_id=user_id)
    return {"status": "success", "message": "Maklumat ID dan profil anda berjaya dikemas kini.", "user": updated_dict}

@router.post("/logout")
async def logout(response: Response, user: Dict[str, Any] = Depends(get_current_user)):
    response.delete_cookie("koko_user_id")
    log_audit(user.get("id"), user.get("username"), user.get("role"), "LOGOUT", "AUTH", f"Pengguna {user.get('username')} log keluar.")
    return {"status": "success", "message": "Log keluar berjaya."}

@router.get("/pending-users")
async def list_pending_users(user: Dict[str, Any] = Depends(require_roles("Admin", "GPK Kokurikulum", "Setiausaha Kokurikulum"))):
    """List new user registrations waiting for Admin/GPK Koko approval."""
    conn = get_db_connection()
    rows = conn.execute("""
        SELECT id, username, full_name, role, email, phone, assigned_category, is_active, approval_status, created_at 
        FROM users 
        WHERE approval_status = 'pending' OR is_active = 0
        ORDER BY id DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]

@router.post("/users/{user_id}/approve")
async def approve_user(user_id: int, user: Dict[str, Any] = Depends(require_roles("Admin", "GPK Kokurikulum", "Setiausaha Kokurikulum"))):
    """Approve a pending teacher registration."""
    conn = get_db_connection()
    target = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if not target:
        conn.close()
        raise HTTPException(status_code=404, detail="Pengguna tidak dijumpai.")
    
    target_dict = dict(target)
    conn.execute("UPDATE users SET is_active = 1, approval_status = 'approved' WHERE id = ?", (user_id,))
    conn.execute("UPDATE teachers SET is_active = 1 WHERE LOWER(name) = LOWER(?)", (target_dict["full_name"],))
    conn.commit()
    conn.close()

    log_audit(user.get("id"), user.get("username"), user.get("role"), "APPROVE_USER", "USERS", f"Luluskan pendaftaran pengguna: {target_dict['username']} ({target_dict['full_name']})", target_id=user_id)
    return {"status": "success", "message": f"Akaun '{target_dict['full_name']}' ({target_dict['username']}) telah berjaya disahkan dan diaktifkan."}

@router.post("/users/{user_id}/reject")
async def reject_user(user_id: int, user: Dict[str, Any] = Depends(require_roles("Admin", "GPK Kokurikulum", "Setiausaha Kokurikulum"))):
    """Reject a pending teacher registration and remove the record."""
    conn = get_db_connection()
    target = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if not target:
        conn.close()
        raise HTTPException(status_code=404, detail="Pengguna tidak dijumpai.")
    
    target_dict = dict(target)
    conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.execute("DELETE FROM teachers WHERE LOWER(name) = LOWER(?) AND is_active = 0", (target_dict["full_name"],))
    conn.commit()
    conn.close()

    log_audit(user.get("id"), user.get("username"), user.get("role"), "REJECT_USER", "USERS", f"Tolak pendaftaran pengguna: {target_dict['username']} ({target_dict['full_name']})", target_id=user_id)
    return {"status": "success", "message": f"Permohonan pendaftaran untuk '{target_dict['full_name']}' ({target_dict['username']}) telah ditolak."}

@router.get("/users")
async def list_users(user: Dict[str, Any] = Depends(require_roles("Admin", "GPK Kokurikulum", "Setiausaha Kokurikulum"))):
    conn = get_db_connection()
    rows = conn.execute("""
        SELECT id, username, full_name, role, email, phone, assigned_category, assigned_org_ids, is_active, approval_status, created_at 
        FROM users 
        ORDER BY id ASC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]

@router.post("/users")
async def create_user(data: UserCreate, user: Dict[str, Any] = Depends(require_roles("Admin", "GPK Kokurikulum", "Setiausaha Kokurikulum"))):
    conn = get_db_connection()
    existing = conn.execute("SELECT id FROM users WHERE LOWER(username) = LOWER(?)", (data.username.strip(),)).fetchone()
    if existing:
        conn.close()
        raise HTTPException(status_code=400, detail="Nama pengguna (username) telah wujud.")

    raw_password = data.password if (data.password and data.password.strip()) else "aba6038"

    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO users (username, password_hash, full_name, role, email, phone, assigned_category, assigned_org_ids, is_active, approval_status)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, 'approved')
    """, (
        data.username.strip(),
        hash_password(raw_password),
        data.full_name.strip(),
        data.role,
        data.email,
        data.phone,
        data.assigned_category,
        data.assigned_org_ids
    ))
    new_id = cursor.lastrowid

    # Also ensure teacher is registered in teachers table
    t_exists = conn.execute("SELECT id FROM teachers WHERE LOWER(name) = LOWER(?)", (data.full_name.strip(),)).fetchone()
    if not t_exists:
        cursor.execute("""
        INSERT INTO teachers (name, phone, email, designation, is_active)
        VALUES (?, ?, ?, ?, 1)
        """, (data.full_name.strip(), data.phone, data.email, data.role))
    else:
        cursor.execute("UPDATE teachers SET is_active = 1 WHERE LOWER(name) = LOWER(?)", (data.full_name.strip(),))

    conn.commit()
    conn.close()

    log_audit(user.get("id"), user.get("username"), user.get("role"), "CREATE", "USERS", f"Cipta/Daftar pengguna guru: {data.username} ({data.role})", target_id=new_id)
    return {"status": "success", "message": f"Guru/Pengguna '{data.full_name}' berjaya didaftarkan dengan kata laluan lalai '{raw_password}'.", "id": new_id}

@router.post("/users/{user_id}/reset-password")
async def reset_user_password(
    user_id: int,
    data: Optional[Dict[str, Any]] = None,
    user: Dict[str, Any] = Depends(require_roles("Admin", "GPK Kokurikulum", "Setiausaha Kokurikulum"))
):
    conn = get_db_connection()
    target = conn.execute("SELECT id, username, full_name FROM users WHERE id = ?", (user_id,)).fetchone()
    if not target:
        conn.close()
        raise HTTPException(status_code=404, detail="Pengguna tidak dijumpai.")

    target_dict = dict(target)
    new_pwd = (data.get("new_password") if data else None) or "aba6038"
    new_hash = hash_password(new_pwd)

    conn.execute("UPDATE users SET password_hash = ? WHERE id = ?", (new_hash, user_id))
    conn.commit()
    conn.close()

    log_audit(user.get("id"), user.get("username"), user.get("role"), "RESET_PASSWORD", "USERS", f"Set semula kata laluan pengguna {target_dict['username']} kepada '{new_pwd}'", target_id=user_id)
    return {
        "status": "success",
        "message": f"Kata laluan untuk '{target_dict['full_name']}' ({target_dict['username']}) telah berjaya diset semula kepada '{new_pwd}'."
    }

@router.put("/users/{user_id}")
async def update_user(user_id: int, data: UserUpdate, user: Dict[str, Any] = Depends(require_roles("Admin", "GPK Kokurikulum", "Setiausaha Kokurikulum"))):
    conn = get_db_connection()
    existing = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if not existing:
        conn.close()
        raise HTTPException(status_code=404, detail="Pengguna tidak dijumpai.")

    update_fields = []
    values = []

    if data.full_name is not None:
        update_fields.append("full_name = ?")
        values.append(data.full_name.strip())
    if data.role is not None:
        update_fields.append("role = ?")
        values.append(data.role)
    if data.email is not None:
        update_fields.append("email = ?")
        values.append(data.email)
    if data.phone is not None:
        update_fields.append("phone = ?")
        values.append(data.phone)
    if data.assigned_category is not None:
        update_fields.append("assigned_category = ?")
        values.append(data.assigned_category)
    if data.assigned_org_ids is not None:
        update_fields.append("assigned_org_ids = ?")
        values.append(data.assigned_org_ids)
    if data.is_active is not None:
        update_fields.append("is_active = ?")
        values.append(data.is_active)
    if data.password:
        update_fields.append("password_hash = ?")
        values.append(hash_password(data.password))

    if update_fields:
        values.append(user_id)
        query = f"UPDATE users SET {', '.join(update_fields)} WHERE id = ?"
        conn.execute(query, tuple(values))
        conn.commit()

    conn.close()
    log_audit(user.get("id"), user.get("username"), user.get("role"), "UPDATE", "USERS", f"Kemas kini pengguna ID: {user_id}", target_id=user_id)
    return {"status": "success", "message": "Pengguna berjaya dikemas kini."}

@router.delete("/users/{user_id}")
async def delete_user(user_id: int, user: Dict[str, Any] = Depends(require_deletion_roles())):
    if user_id == user.get("id"):
        raise HTTPException(status_code=400, detail="Anda tidak boleh memadam akaun anda sendiri semasa log masuk.")

    conn = get_db_connection()
    target = conn.execute("SELECT username FROM users WHERE id = ?", (user_id,)).fetchone()
    if not target:
        conn.close()
        raise HTTPException(status_code=404, detail="Pengguna tidak dijumpai.")

    conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()

    log_audit(user.get("id"), user.get("username"), user.get("role"), "DELETE", "USERS", f"Padam pengguna: {dict(target)['username']}", target_id=user_id)
    return {"status": "success", "message": "Pengguna berjaya dipadam."}
