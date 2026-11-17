import sys
import os
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path("C:/Antigravity/Sistem Pengurusan Unit Kokurikulum")
sys.path.insert(0, str(BASE_DIR))

from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db_connection

client = TestClient(app)

def test_conflict_prevention_in_org_members():
    conn = get_db_connection()
    # Find two organizations in the same category, e.g. Rumah Sukan
    orgs = conn.execute("SELECT id, name, category FROM organizations WHERE category = 'Rumah Sukan' LIMIT 2").fetchall()
    assert len(orgs) >= 2, "Need at least 2 sport houses"
    org1 = dict(orgs[0])
    org2 = dict(orgs[1])

    # Find or assign a student to org1
    student = conn.execute("SELECT id, full_name, sport_house_id FROM students WHERE sport_house_id = ?", (org1["id"],)).fetchone()
    if not student:
        # Pick any student and assign to org1
        s = conn.execute("SELECT id, full_name FROM students LIMIT 1").fetchone()
        conn.execute("UPDATE students SET sport_house_id = ? WHERE id = ?", (org1["id"], s["id"]))
        conn.commit()
        student = conn.execute("SELECT id, full_name, sport_house_id FROM students WHERE id = ?", (s["id"],)).fetchone()

    s_id = student["id"]
    s_name = student["full_name"]
    conn.close()

    # Pass admin header X-User-Id
    headers = {"X-User-Id": "1"}

    # Try to add this student to org2 (different house in same category)
    resp = client.post(f"/api/organizations/{org2['id']}/members", json={"student_ids": [s_id]}, headers=headers)
    print("Status code for conflict add:", resp.status_code)
    print("Response text:", resp.text)
    assert resp.status_code == 400, f"Expected 400 due to category conflict, got {resp.status_code}"
    assert "tidak boleh didaftarkan ke dalam unit berbeza" in resp.text
    assert s_name in resp.text

    print("PASS: Conflict prevention in org members verified successfully!")

def test_borang_r01_and_r02_rendered_html():
    # Read app.js and check string contents for R01 manager blank and R02 Guru Besar
    app_js_path = BASE_DIR / "app" / "static" / "js" / "app.js"
    with open(app_js_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Check R01 manager name is blank dots
    assert '<div style="margin-top: 4px;">Nama : ................................................</div>' in content, "R01 manager name should be dotted blank"
    print("PASS: Borang R01 manager name is blank dots!")

    # Check R02 Guru Besar in right column
    assert '<div style="font-weight: bold; font-size: 9.5pt; margin-top: 2px; margin-bottom: 6px;">Guru Besar</div>' in content, "R02 signature heading should be Guru Besar"
    assert '${school.principal_name || \'................................................\'}' in content, "R02 should include school.principal_name"
    print("PASS: Borang R02 signature block changed to Guru Besar!")

if __name__ == "__main__":
    test_conflict_prevention_in_org_members()
    test_borang_r01_and_r02_rendered_html()
    print("\nALL VERIFICATIONS PASSED!")
