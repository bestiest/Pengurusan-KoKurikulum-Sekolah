import hashlib
import hmac
from typing import Optional, Dict, Any
from fastapi import Request, HTTPException, Depends
from app.database import get_db_connection

SECRET_SALT = "sk_sungai_dendang_koko_secret_2026"
DEFAULT_PASSWORD = "aba6038"

def hash_password(password: str) -> str:
    return hashlib.sha256(f"{password.strip()}_{SECRET_SALT}".encode()).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    if hmac.compare_digest(hash_password(plain_password), hashed_password):
        return True
    if hmac.compare_digest(hash_password(plain_password.lower()), hashed_password):
        return True
    return False

def get_current_user(request: Request) -> Dict[str, Any]:
    # Check session cookie or header
    user_id = request.cookies.get("koko_user_id") or request.headers.get("X-User-Id")
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Sila log masuk terlebih dahulu.")
    
    conn = get_db_connection()
    try:
        user = conn.execute("SELECT * FROM users WHERE id = ? AND is_active = 1", (int(user_id),)).fetchone()
        conn.close()
        if user:
            return dict(user)
    except Exception:
        conn.close()
        pass

    raise HTTPException(status_code=401, detail="Sesi telah tamat atau tidak sah. Sila log masuk semula.")

def get_optional_user(request: Request) -> Optional[Dict[str, Any]]:
    user_id = request.cookies.get("koko_user_id") or request.headers.get("X-User-Id")
    if not user_id:
        return None
    try:
        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE id = ? AND is_active = 1", (int(user_id),)).fetchone()
        conn.close()
        if user:
            return dict(user)
    except Exception:
        pass
    return None

def require_roles(*allowed_roles):
    def role_checker(user: Dict[str, Any] = Depends(get_current_user)):
        user_role = user.get("role")
        if user_role != "Admin" and user_role not in allowed_roles:
            raise HTTPException(status_code=403, detail="Akses ditolak. Anda tidak mempunyai kebenaran yang mencukupi.")
        return user
    return role_checker

DELETION_ALLOWED_ROLES = [
    "Admin",
    "GPK Kokurikulum",
    "Setiausaha Kokurikulum",
    "Setiausaha Sukan",
    "Penyelaras Kokurikulum",
    "Penyelaras"
]

def require_deletion_roles():
    def role_checker(user: Dict[str, Any] = Depends(get_current_user)):
        user_role = user.get("role") or ""
        # Strictly block Guru Penasihat and Guru Pemimpin from deleting anything
        if user_role in ["Guru Penasihat", "Guru Pemimpin"]:
            raise HTTPException(
                status_code=403,
                detail="Akses ditolak. Guru Penasihat tidak dibenarkan memadam sebarang maklumat, laporan, atau keputusan."
            )
        if user_role != "Admin":
            allowed_normalized = [r.lower().replace(" ", "").replace("_", "") for r in DELETION_ALLOWED_ROLES]
            user_normalized = user_role.lower().replace(" ", "").replace("_", "")
            if not any(user_normalized == r or r in user_normalized or user_normalized in r for r in allowed_normalized):
                raise HTTPException(
                    status_code=403,
                    detail="Akses ditolak. Hanya akaun Admin, GPK Kokurikulum, Penyelaras, dan Setiausaha Sukan/Kokurikulum sahaja yang dibenarkan memadam maklumat."
                )
        return user
    return role_checker

