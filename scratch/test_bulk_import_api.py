import sys
import io
import openpyxl
from fastapi.testclient import TestClient

# Add project root to sys.path
sys.path.insert(0, r"C:\Antigravity\Sistem Pengurusan Unit Kokurikulum")

from app.main import app
from app.database import get_db_connection

client = TestClient(app)

def login_as_admin():
    res = client.post("/api/auth/login", json={"username": "admin", "password": "password"})
    if res.status_code != 200:
        res = client.post("/api/auth/login", json={"username": "admin", "password": "aba6038"})
    assert res.status_code == 200, f"Failed to login: {res.text}"
    user_id = str(res.json()["user"]["id"])
    return {"koko_user_id": user_id}

def run_tests():
    print("=== STARTING BULK IMPORT API INTEGRATION TESTS ===")
    cookies = login_as_admin()
    print("✓ Successfully authenticated as Admin")

    # 1. Test template download
    res_template = client.get("/api/students/template/excel", cookies=cookies)
    assert res_template.status_code == 200, f"Template download failed: {res_template.status_code}"
    wb = openpyxl.load_workbook(io.BytesIO(res_template.content))
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    assert len(rows) >= 3, f"Template should have headers and sample rows, got {len(rows)}"
    print(f"✓ Template download verified: {len(rows)} rows, active sheet '{ws.title}'")

    # Clean up test students before running
    test_ics = ('160101088891', '160202088892', '150707087711', '150808087722', '160303089933', '160404089944')
    conn = get_db_connection()
    conn.execute(f"DELETE FROM students WHERE ic_number IN ({','.join(['?']*len(test_ics))})", test_ics)
    conn.commit()
    initial_count = conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]
    conn.close()
    print(f"✓ Initial student count in DB (after cleanup): {initial_count}")

    # 2. Test importing Excel using the official template format with 2 new students
    wb_test = openpyxl.Workbook()
    ws_test = wb_test.active
    ws_test.append([
        "Nama Penuh", "No KP / MyKid", "Tarikh Lahir (YYYY-MM-DD)", "Jantina (Lelaki/Perempuan)",
        "Tahun (1-6)", "Nama Kelas", "Nama Penjaga", "No Telefon Penjaga",
        "Alamat", "Maklumat Kesihatan", "Rumah Sukan", "Unit Beruniform",
        "Kelab Persatuan", "Sukan Permainan"
    ])
    ws_test.append([
        "AHMAD DANIEL BIN FIRDAUS", "160101088891", "2016-01-01", "Lelaki",
        4, "4 Cemerlang", "Firdaus bin Ramli", "012-3456789",
        "Kampung Melayu, Selama", "Tiada", "Merah", "Pengakap",
        "Bahasa Melayu", "Bola Jaring"
    ])
    ws_test.append([
        "NUR AMALINA BINTI HISHAM", "160202088892", "2016-02-02", "Perempuan",
        4, "4 Cemerlang", "Hisham bin Bakar", "019-8765432",
        "Taman Seri Selama", "Alahan Debu", "Biru", "TKRS",
        "Rukun Negara", "Hoki"
    ])
    buf = io.BytesIO()
    wb_test.save(buf)
    buf.seek(0)

    res_import1 = client.post(
        "/api/students/import",
        cookies=cookies,
        files={"file": ("import_test_template.xlsx", buf.getvalue(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
    )
    assert res_import1.status_code == 200, f"Import 1 failed: {res_import1.text}"
    data1 = res_import1.json()
    print("Import 1 Response:", data1)
    assert data1["imported_count"] == 2 or (data1["imported_count"] + data1["updated_count"] == 2)
    assert "total_imported" in data1
    assert "message" in data1
    print("✓ Test 1 Passed: Official template Excel import succeeded")

    # 3. Test importing APDM format Excel with 'Bil' column and banner header
    wb_apdm = openpyxl.Workbook()
    ws_apdm = wb_apdm.active
    ws_apdm.append(["KEMENTERIAN PENDIDIKAN MALAYSIA"])
    ws_apdm.append(["SEKOLAH KEBANGSAAN SUNGAI DENDANG"])
    ws_apdm.append(["SENARAI NAMA MURID KELAS 5 CEMERLANG TAHUN 2026"])
    ws_apdm.append(["Bil", "Nama Murid", "No. Kad Pengenalan / MyKid", "Jantina", "Tingkatan / Kelas", "Tarikh Lahir", "Nama Penjaga", "No. Tel Bimbit Penjaga"])
    ws_apdm.append([1, "MUHAMMAD IMRAN HAKIMI", "150707-08-7711", "L", "5 Cemerlang", "07/07/2015", "Hakimi bin Ahmad", "017-8899001"])
    ws_apdm.append([2, "NUR SYAFIQAH BINTI RAZAK", 150808087722.0, "P", "5 Cemerlang", "08/08/2015", "Razak bin Osman", "011-22334455"]) # Float IC
    buf_apdm = io.BytesIO()
    wb_apdm.save(buf_apdm)
    buf_apdm.seek(0)

    res_import2 = client.post(
        "/api/students/import",
        cookies=cookies,
        files={"file": ("apdm_export.xlsx", buf_apdm.getvalue(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
    )
    assert res_import2.status_code == 200, f"Import 2 failed: {res_import2.text}"
    data2 = res_import2.json()
    print("Import 2 (APDM) Response:", data2)
    assert data2["imported_count"] == 2 or (data2["imported_count"] + data2["updated_count"] == 2)
    print("✓ Test 2 Passed: APDM-style Excel import with Bil & title banners succeeded")

    # 4. Test importing CSV format
    csv_content = """Bil,Nama Pelajar,No KP,Tahun,Kelas,Jantina,Rumah Sukan
1,FARIS ISKANDAR BIN ISMAIL,160303089933,4,4 Cemerlang,Lelaki,Hijau
2,NURUL HUDA BINTI DAUD,160404089944,4,4 Cemerlang,Perempuan,Kuning
"""
    res_import3 = client.post(
        "/api/students/import",
        cookies=cookies,
        files={"file": ("senarai_murid.csv", csv_content.encode("utf-8"), "text/csv")}
    )
    assert res_import3.status_code == 200, f"Import 3 failed: {res_import3.text}"
    data3 = res_import3.json()
    print("Import 3 (CSV) Response:", data3)
    assert data3["imported_count"] == 2 or (data3["imported_count"] + data3["updated_count"] == 2)
    print("✓ Test 3 Passed: CSV import succeeded")

    # 5. Test importing invalid data row
    wb_err = openpyxl.Workbook()
    ws_err = wb_err.active
    ws_err.append(["Nama Penuh", "No KP / MyKid"])
    ws_err.append(["", ""]) # completely empty
    ws_err.append(["MURID TANPA IC", ""]) # missing IC
    buf_err = io.BytesIO()
    wb_err.save(buf_err)
    buf_err.seek(0)

    res_err = client.post(
        "/api/students/import",
        cookies=cookies,
        files={"file": ("invalid_data.xlsx", buf_err.getvalue(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
    )
    assert res_err.status_code == 200
    data_err = res_err.json()
    print("Invalid Data Import Response:", data_err)
    assert data_err["imported_count"] == 0
    assert data_err["updated_count"] == 0
    assert data_err["errors_count"] >= 1
    print("✓ Test 5 Passed: Graceful error reporting for invalid rows verified")

    # 6. Verify database student count increased
    conn = get_db_connection()
    new_count = conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]
    print(f"✓ New student count in DB: {new_count} (increased from {initial_count})")
    assert new_count >= initial_count + 6, f"Expected count to increase by at least 6, got {new_count} vs {initial_count}"

    # Verify student data and org memberships
    s1 = conn.execute("SELECT * FROM students WHERE ic_number = '160101088891'").fetchone()
    assert s1 is not None, "Student 1 not found in DB"
    assert s1["full_name"] == "AHMAD DANIEL BIN FIRDAUS"
    assert s1["sport_house_id"] is not None
    assert s1["uniform_unit_id"] is not None
    assert s1["club_society_id"] is not None
    assert s1["sports_game_id"] is not None
    print("✓ Test 4 Passed: Student fields & all 4 organization memberships verified in DB")

    conn.close()
    print("\n=== ALL BULK IMPORT INTEGRATION TESTS PASSED SUCCESSFULLY! ===")

if __name__ == "__main__":
    run_tests()
