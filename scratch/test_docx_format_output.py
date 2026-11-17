import sys, os
sys.path.insert(0, os.path.abspath("."))
from fastapi.testclient import TestClient
from app.main import app

with TestClient(app) as client:
    # 0. Login as admin
    login_admin = client.post('/api/auth/login', json={'username': 'admin', 'password': 'aba6038'})
    assert login_admin.status_code == 200

    # 1. Check school settings
    school_res = client.get('/api/settings/school')
    assert school_res.status_code == 200
    school = school_res.json()
    print("School settings:", school.get('school_name'), school.get('logo_url'))
    assert 'TOH RAKNA SAKTI' in school.get('school_name', '')

    # 2. Check logo file on disk
    logo_path = 'app/static/images/school_logo.png'
    assert os.path.exists(logo_path), "school_logo.png does not exist!"
    assert os.path.getsize(logo_path) > 100000, "school_logo.png size is unexpectedly small!"
    print(f"School logo verified: {os.path.getsize(logo_path)} bytes")

    # 3. Check signature file on disk
    sig_path = 'app/static/images/principal_signature.png'
    assert os.path.exists(sig_path), "principal_signature.png does not exist!"
    print(f"Principal signature verified: {os.path.getsize(sig_path)} bytes")

    # 4. Check Letter 35 data
    let_res = client.get('/api/permission-letters/35')
    assert let_res.status_code == 200
    let = let_res.json()
    print(f"Letter 35 loaded: {let['program_name']} ({len(let['students'])} students)")
    assert len(let['students']) > 0

    # 5. Check JS content for docx format clauses
    with open('app/static/js/app.js', 'r', encoding='utf-8') as f:
        js = f.read()
    assert "KEBENARAN IBU BAPA" in js
    assert "Insuran Takaful" in js
    assert "tindakan mahkamah" in js
    assert "memberi sebarang rawatan yang perlu" in js
    assert "renderParentConsentDocxSlip" in js
    print("All docx clauses verified inside app.js!")

    print("ALL VERIFICATION TESTS PASSED SUCCESSFULLY!")
