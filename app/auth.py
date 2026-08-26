import hashlib
import hmac
import secrets
from typing import Optional, Dict, Any
from fastapi import Request, HTTPException, Depends
from app.database import get_db_connection

SECRET_SALT = "sk_sungai_dendang_koko_secret_2026"

def hash_password(password: str) -> str:
    return hashlib.sha256(f"{password}_{SECRET_SALT}".encode()).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return hmac.compare_digest(hash_password(plain_password), hashed_password)

def get_current_user(request: Request) -> Dict[str, Any]:
    # Check session cookie or header
    user_id = request.cookies.get("koko_user_id") or request.headers.get("X-User-Id")
    
    conn = get_db_connection()
    if user_id:
        try:
            user = conn.execute("SELECT * FROM users WHERE id = ? AND is_active = 1", (int(user_id),)).fetchone()
            if user:
                conn.close()
                return dict(user)
        except Exception:
            pass
    
    # Default fallback to Admin for seamless demo/testing if not logged in
    default_user = conn.execute("SELECT * FROM users WHERE username = 'admin'").fetchone()
    conn.close()
    if default_user:
        return dict(default_user)
    
    return {
        "id": 1,
        "username": "admin",
        "full_name": "Pentadbir Sistem (Admin)",
        "role": "Admin",
        "email": "admin@sksungaidendang.edu.my"
    }

def require_roles(*allowed_roles):
    def role_checker(user: Dict[str, Any] = Depends(get_current_user)):
        user_role = user.get("role")
        if user_role not in allowed_roles and "Admin" not in allowed_roles and user_role != "Admin":
            raise HTTPException(status_code=403, detail="Akses ditolak. Anda tidak mempunyai kebenaran yang mencukupi.")
        return user
    return role_checker
