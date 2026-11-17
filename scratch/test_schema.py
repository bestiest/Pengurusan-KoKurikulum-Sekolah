import sqlite3

conn = sqlite3.connect(r"C:\Antigravity\Sistem Pengurusan Unit Kokurikulum\data\kokurikulum.db")
cur = conn.cursor()
cur.execute("SELECT name, sql FROM sqlite_master WHERE type='table' AND name IN ('students', 'organization_members')")
for name, sql in cur.fetchall():
    print(f"Table: {name}")
    print(sql)
    print("-" * 50)
cur.execute("SELECT name, sql FROM sqlite_master WHERE type='index' AND tbl_name IN ('students', 'organization_members')")
for name, sql in cur.fetchall():
    print(f"Index: {name}: {sql}")
conn.close()
