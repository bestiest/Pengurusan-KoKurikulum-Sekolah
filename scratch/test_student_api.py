import sys, os
sys.path.insert(0, os.path.abspath("."))
from fastapi.testclient import TestClient
from app.main import app

with TestClient(app) as client:
    # 0. Login as admin
    login_resp = client.post('/api/auth/login', json={'username': 'admin', 'password': 'aba6038'})
    assert login_resp.status_code == 200, f'Login failed: {login_resp.text}'
    print('Admin logged in successfully!')

    # 1. Test classes endpoint
    resp = client.get('/api/settings/classes')
    assert resp.status_code == 200, f'Expected 200, got {resp.status_code}'
    classes = resp.json()
    class_names = [c['class_name'] for c in classes]
    print('Classes in DB:', class_names)
    assert '1 UM' in class_names
    assert '2 UKM' in class_names
    assert '3 UPM' in class_names
    assert '4 USM' in class_names
    assert '5 UTM' in class_names
    assert '6 UITM' in class_names

    # 2. Test saving student with incomplete data (no IC, no orgs, minimal fields)
    post_payload = {
        'full_name': 'Murid Ujian Tidak Lengkap',
        'grade': 2
    }
    resp2 = client.post('/api/students', json=post_payload)
    print('Create student incomplete status:', resp2.status_code, resp2.text)
    assert resp2.status_code == 200
    student_id = resp2.json()['id']

    # Fetch created student
    created = client.get(f'/api/students/{student_id}').json()
    print('Created student fetched:', created['id'], created['full_name'], created['ic_number'], created['class_name'])
    assert created['class_name'] == '2 UKM'
    assert created['ic_number'] is not None

    # 3. Test updating student with incomplete data
    update_payload = {
        'full_name': 'Murid Ujian Dikemaskini',
        'grade': 3
    }
    resp3 = client.put(f'/api/students/{student_id}', json=update_payload)
    print('Update student status:', resp3.status_code, resp3.text)
    assert resp3.status_code == 200
    updated = client.get(f'/api/students/{student_id}').json()
    print('Updated student fetched:', updated['id'], updated['full_name'], updated['class_name'])
    assert updated['class_name'] == '3 UPM'

    # 4. Test student from the screenshot (Adam Izz Irsyad)
    s_resp = client.get('/api/students')
    students = s_resp.json()
    adam = next((s for s in students if 'ADAM IZZ IRSYAD' in s.get('full_name', '').upper()), None)
    if adam:
        print('Found Adam:', adam['id'], adam['full_name'], adam['grade'], adam['class_name'])
        update_adam = {
            'full_name': adam['full_name'],
            'ic_number': adam['ic_number'],
            'gender': adam['gender'],
            'grade': 2,
            'class_name': '2 UKM'
        }
        resp4 = client.put(f"/api/students/{adam['id']}", json=update_adam)
        print('Update Adam status:', resp4.status_code, resp4.text)
        assert resp4.status_code == 200
        adam_updated = client.get(f"/api/students/{adam['id']}").json()
        assert adam_updated['class_name'] == '2 UKM'
        print('Adam successfully updated to 2 UKM!')

    # Cleanup test student
    del_resp = client.delete(f'/api/students/{student_id}')
    assert del_resp.status_code == 200
    print('ALL TESTS PASSED SUCCESSFULLY!')
