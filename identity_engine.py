import os
import hashlib
from memory_module import save_setting, get_setting
from dotenv import load_dotenv

load_dotenv()

def _hash(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def setup_identity():
    admin_pass = os.getenv("ADMIN_PASSWORD")
    if not admin_pass:
        print("[NURI.IDENTITY] XATO: ADMIN_PASSWORD .env da yo'q!")
        return
    existing = get_setting("admin_password_hash")
    if not existing:
        save_setting("admin_password_hash", _hash(admin_pass))
    print("[NURI.IDENTITY] Identifikatsiya tizimi yuklandi ✅")

def verify_user_password(password: str) -> bool:
    admin_pass = os.getenv("ADMIN_PASSWORD")
    if password == admin_pass:
        return False

    inner_pass = os.getenv("NURI_INNER_PASSWORD", "root")
    if password == inner_pass:
        return True

    stored = get_setting(f"user_pass_{_hash(password)}")
    return bool(stored)

def get_username_by_password(password: str) -> str:
    inner_pass = os.getenv("NURI_INNER_PASSWORD", "root")
    if password == inner_pass:
        return "user"
    stored = get_setting(f"user_pass_{_hash(password)}")
    return stored if stored else "user"

def add_user_password(username: str, password: str):
    if not username or not password:
        return
    save_setting(f"user_pass_{_hash(password)}", username)
    print(f"[NURI.IDENTITY] '{username}' uchun parol qo'shildi.")

def verify_access(password: str) -> str:
    admin_pass = os.getenv("ADMIN_PASSWORD")
    if password == admin_pass:
        return "admin"
    if verify_user_password(password):
        return "user"
    return "stranger"
