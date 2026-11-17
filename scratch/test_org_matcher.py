import re
import sqlite3

conn = sqlite3.connect(r"C:\Antigravity\Sistem Pengurusan Unit Kokurikulum\data\kokurikulum.db")
conn.row_factory = sqlite3.Row
org_rows = conn.execute("SELECT id, name, category FROM organizations").fetchall()
conn.close()

def build_org_lookup(org_rows):
    lookup = {
        'Rumah Sukan': {},
        'Unit Beruniform': {},
        'Kelab & Persatuan': {},
        'Sukan & Permainan': {},
        'all': {}
    }
    for r in org_rows:
        org_id = r["id"]
        name = r["name"].strip()
        cat = r["category"]
        
        lookup['all'][name.lower()] = org_id
        if cat in lookup:
            lookup[cat][name.lower()] = org_id
            
        clean = re.sub(r'[^a-zA-Z0-9\s]', ' ', name).lower().split()
        for word in clean:
            if len(word) > 2 and word not in ('rumah', 'kelab', 'persatuan', 'unit', 'badan', 'dan'):
                if cat in lookup:
                    lookup[cat].setdefault(word, org_id)
                lookup['all'].setdefault(word, org_id)
                
    return lookup

def find_org_id(query_str, category, lookup):
    if not query_str:
        return None
    q = query_str.strip().lower()
    cat_dict = lookup.get(category, {})
    
    if q in cat_dict:
        return cat_dict[q]
    if q in lookup['all']:
        return lookup['all'][q]
        
    for name, org_id in cat_dict.items():
        if q in name or name in q:
            return org_id
            
    q_words = [w for w in re.sub(r'[^a-zA-Z0-9\s]', ' ', q).split() if len(w) > 2]
    for w in q_words:
        if w in cat_dict:
            return cat_dict[w]
    return None

lookup = build_org_lookup(org_rows)
test_queries = [
    ("Merah", "Rumah Sukan"),
    ("Rumah Bendahara (Merah)", "Rumah Sukan"),
    ("Bendahara", "Rumah Sukan"),
    ("Hijau", "Rumah Sukan"),
    ("Pengakap", "Unit Beruniform"),
    ("TKRS", "Unit Beruniform"),
    ("Bahasa Melayu", "Kelab & Persatuan"),
    ("Bola Jaring", "Sukan & Permainan"),
    ("Hoki", "Sukan & Permainan"),
]

for q, cat in test_queries:
    res = find_org_id(q, cat, lookup)
    print(f"Query: '{q}' [{cat}] -> ID: {res}")
