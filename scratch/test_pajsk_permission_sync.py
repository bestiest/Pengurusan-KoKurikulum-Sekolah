import sys, os
sys.path.insert(0, os.path.abspath("."))
from fastapi.testclient import TestClient
from app.main import app

with TestClient(app) as client:
    # 0. Login as admin
    login_admin = client.post('/api/auth/login', json={'username': 'admin', 'password': 'aba6038'})
    assert login_admin.status_code == 200, f"Admin login failed: {login_admin.text}"
    print("Admin logged in successfully!")

    # 1. Verify existing letter 35 (Kejohanan Bola Baling) is in external_participations
    res_events = client.get('/api/pajsk/events')
    assert res_events.status_code == 200
    events = res_events.json()
    bola_baling = next((e for e in events if 'Kejohanan Bola Baling' in e['program_name']), None)
    assert bola_baling is not None, "Kejohanan Bola Baling not found in external_participations!"
    print(f"[TEST 1 PASS] Kejohanan Bola Baling is present in PAJSK with {bola_baling['student_count']} students!")

    # 2. Test creating a new Permission Letter and verify automatic sync to PAJSK
    students_res = client.get('/api/students?limit=5')
    all_students = students_res.json()
    chosen_ids = [s['id'] for s in all_students[:3]]

    payload_letter = {
        "program_name": "Kejohanan Sepak Takraw Bawah 12 MSSD",
        "destination_venue": "Dewan Serbaguna Selama",
        "start_datetime": "2026-09-10 08:00",
        "end_datetime": "2026-09-10 16:30",
        "organizer": "MSSD Larut Matang & Selama",
        "transportation": "Kereta Guru",
        "accompanying_teachers": "Cikgu Ahmad & Cikgu Razak",
        "fee_amount": 0.0,
        "contact_phone": "019-5551103",
        "participation_level": "Daerah",
        "activity_category": "Sukan & Permainan",
        "represented_org_id": None,
        "student_ids": chosen_ids
    }

    create_let_res = client.post('/api/permission-letters', json=payload_letter)
    assert create_let_res.status_code == 200, f"Create letter failed: {create_let_res.text}"
    letter_id = create_let_res.json()['id']
    print(f"Created Permission Letter ID: {letter_id}")

    # Check that it automatically appeared in PAJSK
    res_events2 = client.get('/api/pajsk/events')
    takraw_event = next((e for e in res_events2.json() if e['program_name'] == "Kejohanan Sepak Takraw Bawah 12 MSSD"), None)
    assert takraw_event is not None, "Takraw event was NOT synced to external_participations!"
    assert takraw_event['student_count'] == 3, f"Expected 3 students, got {takraw_event['student_count']}"
    assert takraw_event['participation_level'] == "Daerah"
    print(f"[TEST 2 PASS] Takraw event automatically synced to PAJSK with {takraw_event['student_count']} students!")

    # 3. Test updating Permission Letter (change to Negeri and add 1 student)
    new_chosen_ids = [s['id'] for s in all_students[:4]]
    payload_letter_update = {
        "program_name": "Kejohanan Sepak Takraw Peringkat Negeri Perak",
        "destination_venue": "Stadium Indera Mulia Ipoh",
        "start_datetime": "2026-09-15 08:00",
        "end_datetime": "2026-09-16 18:00",
        "organizer": "Jabatan Pendidikan Negeri Perak (JPN)",
        "transportation": "Bas Sekolah",
        "accompanying_teachers": "Cikgu Ahmad & Cikgu Razak",
        "fee_amount": 10.0,
        "contact_phone": "019-5551103",
        "participation_level": "Negeri",
        "activity_category": "Sukan & Permainan",
        "represented_org_id": None,
        "student_ids": new_chosen_ids
    }
    update_let_res = client.put(f'/api/permission-letters/{letter_id}', json=payload_letter_update)
    assert update_let_res.status_code == 200

    # Verify PAJSK event is updated
    ev_detail_res = client.get(f"/api/pajsk/events/{takraw_event['id']}")
    assert ev_detail_res.status_code == 200
    ev_detail = ev_detail_res.json()
    assert ev_detail['program_name'] == "Kejohanan Sepak Takraw Peringkat Negeri Perak"
    assert ev_detail['participation_level'] == "Negeri"
    assert len(ev_detail['students']) == 4
    print(f"[TEST 3 PASS] Updated Permission Letter synced to PAJSK (Negeri, 4 students)!")

    # 4. Test updating student achievements in PAJSK (Group & Individual)
    # Group: Set all 4 students to Johan
    # Individual: Set student index 0 to Tempat Ketiga
    students_update = []
    for idx, st in enumerate(ev_detail['students']):
        ach = "Tempat Ketiga" if idx == 0 else "Johan"
        students_update.append({
            "student_id": st['student_id'],
            "role": "Peserta",
            "achievement": ach,
            "remarks": "Ujian Kemaskini"
        })

    pajsk_update_payload = {
        "program_name": ev_detail['program_name'],
        "event_date": ev_detail['event_date'],
        "venue": ev_detail['venue'],
        "organizer": ev_detail['organizer'],
        "activity_category": ev_detail['activity_category'],
        "participation_level": ev_detail['participation_level'],
        "represented_org_id": ev_detail['represented_org_id'],
        "students": students_update
    }

    put_pajsk_res = client.put(f"/api/pajsk/events/{takraw_event['id']}", json=pajsk_update_payload)
    assert put_pajsk_res.status_code == 200, f"PUT PAJSK failed: {put_pajsk_res.text}"

    # Verify scores: Negeri Johan = 17.0, Negeri Tempat Ketiga = 15.0
    ev_detail_after = client.get(f"/api/pajsk/events/{takraw_event['id']}").json()
    st0 = next(s for s in ev_detail_after['students'] if s['student_id'] == students_update[0]['student_id'])
    st1 = next(s for s in ev_detail_after['students'] if s['student_id'] == students_update[1]['student_id'])
    assert st0['achievement'] == "Tempat Ketiga" and st0['pajsk_score'] == 15.0
    assert st1['achievement'] == "Johan" and st1['pajsk_score'] == 17.0
    print(f"[TEST 4 PASS] Group & Individual achievements updated successfully (15.0m & 17.0m)!")

    # 5. Test deletion permissions on external event
    # Logout and login as Guru Penasihat (syuhada)
    client.post('/api/auth/logout')
    login_gp = client.post('/api/auth/login', json={'username': 'syuhada', 'password': 'aba6038'})
    assert login_gp.status_code == 200, f"GP login failed: {login_gp.text}"

    del_gp_res = client.delete(f"/api/pajsk/events/{takraw_event['id']}")
    print("Guru Penasihat DELETE status:", del_gp_res.status_code)
    assert del_gp_res.status_code == 403, f"Expected 403 for Guru Penasihat, got {del_gp_res.status_code}"
    print("[TEST 5A PASS] Guru Penasihat correctly BLOCKED (403) from deleting external event!")

    # Login as admin to delete
    client.post('/api/auth/logout')
    client.post('/api/auth/login', json={'username': 'admin', 'password': 'aba6038'})

    del_admin_res = client.delete(f"/api/pajsk/events/{takraw_event['id']}")
    assert del_admin_res.status_code == 200
    print("[TEST 5B PASS] Admin successfully deleted external event (200)!")

    # Cleanup permission letter
    client.delete(f'/api/permission-letters/{letter_id}')
    print("ALL INTEGRATION TESTS PASSED SUCCESSFULLY!")
