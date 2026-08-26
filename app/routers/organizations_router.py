from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from app.database import get_db_connection, log_audit
from app.auth import get_current_user, require_roles
from app.models import OrganizationCreate, OrganizationUpdate, CommitteeMemberAssign

router = APIRouter(prefix="/api/organizations", tags=["Pengurusan Organisasi"])

class AddMembersRequest(BaseModel):
    student_ids: List[int]

@router.get("")
async def list_organizations(
    category: Optional[str] = None,
    status: Optional[str] = None,
    user: Dict[str, Any] = Depends(get_current_user)
):
    conn = get_db_connection()
    query = """
    SELECT 
        o.*,
        COUNT(DISTINCT om.student_id) as member_count
    FROM organizations o
    LEFT JOIN organization_members om ON o.id = om.organization_id AND om.status = 'Aktif'
    WHERE 1=1
    """
    params = []

    if category:
        query += " AND o.category = ?"
        params.append(category)

    if status:
        query += " AND o.status = ?"
        params.append(status)

    # If user is Guru Penasihat with assigned orgs, we can tag which are theirs
    user_role = user.get("role")
    assigned_org_ids = [int(x) for x in (user.get("assigned_org_ids") or "").split(",") if x.strip().isdigit()]

    query += " GROUP BY o.id ORDER BY o.category ASC, o.name ASC"
    rows = conn.execute(query, tuple(params)).fetchall()
    conn.close()

    results = []
    for r in rows:
        d = dict(r)
        d["is_assigned"] = d["id"] in assigned_org_ids or user_role in ["Admin", "GPK Kokurikulum", "Setiausaha Kokurikulum"]
        results.append(d)

    return results

@router.get("/{org_id}")
async def get_organization(org_id: int, user: Dict[str, Any] = Depends(get_current_user)):
    conn = get_db_connection()
    org = conn.execute("SELECT * FROM organizations WHERE id = ?", (org_id,)).fetchone()
    if not org:
        conn.close()
        raise HTTPException(status_code=404, detail="Organisasi tidak dijumpai.")

    org_dict = dict(org)

    # 1. Members
    members = conn.execute("""
    SELECT 
        s.id, s.full_name, s.ic_number, s.grade, s.class_name, s.gender, s.guardian_phone,
        om.joined_date, om.status as membership_status,
        sc.position as committee_position
    FROM organization_members om
    JOIN students s ON om.student_id = s.id
    LEFT JOIN student_committees sc ON sc.organization_id = om.organization_id AND sc.student_id = s.id
    WHERE om.organization_id = ? AND s.status = 'Aktif'
    ORDER BY s.grade ASC, s.class_name ASC, s.full_name ASC
    """, (org_id,)).fetchall()
    org_dict["members"] = [dict(m) for m in members]
    org_dict["member_count"] = len(members)

    # 2. Committee (AJK)
    committees = conn.execute("""
    SELECT 
        sc.*,
        s.full_name as student_name, s.ic_number, s.grade, s.class_name, s.gender
    FROM student_committees sc
    JOIN students s ON sc.student_id = s.id
    WHERE sc.organization_id = ?
    ORDER BY 
        CASE sc.position
            WHEN 'Pengerusi' THEN 1
            WHEN 'Ketua Rumah / Ketua Pasukan' THEN 1
            WHEN 'Naib Pengerusi' THEN 2
            WHEN 'Penolong Ketua' THEN 2
            WHEN 'Setiausaha' THEN 3
            WHEN 'Penolong Setiausaha' THEN 4
            WHEN 'Bendahari' THEN 5
            WHEN 'Penolong Bendahari' THEN 6
            ELSE 7
        END ASC, s.grade DESC
    """, (org_id,)).fetchall()
    org_dict["committees"] = [dict(c) for c in committees]

    # 3. Attendance Summary
    sessions = conn.execute("""
    SELECT id, session_date, start_time, end_time, venue, activity_title, advisor_teacher, total_enrolled, total_present, total_absent, notes
    FROM attendance_sessions
    WHERE organization_id = ?
    ORDER BY session_date DESC
    """, (org_id,)).fetchall()
    org_dict["sessions"] = [dict(s) for s in sessions]

    # 4. Weekly Reports
    activities = conn.execute("""
    SELECT id, activity_date, start_time, end_time, venue, title, status, attendees_count, teachers_involved, review_remarks, submitted_by
    FROM weekly_activities
    WHERE organization_id = ?
    ORDER BY activity_date DESC
    """, (org_id,)).fetchall()
    org_dict["activities"] = [dict(a) for a in activities]

    # 5. External Achievements
    achievements = conn.execute("""
    SELECT 
        ep.id, ep.program_name, ep.event_date, ep.venue, ep.organizer, ep.participation_level, ep.activity_category,
        eps.role, eps.achievement, eps.pajsk_score,
        s.full_name as student_name, s.class_name
    FROM external_participations ep
    JOIN external_participation_students eps ON ep.id = eps.participation_id
    JOIN students s ON eps.student_id = s.id
    WHERE ep.represented_org_id = ?
    ORDER BY ep.event_date DESC
    """, (org_id,)).fetchall()
    org_dict["achievements"] = [dict(ac) for ac in achievements]

    conn.close()
    return org_dict

@router.post("")
async def create_organization(
    data: OrganizationCreate,
    user: Dict[str, Any] = Depends(require_roles("Admin", "GPK Kokurikulum", "Setiausaha Kokurikulum"))
):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO organizations (
        name, category, code, advisor_teachers, coordinator_name,
        logo_icon, color_code, vision_mission, meeting_day, meeting_time, meeting_venue,
        academic_year, status
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data.name.strip(),
        data.category,
        data.code,
        data.advisor_teachers,
        data.coordinator_name,
        data.logo_icon or "award",
        data.color_code or "#1e40af",
        data.vision_mission,
        data.meeting_day,
        data.meeting_time,
        data.meeting_venue,
        data.academic_year or "2026/2027",
        data.status or "Aktif"
    ))
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()

    log_audit(user.get("id"), user.get("username"), user.get("role"), "CREATE", "ORGANIZATIONS", f"Cipta organisasi: {data.name} ({data.category})", target_id=new_id)
    return {"status": "success", "message": "Organisasi berjaya dicipta.", "id": new_id}

@router.put("/{org_id}")
async def update_organization(
    org_id: int,
    data: OrganizationUpdate,
    user: Dict[str, Any] = Depends(require_roles("Admin", "GPK Kokurikulum", "Setiausaha Kokurikulum", "Penyelaras Kokurikulum", "Guru Penasihat"))
):
    conn = get_db_connection()
    existing = conn.execute("SELECT * FROM organizations WHERE id = ?", (org_id,)).fetchone()
    if not existing:
        conn.close()
        raise HTTPException(status_code=404, detail="Organisasi tidak dijumpai.")

    update_fields = []
    values = []

    fields_map = {
        "name": data.name.strip() if data.name else None,
        "category": data.category,
        "code": data.code,
        "advisor_teachers": data.advisor_teachers,
        "coordinator_name": data.coordinator_name,
        "logo_icon": data.logo_icon,
        "color_code": data.color_code,
        "vision_mission": data.vision_mission,
        "meeting_day": data.meeting_day,
        "meeting_time": data.meeting_time,
        "meeting_venue": data.meeting_venue,
        "status": data.status
    }

    for col, val in fields_map.items():
        if val is not None:
            update_fields.append(f"{col} = ?")
            values.append(val)

    if update_fields:
        values.append(org_id)
        conn.execute(f"UPDATE organizations SET {', '.join(update_fields)} WHERE id = ?", tuple(values))
        conn.commit()

    conn.close()
    log_audit(user.get("id"), user.get("username"), user.get("role"), "UPDATE", "ORGANIZATIONS", f"Kemas kini organisasi ID: {org_id}", target_id=org_id)
    return {"status": "success", "message": "Organisasi berjaya dikemas kini."}

@router.delete("/{org_id}")
async def delete_organization(
    org_id: int,
    user: Dict[str, Any] = Depends(require_roles("Admin", "GPK Kokurikulum"))
):
    conn = get_db_connection()
    target = conn.execute("SELECT name FROM organizations WHERE id = ?", (org_id,)).fetchone()
    if not target:
        conn.close()
        raise HTTPException(status_code=404, detail="Organisasi tidak dijumpai.")

    conn.execute("DELETE FROM organizations WHERE id = ?", (org_id,))
    conn.commit()
    conn.close()

    log_audit(user.get("id"), user.get("username"), user.get("role"), "DELETE", "ORGANIZATIONS", f"Padam organisasi: {dict(target)['name']}", target_id=org_id)
    return {"status": "success", "message": "Organisasi berjaya dipadam."}

@router.get("/{org_id}/members")
async def get_org_members(org_id: int, user: Dict[str, Any] = Depends(get_current_user)):
    conn = get_db_connection()
    members = conn.execute("""
    SELECT 
        s.id, s.full_name, s.ic_number, s.grade, s.class_name, s.gender, s.guardian_phone,
        om.joined_date, om.status,
        sc.position as committee_position
    FROM organization_members om
    JOIN students s ON om.student_id = s.id
    LEFT JOIN student_committees sc ON sc.organization_id = om.organization_id AND sc.student_id = s.id
    WHERE om.organization_id = ?
    ORDER BY s.grade ASC, s.class_name ASC, s.full_name ASC
    """, (org_id,)).fetchall()
    conn.close()
    return [dict(m) for m in members]

@router.post("/{org_id}/members")
async def add_org_members(
    org_id: int,
    data: AddMembersRequest,
    user: Dict[str, Any] = Depends(require_roles("Admin", "GPK Kokurikulum", "Setiausaha Kokurikulum", "Penyelaras Kokurikulum", "Guru Penasihat"))
):
    conn = get_db_connection()
    org = conn.execute("SELECT name, category FROM organizations WHERE id = ?", (org_id,)).fetchone()
    if not org:
        conn.close()
        raise HTTPException(status_code=404, detail="Organisasi tidak dijumpai.")

    category_col_map = {
        "Rumah Sukan": "sport_house_id",
        "Unit Beruniform": "uniform_unit_id",
        "Kelab & Persatuan": "club_society_id",
        "Kelab dan Persatuan": "club_society_id",
        "Sukan & Permainan": "sports_game_id",
        "Sukan dan Permainan": "sports_game_id"
    }
    col_name = category_col_map.get(org["category"])

    cursor = conn.cursor()
    added_count = 0
    for s_id in data.student_ids:
        cursor.execute("INSERT OR IGNORE INTO organization_members (organization_id, student_id, academic_year) VALUES (?, ?, '2026/2027')", (org_id, s_id))
        if col_name:
            cursor.execute(f"UPDATE students SET {col_name} = ? WHERE id = ?", (org_id, s_id))
        added_count += 1

    conn.commit()
    conn.close()

    log_audit(user.get("id"), user.get("username"), user.get("role"), "ADD_MEMBERS", "ORGANIZATIONS", f"Tambah {added_count} ahli ke {org['name']}", target_id=org_id)
    return {"status": "success", "message": f"{added_count} ahli berjaya didaftarkan ke dalam {org['name']}."}

@router.delete("/{org_id}/members/{student_id}")
async def remove_org_member(
    org_id: int,
    student_id: int,
    user: Dict[str, Any] = Depends(require_roles("Admin", "GPK Kokurikulum", "Setiausaha Kokurikulum", "Penyelaras Kokurikulum", "Guru Penasihat"))
):
    conn = get_db_connection()
    org = conn.execute("SELECT name, category FROM organizations WHERE id = ?", (org_id,)).fetchone()
    if not org:
        conn.close()
        raise HTTPException(status_code=404, detail="Organisasi tidak dijumpai.")

    category_col_map = {
        "Rumah Sukan": "sport_house_id",
        "Unit Beruniform": "uniform_unit_id",
        "Kelab & Persatuan": "club_society_id",
        "Kelab dan Persatuan": "club_society_id",
        "Sukan & Permainan": "sports_game_id",
        "Sukan dan Permainan": "sports_game_id"
    }
    col_name = category_col_map.get(org["category"])

    conn.execute("DELETE FROM organization_members WHERE organization_id = ? AND student_id = ?", (org_id, student_id))
    conn.execute("DELETE FROM student_committees WHERE organization_id = ? AND student_id = ?", (org_id, student_id))
    if col_name:
        conn.execute(f"UPDATE students SET {col_name} = NULL WHERE id = ? AND {col_name} = ?", (student_id, org_id))

    conn.commit()
    conn.close()

    log_audit(user.get("id"), user.get("username"), user.get("role"), "REMOVE_MEMBER", "ORGANIZATIONS", f"Keluarkan murid ID {student_id} daripada {org['name']}", target_id=org_id)
    return {"status": "success", "message": "Ahli berjaya dikeluarkan daripada organisasi."}

@router.post("/{org_id}/committee")
async def assign_committee_member(
    org_id: int,
    data: CommitteeMemberAssign,
    user: Dict[str, Any] = Depends(require_roles("Admin", "GPK Kokurikulum", "Setiausaha Kokurikulum", "Penyelaras Kokurikulum", "Guru Penasihat"))
):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if student already has a position in this org
    existing = conn.execute("SELECT id FROM student_committees WHERE organization_id = ? AND student_id = ?", (org_id, data.student_id)).fetchone()
    if existing:
        cursor.execute("UPDATE student_committees SET position = ?, notes = ? WHERE id = ?", (data.position, data.notes, existing["id"]))
    else:
        cursor.execute("""
        INSERT INTO student_committees (organization_id, student_id, position, academic_year, notes)
        VALUES (?, ?, ?, '2026/2027', ?)
        """, (org_id, data.student_id, data.position, data.notes))

    conn.commit()
    conn.close()

    log_audit(user.get("id"), user.get("username"), user.get("role"), "ASSIGN_AJK", "ORGANIZATIONS", f"Lantik jawatan {data.position} untuk murid ID {data.student_id} dalam org ID {org_id}", target_id=org_id)
    return {"status": "success", "message": f"Jawatan {data.position} berjaya disimpan."}

@router.delete("/{org_id}/committee/{student_id}")
async def remove_committee_member(
    org_id: int,
    student_id: int,
    user: Dict[str, Any] = Depends(require_roles("Admin", "GPK Kokurikulum", "Setiausaha Kokurikulum", "Penyelaras Kokurikulum", "Guru Penasihat"))
):
    conn = get_db_connection()
    conn.execute("DELETE FROM student_committees WHERE organization_id = ? AND student_id = ?", (org_id, student_id))
    conn.commit()
    conn.close()

    log_audit(user.get("id"), user.get("username"), user.get("role"), "REMOVE_AJK", "ORGANIZATIONS", f"Gugur jawatan AJK murid ID {student_id} dalam org ID {org_id}", target_id=org_id)
    return {"status": "success", "message": "Jawatan jawatankuasa murid berjaya digugurkan."}

@router.get("/{org_id}/org-chart")
async def get_org_chart(org_id: int, user: Dict[str, Any] = Depends(get_current_user)):
    conn = get_db_connection()
    org = conn.execute("SELECT * FROM organizations WHERE id = ?", (org_id,)).fetchone()
    if not org:
        conn.close()
        raise HTTPException(status_code=404, detail="Organisasi tidak dijumpai.")

    school = conn.execute("SELECT * FROM school_settings WHERE id = 1").fetchone()
    committees = conn.execute("""
    SELECT sc.position, sc.notes, s.id as student_id, s.full_name as student_name, s.class_name, s.gender
    FROM student_committees sc
    JOIN students s ON sc.student_id = s.id
    WHERE sc.organization_id = ?
    ORDER BY 
        CASE sc.position
            WHEN 'Pengerusi' THEN 1
            WHEN 'Ketua Rumah / Ketua Pasukan' THEN 1
            WHEN 'Naib Pengerusi' THEN 2
            WHEN 'Penolong Ketua' THEN 2
            WHEN 'Setiausaha' THEN 3
            WHEN 'Penolong Setiausaha' THEN 4
            WHEN 'Bendahari' THEN 5
            WHEN 'Penolong Bendahari' THEN 6
            ELSE 7
        END ASC
    """, (org_id,)).fetchall()
    conn.close()

    return {
        "school": dict(school) if school else None,
        "organization": dict(org),
        "committees": [dict(c) for c in committees]
    }
