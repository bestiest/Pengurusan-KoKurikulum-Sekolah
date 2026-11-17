import sys
import io
import re
from fastapi.testclient import TestClient

sys.path.insert(0, r"C:\Antigravity\Sistem Pengurusan Unit Kokurikulum")

from app.main import app
from app.database import get_db_connection

client = TestClient(app)

def login(username, password):
    res = client.post("/api/auth/login", json={"username": username, "password": password})
    assert res.status_code == 200, f"Failed to login as {username}: {res.text}"
    return {"koko_user_id": str(res.json()["user"]["id"])}

def run_tests():
    print("=== STARTING ACTIVITY DELETE & R02 COLUMN ORDER TESTS ===")
    
    # 1. Login as GPK Kokurikulum
    cookies_gpk = login("gpk_koko", "aba6038")
    print("✓ Successfully authenticated as GPK Kokurikulum")

    # 2. Create a test activity to delete
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
    INSERT INTO weekly_activities (
        organization_id, activity_date, start_time, end_time, venue,
        title, objectives, description_rundown, status, academic_year
    ) VALUES (
        1, '2026-11-20', '14:00', '16:00', 'Padang Sekolah',
        'Ujian Latihan Padam Test Activity', 'Objektif Ujian', 'Penerangan ringkas', 'Draf', '2026/2027'
    )
    """)
    act_id = cur.lastrowid
    
    # Also insert associated attendance session
    cur.execute("""
    INSERT INTO attendance_sessions (
        organization_id, session_date, activity_title, venue, academic_year
    ) VALUES (
        1, '2026-11-20', 'Ujian Latihan Padam Test Activity', 'Padang Sekolah', '2026/2027'
    )
    """)
    sess_id = cur.lastrowid
    conn.commit()
    conn.close()
    print(f"✓ Created test activity ID {act_id} and attendance session ID {sess_id}")

    # 3. Test deleting the activity as GPK Kokurikulum
    res_del = client.delete(f"/api/activities/{act_id}", cookies=cookies_gpk)
    assert res_del.status_code == 200, f"Failed to delete activity: {res_del.text}"
    del_data = res_del.json()
    assert del_data["status"] == "success"
    print(f"✓ Delete API response: {del_data['message']}")

    # Verify deletion in database
    conn = get_db_connection()
    remaining_act = conn.execute("SELECT id FROM weekly_activities WHERE id = ?", (act_id,)).fetchone()
    assert remaining_act is None, "Activity should be deleted from DB"
    remaining_sess = conn.execute("SELECT id FROM attendance_sessions WHERE id = ?", (sess_id,)).fetchone()
    assert remaining_sess is None, "Associated attendance session should also be cleaned up"
    conn.close()
    print("✓ Database verified: activity & session cleanly deleted")

    # 4. Test deleting non-existent activity returns 404
    res_404 = client.delete("/api/activities/999999", cookies=cookies_gpk)
    assert res_404.status_code == 404, f"Expected 404, got {res_404.status_code}"
    print("✓ 404 verified for non-existent activity")

    # 5. Check Borang R02 Column Order in app.js
    with open(r"C:\Antigravity\Sistem Pengurusan Unit Kokurikulum\app\static\js\app.js", "r", encoding="utf-8") as f:
        js_content = f.read()

    # Verify table headers in R02
    r02_section = re.search(r"<!-- 3\. JADUAL SENARAI PEMAIN.*?-->\s*<table.*?<thead>(.*?)</thead>", js_content, re.DOTALL)
    assert r02_section is not None, "R02 table headers section not found in app.js"
    headers_html = r02_section.group(1)
    
    # Extract header text order
    th_matches = re.findall(r"<th[^>]*>(.*?)</th>", headers_html, re.DOTALL)
    cleaned_headers = [re.sub(r"<[^>]+>", "", h).strip() for h in th_matches]
    print(f"✓ Extracted R02 Table Headers: {cleaned_headers}")

    expected_headers = [
        "Bil",
        "Nama Pemain",
        "No. Surat Beranak / No. KP",
        "No. Jersi",
        "Sekolah"
    ]
    assert cleaned_headers == expected_headers, f"Expected headers {expected_headers}, got {cleaned_headers}"
    print("✓ Header order verified: 'No. Jersi' is directly between 'No. Surat Beranak / No. KP' and 'Sekolah'")

    # Verify table row cells order in R02
    r02_tbody = re.search(r"<tbody>\s*\$\{players\.map\(\(pl, idx\) => `\s*<tr[^>]*>(.*?)</tr>", js_content, re.DOTALL)
    assert r02_tbody is not None, "R02 table row template not found in app.js"
    row_html = r02_tbody.group(1)
    
    # Verify that jersey-input appears after ic and before school in the row
    name_pos = row_html.find("${pl.name || '&nbsp;'}")
    ic_pos = row_html.find("${pl.ic || '&nbsp;'}")
    jersey_pos = row_html.find("jersey-input")
    school_pos = row_html.find("${pl.school || '&nbsp;'}")

    assert name_pos != -1, "Player name placeholder not found"
    assert ic_pos != -1, "IC placeholder not found"
    assert jersey_pos != -1, "Jersey input placeholder not found"
    assert school_pos != -1, "School placeholder not found"

    assert name_pos < ic_pos < jersey_pos < school_pos, (
        f"Row column order incorrect! Expected name < ic < jersey < school, but got positions: "
        f"name={name_pos}, ic={ic_pos}, jersey={jersey_pos}, school={school_pos}"
    )
    print("✓ Row cell order verified: Nama Pemain -> No KP -> No. Jersi -> Sekolah")

    # 6. Verify delete button is present on activity cards
    assert "app.deleteActivity(" in js_content, "app.deleteActivity not found in app.js"
    assert "btn-delete-activity-modal" in js_content, "btn-delete-activity-modal not referenced in app.js"
    print("✓ Frontend delete buttons and methods verified in app.js")

    print("\n=== ALL TESTS PASSED SUCCESSFULLY! ===")

if __name__ == "__main__":
    run_tests()
