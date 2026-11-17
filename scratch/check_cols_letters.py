import sqlite3

conn = sqlite3.connect(r"C:\Antigravity\Sistem Pengurusan Unit Kokurikulum\data\kokurikulum.db")
cols = [r[1] for r in conn.execute("PRAGMA table_info(permission_letters)").fetchall()]
print("permission_letters cols:", cols)
