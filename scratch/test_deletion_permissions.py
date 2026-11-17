import sys
import os
import sqlite3
from fastapi.testclient import TestClient

sys.path.insert(0, r"C:\Antigravity\Sistem Pengurusan Unit Kokurikulum")
from app.main import app
from app.database import get_db_connection

client = TestClient(app)

def test_deletion_permissions():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Find or create test users with different roles
    roles_to_test = {
        "admin": "Admin",
        "gpk_koko": "GPK Kokurikulum",
        "su_sukan": "Setiausaha Sukan",
        "penyelaras": "Penyelaras",
        "guru_penasihat": "Guru Penasihat"
    }

    user_ids = {}
    for uname, rname in roles_to_test.items():
        row = cursor.execute("SELECT id FROM users WHERE username = ?", (uname,)).fetchone()
        if not row:
            cursor.execute(
                "INSERT INTO users (username, password_hash, full_name, role, is_active) VALUES (?, ?, ?, ?, 1)",
                (uname, "testpass", f"Cikgu {rname}", rname)
            )
            user_ids[uname] = cursor.lastrowid
        else:
            user_ids[uname] = row["id"]
            cursor.execute("UPDATE users SET role = ?, is_active = 1 WHERE id = ?", (rname, user_ids[uname]))
    conn.commit()

    print("[1] Testing Cross Country Result Deletion...")
    house = cursor.execute("SELECT id FROM organizations WHERE category = 'Rumah Sukan' LIMIT 1").fetchone()
    house_id = house["id"] if house else 1

    cursor.execute("""
        INSERT INTO cross_country_records (student_id, category, sport_house_id, rank_position, time_recorded, house_points, is_record_broken, remarks)
        SELECT id, 'Lelaki (Tahap 2)', ?, 1, '10:00', 10, 0, 'Test' FROM students LIMIT 1
    """, (house_id,))
    conn.commit()

    # Test Guru Penasihat -> MUST be 403 Forbidden
    client.cookies.set("koko_user_id", str(user_ids["guru_penasihat"]))
    res = client.delete("/api/cross-country/results/Lelaki (Tahap 2)")
    print(f"Guru Penasihat DELETE cross-country: {res.status_code} (Expected: 403)")
    assert res.status_code == 403, f"Expected 403, got {res.status_code}: {res.text}"

    # Test GPK Kokurikulum -> MUST be 200 OK
    client.cookies.set("koko_user_id", str(user_ids["gpk_koko"]))
    res = client.delete("/api/cross-country/results/Lelaki (Tahap 2)")
    print(f"GPK Kokurikulum DELETE cross-country: {res.status_code} (Expected: 200)")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"

    print("\n[2] Testing Activity Deletion...")
    cursor.execute("""
        INSERT INTO weekly_activities (organization_id, title, activity_date, start_time, end_time, venue, status)
        SELECT id, 'Aktiviti Ujian', '2026-11-20', '14:00', '16:00', 'Padang', 'Draf' FROM organizations LIMIT 1
    """)
    test_act_id = cursor.lastrowid
    conn.commit()

    # Guru Penasihat -> MUST be 403 Forbidden
    client.cookies.set("koko_user_id", str(user_ids["guru_penasihat"]))
    res = client.delete(f"/api/activities/{test_act_id}")
    print(f"Guru Penasihat DELETE activity: {res.status_code} (Expected: 403)")
    assert res.status_code == 403, f"Expected 403, got {res.status_code}: {res.text}"

    # Penyelaras -> MUST be 200 OK
    client.cookies.set("koko_user_id", str(user_ids["penyelaras"]))
    res = client.delete(f"/api/activities/{test_act_id}")
    print(f"Penyelaras DELETE activity: {res.status_code} (Expected: 200)")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"

    print("\n[3] Testing Sports Event Deletion...")
    cursor.execute("""
        INSERT INTO school_sports_events (event_name, category, gender, event_type, status)
        VALUES ('Acara Ujian 100M', 'Tahap 2', 'Lelaki', 'Balapan', 'Pendaftaran')
    """)
    test_event_id = cursor.lastrowid
    conn.commit()

    # Guru Penasihat -> MUST be 403 Forbidden
    client.cookies.set("koko_user_id", str(user_ids["guru_penasihat"]))
    res = client.delete(f"/api/sports/events/{test_event_id}")
    print(f"Guru Penasihat DELETE sports event: {res.status_code} (Expected: 403)")
    assert res.status_code == 403, f"Expected 403, got {res.status_code}: {res.text}"

    # Setiausaha Sukan -> MUST be 200 OK
    client.cookies.set("koko_user_id", str(user_ids["su_sukan"]))
    res = client.delete(f"/api/sports/events/{test_event_id}")
    print(f"Setiausaha Sukan DELETE sports event: {res.status_code} (Expected: 200)")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"

    print("\n[4] Testing Permission Letter Deletion...")
    cursor.execute("""
        INSERT INTO permission_letters (letter_no, program_name, destination_venue, start_datetime, end_datetime, organizer, accompanying_teachers)
        VALUES ('TEST/01', 'Surat Lawatan Ujian', 'Ipoh', '2026-12-01 08:00', '2026-12-01 17:00', 'Unit Koko', 'En. Ali')
    """)
    test_letter_id = cursor.lastrowid
    conn.commit()

    # Guru Penasihat -> MUST be 403 Forbidden
    client.cookies.set("koko_user_id", str(user_ids["guru_penasihat"]))
    res = client.delete(f"/api/permission-letters/{test_letter_id}")
    print(f"Guru Penasihat DELETE permission letter: {res.status_code} (Expected: 403)")
    assert res.status_code == 403, f"Expected 403, got {res.status_code}: {res.text}"

    # Admin -> MUST be 200 OK
    client.cookies.set("koko_user_id", str(user_ids["admin"]))
    res = client.delete(f"/api/permission-letters/{test_letter_id}")
    print(f"Admin DELETE permission letter: {res.status_code} (Expected: 200)")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"

    print("\n[5] Testing Student Deletion...")
    cursor.execute("""
        INSERT INTO students (full_name, ic_number, class_name, gender, grade)
        VALUES ('Murid Ujian Padam', '150101089999', '4 Cemerlang', 'Lelaki', 4)
    """)
    test_student_id = cursor.lastrowid
    conn.commit()

    # Guru Penasihat -> MUST be 403 Forbidden
    client.cookies.set("koko_user_id", str(user_ids["guru_penasihat"]))
    res = client.delete(f"/api/students/{test_student_id}")
    print(f"Guru Penasihat DELETE student: {res.status_code} (Expected: 403)")
    assert res.status_code == 403, f"Expected 403, got {res.status_code}: {res.text}"

    # GPK Kokurikulum -> MUST be 200 OK
    client.cookies.set("koko_user_id", str(user_ids["gpk_koko"]))
    res = client.delete(f"/api/students/{test_student_id}")
    print(f"GPK Kokurikulum DELETE student: {res.status_code} (Expected: 200)")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"

    print("\n[6] Testing Organization Member Removal...")
    org = cursor.execute("SELECT id FROM organizations LIMIT 1").fetchone()
    org_id = org["id"]
    st = cursor.execute("SELECT id FROM students LIMIT 1").fetchone()
    st_id = st["id"] if st else 1
    cursor.execute("""
        INSERT OR IGNORE INTO organization_members (organization_id, student_id, status)
        VALUES (?, ?, 'Aktif')
    """, (org_id, st_id))
    conn.commit()

    # Guru Penasihat -> MUST be 403 Forbidden
    client.cookies.set("koko_user_id", str(user_ids["guru_penasihat"]))
    res = client.delete(f"/api/organizations/{org_id}/members/{st_id}")
    print(f"Guru Penasihat DELETE org member: {res.status_code} (Expected: 403)")
    assert res.status_code == 403, f"Expected 403, got {res.status_code}: {res.text}"

    # Admin -> MUST be 200 OK
    client.cookies.set("koko_user_id", str(user_ids["admin"]))
    res = client.delete(f"/api/organizations/{org_id}/members/{st_id}")
    print(f"Admin DELETE org member: {res.status_code} (Expected: 200)")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"

    conn.close()
    print("\n ALL TESTS PASSED! Strict role-based deletion permissions verified successfully across all modules!")

if __name__ == "__main__":
    test_deletion_permissions()
