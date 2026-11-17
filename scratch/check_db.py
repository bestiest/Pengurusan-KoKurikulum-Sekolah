import sqlite3
import os

db_path = r"C:\Antigravity\Sistem Pengurusan Unit Kokurikulum\data\kokurikulum.db"
print("File exists:", os.path.exists(db_path))
try:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM students")
    print("Total students:", cur.fetchone()[0])
    cur.execute("SELECT id, full_name, ic_number FROM students LIMIT 5")
    for r in cur.fetchall():
        print(r)
    conn.close()
except Exception as e:
    print("Error:", e)
