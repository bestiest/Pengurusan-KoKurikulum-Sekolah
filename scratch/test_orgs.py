import sqlite3

conn = sqlite3.connect(r"C:\Antigravity\Sistem Pengurusan Unit Kokurikulum\data\kokurikulum.db")
conn.row_factory = sqlite3.Row
rows = conn.execute("SELECT id, name, category FROM organizations ORDER BY category, id").fetchall()
print(f"Total organizations: {len(rows)}")
for r in rows:
    print(f"[{r['id']}] [{r['category']}] {r['name']}")
conn.close()
