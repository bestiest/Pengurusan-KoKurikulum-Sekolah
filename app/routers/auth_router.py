from fastapi import APIRouter, HTTPException, Depends, Response, Request
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from app.database import get_db_connection, log_audit
from app.auth import hash_password, verify_password, get_current_user, require_roles
from app.models import UserLogin, UserCreate, UserUpdate

router = APIRouter(prefix="/api/auth", tags=["Autentikasi & Pengguna"])

class RoleSwitchRequest(BaseModel):
    role: str
    username: Optional[str] = None

@router.post("/login")
async def login(data: UserLogin, response: Response):
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE username = ? AND is_active = 1", (data.username.strip(),)).fetchone()
    conn.close()

    if not user:
        raise HTTPException(status_code=400, detail="ID Pengguna atau Kata Laluan tidak sah.")

    user_dict = dict(user)
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

@router.post("/logout")
async def logout(response: Response, user: Dict[str, Any] = Depends(get_current_user)):
    response.delete_cookie("koko_user_id")
    log_audit(user.get("id"), user.get("username"), user.get("role"), "LOGOUT", "AUTH", f"Pengguna {user.get('username')} log keluar.")
    return {"status": "success", "message": "Log keluar berjaya."}

@router.get("/users")
async def list_users(user: Dict[str, Any] = Depends(require_roles("Admin", "GPK Kokurikulum"))):
    conn = get_db_connection()
    rows = conn.execute("SELECT id, username, full_name, role, email, phone, assigned_category, assigned_org_ids, is_active, created_at FROM users ORDER BY id ASC").fetchall()
    conn.close()
    return [dict(r) for r in rows]

@router.post("/users")
async def create_user(data: UserCreate, user: Dict[str, Any] = Depends(require_roles("Admin"))):
    conn = get_db_connection()
    existing = conn.execute("SELECT id FROM users WHERE username = ?", (data.username.strip(),)).fetchone()
    if existing:
        conn.close()
        raise HTTPException(status_code=400, detail="Nama pengguna (username) telah wujud.")

    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO users (username, password_hash, full_name, role, email, phone, assigned_category, assigned_org_ids, is_active)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
    """, (
        data.username.strip(),
        hash_password(data.password),
        data.full_name.strip(),
        data.role,
        data.email,
        data.phone,
        data.assigned_category,
        data.assigned_org_ids
    ))
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()

    log_audit(user.get("id"), user.get("username"), user.get("role"), "CREATE", "USERS", f"Cipta pengguna baharu: {data.username} ({data.role})", target_id=new_id)
    return {"status": "success", "message": "Pengguna berjaya ditambah.", "id": new_id}

@router.put("/users/{user_id}")
async def update_user(user_id: int, data: UserUpdate, user: Dict[str, Any] = Depends(require_roles("Admin"))):
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
async def delete_user(user_id: int, user: Dict[str, Any] = Depends(require_roles("Admin"))):
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
