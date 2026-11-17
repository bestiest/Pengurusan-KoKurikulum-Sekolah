from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Query, UploadFile, File
from app.database import get_db_connection, log_audit
from app.auth import get_current_user, require_roles, require_deletion_roles
from app.models import ExternalParticipationCreate, ExternalParticipationStudentItem

router = APIRouter(prefix="/api/pajsk", tags=["Penyertaan Luar & PAJSK"])

def calculate_pajsk_score(level: str, achievement: str, role: str) -> float:
    """
    Standard KPM PAJSK Scoring Matrix for Co-Curricular Competitions & Events
    """
    matrix = {
        "Antarabangsa": {
            "Johan": 20.0, "Pingat Emas": 20.0,
            "Naib Johan": 20.0, "Pingat Perak": 20.0,
            "Tempat Ketiga": 19.0, "Pingat Gangsa": 19.0,
            "Saguhati": 18.0,
            "Penyertaan": 17.0
        },
        "Kebangsaan": {
            "Johan": 20.0, "Pingat Emas": 20.0,
            "Naib Johan": 19.0, "Pingat Perak": 19.0,
            "Tempat Ketiga": 18.0, "Pingat Gangsa": 18.0,
            "Saguhati": 17.0,
            "Penyertaan": 16.0
        },
        "Negeri": {
            "Johan": 17.0, "Pingat Emas": 17.0,
            "Naib Johan": 16.0, "Pingat Perak": 16.0,
            "Tempat Ketiga": 15.0, "Pingat Gangsa": 15.0,
            "Saguhati": 14.0,
            "Penyertaan": 13.0
        },
        "Daerah": {
            "Johan": 14.0, "Pingat Emas": 14.0,
            "Naib Johan": 13.0, "Pingat Perak": 13.0,
            "Tempat Ketiga": 12.0, "Pingat Gangsa": 12.0,
            "Saguhati": 11.0,
            "Penyertaan": 10.0
        },
        "Zon": {
            "Johan": 11.0, "Pingat Emas": 11.0,
            "Naib Johan": 10.0, "Pingat Perak": 10.0,
            "Tempat Ketiga": 9.0, "Pingat Gangsa": 9.0,
            "Saguhati": 8.0,
            "Penyertaan": 7.0
        }
    }

    base = matrix.get(level, {}).get(achievement, 10.0)
    # Role adjustments
    if role in ["Jawatankuasa", "Urusetia"]:
        base = max(base - 2.0, 5.0)
    elif role == "Guru Pembimbing":
        base = 0.0

    return round(base, 1)

@router.get("/events")
async def list_external_events(
    level: Optional[str] = None,
    category: Optional[str] = None,
    search: Optional[str] = None,
    class_name: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    user: Dict[str, Any] = Depends(get_current_user)
):
    conn = get_db_connection()
    query = """
    SELECT 
        ep.*,
        o.name as org_name,
        COUNT(DISTINCT eps.student_id) as student_count,
        MAX(eps.pajsk_score) as top_score,
        GROUP_CONCAT(DISTINCT s.full_name) as involved_student_names,
        GROUP_CONCAT(DISTINCT s.class_name) as involved_classes
    FROM external_participations ep
    LEFT JOIN organizations o ON ep.represented_org_id = o.id
    LEFT JOIN external_participation_students eps ON ep.id = eps.participation_id
    LEFT JOIN students s ON eps.student_id = s.id
    WHERE 1=1
    """
    params = []

    if level:
        query += " AND ep.participation_level = ?"
        params.append(level)

    if category:
        query += " AND ep.activity_category = ?"
        params.append(category)

    if class_name:
        query += " AND s.class_name = ?"
        params.append(class_name)

    if search:
        s_term = f"%{search.strip()}%"
        query += " AND (ep.program_name LIKE ? OR ep.venue LIKE ? OR ep.organizer LIKE ? OR s.full_name LIKE ? OR s.ic_number LIKE ?)"
        params.extend([s_term, s_term, s_term, s_term, s_term])

    if start_date:
        query += " AND ep.event_date >= ?"
        params.append(start_date)

    if end_date:
        query += " AND ep.event_date <= ?"
        params.append(end_date)

    query += " GROUP BY ep.id ORDER BY ep.event_date DESC, ep.id DESC"
    rows = conn.execute(query, tuple(params)).fetchall()
    conn.close()

    return [dict(r) for r in rows]

@router.get("/student-achievements")
async def list_student_pajsk_achievements(
    search: Optional[str] = None,
    class_name: Optional[str] = None,
    grade: Optional[int] = None,
    level: Optional[str] = None,
    user: Dict[str, Any] = Depends(get_current_user)
):
    conn = get_db_connection()
    query = """
    SELECT 
        s.id as student_id,
        s.full_name,
        s.ic_number,
        s.grade,
        s.class_name,
        s.gender,
        rh.name as sport_house_name,
        ub.name as uniform_unit_name,
        kp.name as club_society_name,
        sp.name as sports_game_name,
        COALESCE(p.total_events, 0) as total_events,
        COALESCE(p.total_pajsk_score, 0) as total_pajsk_score,
        p.achievements_summary,
        COALESCE(att.att_total, 0) as att_total,
        COALESCE(att.att_present, 0) as att_present
    FROM students s
    LEFT JOIN organizations rh ON s.sport_house_id = rh.id
    LEFT JOIN organizations ub ON s.uniform_unit_id = ub.id
    LEFT JOIN organizations kp ON s.club_society_id = kp.id
    LEFT JOIN organizations sp ON s.sports_game_id = sp.id
    LEFT JOIN (
        SELECT 
            eps.student_id,
            COUNT(eps.id) as total_events,
            SUM(eps.pajsk_score) as total_pajsk_score,
            GROUP_CONCAT(ep.program_name || ' (' || ep.participation_level || ' - ' || eps.achievement || ')', ' • ') as achievements_summary
        FROM external_participation_students eps
        JOIN external_participations ep ON eps.participation_id = ep.id
        WHERE 1=1
    """
    params = []

    if level:
        query += " AND ep.participation_level = ?"
        params.append(level)

    query += """
        GROUP BY eps.student_id
    ) p ON s.id = p.student_id
    LEFT JOIN (
        SELECT 
            ar.student_id,
            COUNT(ar.id) as att_total,
            SUM(CASE WHEN ar.status IN ('Hadir', 'Lewat') THEN 1 ELSE 0 END) as att_present
        FROM attendance_records ar
        GROUP BY ar.student_id
    ) att ON s.id = att.student_id
    WHERE 1=1
    """

    if class_name:
        query += " AND s.class_name = ?"
        params.append(class_name)

    if grade:
        query += " AND s.grade = ?"
        params.append(grade)

    if search:
        s_term = f"%{search.strip()}%"
        query += " AND (s.full_name LIKE ? OR s.ic_number LIKE ? OR p.achievements_summary LIKE ?)"
        params.extend([s_term, s_term, s_term])

    query += " ORDER BY total_pajsk_score DESC, total_events DESC, s.grade ASC, s.class_name ASC, s.full_name ASC"
    rows = conn.execute(query, tuple(params)).fetchall()
    conn.close()

    result = []
    for r in rows:
        d = dict(r)
        score = d.get("total_pajsk_score") or 0
        # Determine Gred PAJSK
        if score >= 80:
            d["gred"] = "A"
        elif score >= 60:
            d["gred"] = "B"
        elif score >= 40:
            d["gred"] = "C"
        elif score >= 20:
            d["gred"] = "D"
        else:
            d["gred"] = "E"

        # Calculate attendance %
        att_total = d.get("att_total") or 0
        att_present = d.get("att_present") or 0
        if att_total > 0:
            att_pct = round((att_present / att_total) * 100, 1)
            d["attendance_percentage"] = att_pct
            d["attendance_text"] = f"{att_pct}% ({att_present}/{att_total})"
        else:
            d["attendance_percentage"] = 100.0
            d["attendance_text"] = "100% (Sepenuhnya)"

        result.append(d)

    return result

@router.get("/events/{event_id}")
async def get_external_event(event_id: int, user: Dict[str, Any] = Depends(get_current_user)):
    conn = get_db_connection()
    event = conn.execute("""
    SELECT ep.*, o.name as org_name, o.category as org_category
    FROM external_participations ep
    LEFT JOIN organizations o ON ep.represented_org_id = o.id
    WHERE ep.id = ?
    """, (event_id,)).fetchone()

    if not event:
        conn.close()
        raise HTTPException(status_code=404, detail="Rekod penyertaan luar tidak dijumpai.")

    ev_dict = dict(event)

    # Involved students
    students = conn.execute("""
    SELECT 
        eps.*,
        s.full_name as student_name, s.ic_number, s.grade, s.class_name, s.gender, s.guardian_phone
    FROM external_participation_students eps
    JOIN students s ON eps.student_id = s.id
    WHERE eps.participation_id = ?
    ORDER BY s.grade ASC, s.class_name ASC, s.full_name ASC
    """, (event_id,)).fetchall()
    ev_dict["students"] = [dict(st) for st in students]

    # School settings
    school = conn.execute("SELECT * FROM school_settings WHERE id = 1").fetchone()
    ev_dict["school"] = dict(school) if school else None

    conn.close()
    return ev_dict

@router.post("/events")
async def create_external_event(
    data: ExternalParticipationCreate,
    user: Dict[str, Any] = Depends(require_roles("Admin", "GPK Kokurikulum", "Setiausaha Kokurikulum", "Penyelaras Kokurikulum", "Guru Penasihat"))
):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO external_participations (
        program_name, event_date, venue, organizer,
        activity_category, participation_level, represented_org_id,
        academic_year, notes, certificate_url, evidence_url,
        created_by, verified_by, verified_at, status
    ) VALUES (?, ?, ?, ?, ?, ?, ?, '2026/2027', ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, 'Disahkan')
    """, (
        data.program_name.strip(),
        data.event_date,
        data.venue.strip(),
        data.organizer.strip(),
        data.activity_category,
        data.participation_level,
        data.represented_org_id,
        data.notes,
        data.certificate_url,
        data.evidence_url,
        user.get("username"),
        user.get("full_name") if user.get("role") in ["GPK Kokurikulum", "Setiausaha Kokurikulum", "Admin"] else None
    ))
    event_id = cursor.lastrowid

    # Insert students with auto calculated PAJSK
    for st in data.students:
        score = calculate_pajsk_score(data.participation_level, st.achievement, st.role)
        cursor.execute("""
        INSERT INTO external_participation_students (
            participation_id, student_id, role, achievement, pajsk_score, remarks
        ) VALUES (?, ?, ?, ?, ?, ?)
        """, (event_id, st.student_id, st.role, st.achievement, score, st.remarks))

    conn.commit()
    conn.close()

    log_audit(user.get("id"), user.get("username"), user.get("role"), "CREATE", "PAJSK", f"Cipta penyertaan luar: {data.program_name} (Peringkat {data.participation_level}, {len(data.students)} murid)", target_id=event_id)
    return {"status": "success", "message": "Rekod penyertaan luar dan PAJSK berjaya disimpan.", "id": event_id}

@router.put("/events/{event_id}")
async def update_external_event(
    event_id: int,
    data: ExternalParticipationCreate,
    user: Dict[str, Any] = Depends(require_roles("Admin", "GPK Kokurikulum", "Setiausaha Kokurikulum", "Penyelaras Kokurikulum", "Guru Penasihat"))
):
    conn = get_db_connection()
    existing = conn.execute("SELECT * FROM external_participations WHERE id = ?", (event_id,)).fetchone()
    if not existing:
        conn.close()
        raise HTTPException(status_code=404, detail="Rekod tidak dijumpai.")

    old_dict = dict(existing)
    cursor = conn.cursor()

    cursor.execute("""
    UPDATE external_participations SET
        program_name = ?, event_date = ?, venue = ?, organizer = ?,
        activity_category = ?, participation_level = ?, represented_org_id = ?,
        notes = ?, certificate_url = ?, evidence_url = ?,
        verified_by = ?, verified_at = CURRENT_TIMESTAMP
    WHERE id = ?
    """, (
        data.program_name.strip(),
        data.event_date,
        data.venue.strip(),
        data.organizer.strip(),
        data.activity_category,
        data.participation_level,
        data.represented_org_id,
        data.notes,
        data.certificate_url,
        data.evidence_url,
        user.get("full_name"),
        event_id
    ))

    # Re-sync students
    cursor.execute("DELETE FROM external_participation_students WHERE participation_id = ?", (event_id,))
    for st in data.students:
        score = calculate_pajsk_score(data.participation_level, st.achievement, st.role)
        cursor.execute("""
        INSERT INTO external_participation_students (
            participation_id, student_id, role, achievement, pajsk_score, remarks
        ) VALUES (?, ?, ?, ?, ?, ?)
        """, (event_id, st.student_id, st.role, st.achievement, score, st.remarks))

    conn.commit()
    conn.close()

    log_audit(user.get("id"), user.get("username"), user.get("role"), "UPDATE", "PAJSK", f"Kemaskini & Sahkan rekod PAJSK ID {event_id}: {data.program_name}", target_id=event_id)
    return {"status": "success", "message": "Rekod PAJSK berjaya dikemas kini."}

@router.delete("/events/{event_id}")
async def delete_external_event(
    event_id: int,
    user: Dict[str, Any] = Depends(require_deletion_roles())
):
    conn = get_db_connection()
    target = conn.execute("SELECT program_name FROM external_participations WHERE id = ?", (event_id,)).fetchone()
    if not target:
        conn.close()
        raise HTTPException(status_code=404, detail="Rekod tidak dijumpai.")

    conn.execute("DELETE FROM external_participations WHERE id = ?", (event_id,))
    conn.commit()
    conn.close()

    log_audit(user.get("id"), user.get("username"), user.get("role"), "DELETE", "PAJSK", f"Padam rekod PAJSK: {dict(target)['program_name']}", target_id=event_id)
    return {"status": "success", "message": "Rekod PAJSK berjaya dipadam."}

@router.get("/student/{student_id}")
async def get_student_pajsk_details(student_id: int, user: Dict[str, Any] = Depends(get_current_user)):
    conn = get_db_connection()
    student = conn.execute("""
    SELECT 
        s.*,
        rh.name as sport_house_name,
        ub.name as uniform_unit_name,
        kp.name as club_society_name,
        sp.name as sports_game_name
    FROM students s
    LEFT JOIN organizations rh ON s.sport_house_id = rh.id
    LEFT JOIN organizations ub ON s.uniform_unit_id = ub.id
    LEFT JOIN organizations kp ON s.club_society_id = kp.id
    LEFT JOIN organizations sp ON s.sports_game_id = sp.id
    WHERE s.id = ?
    """, (student_id,)).fetchone()

    if not student:
        conn.close()
        raise HTTPException(status_code=404, detail="Murid tidak dijumpai.")

    st_dict = dict(student)

    # Co-curricular positions (Jawatan yang disandang)
    committees = conn.execute("""
    SELECT sc.position, o.id as org_id, o.name as org_name, o.category
    FROM student_committees sc
    JOIN organizations o ON sc.organization_id = o.id
    WHERE sc.student_id = ?
    """, (student_id,)).fetchall()
    
    comm_map = {}
    for c in committees:
        cd = dict(c)
        comm_map[cd["category"]] = cd["position"]

    st_dict["sport_house_position"] = comm_map.get("Rumah Sukan", "Ahli Aktif" if st_dict.get("sport_house_id") else "-")
    st_dict["uniform_unit_position"] = comm_map.get("Unit Beruniform", "Ahli Aktif" if st_dict.get("uniform_unit_id") else "-")
    st_dict["club_society_position"] = comm_map.get("Kelab & Persatuan", "Ahli Aktif" if st_dict.get("club_society_id") else "-")
    st_dict["sports_game_position"] = comm_map.get("Sukan & Permainan", "Ahli Aktif" if st_dict.get("sports_game_id") else "-")

    # Attendance Statistics (Peratus Kehadiran Aktiviti Mingguan)
    att_stats = conn.execute("""
    SELECT 
        COUNT(ar.id) as total_sessions,
        SUM(CASE WHEN ar.status = 'Hadir' THEN 1 ELSE 0 END) as total_present,
        SUM(CASE WHEN ar.status = 'Lewat' THEN 1 ELSE 0 END) as total_late,
        SUM(CASE WHEN ar.status = 'Kebenaran' THEN 1 ELSE 0 END) as total_excused,
        SUM(CASE WHEN ar.status = 'Tidak Hadir' THEN 1 ELSE 0 END) as total_absent
    FROM attendance_records ar
    WHERE ar.student_id = ?
    """, (student_id,)).fetchone()

    att_dict = dict(att_stats) if att_stats else {"total_sessions": 0, "total_present": 0}
    total_sessions = att_dict.get("total_sessions") or 0
    total_present = (att_dict.get("total_present") or 0) + (att_dict.get("total_late") or 0)
    
    if total_sessions > 0:
        att_pct = round((total_present / total_sessions) * 100, 1)
        att_text = f"{att_pct}% ({total_present}/{total_sessions} Perjumpaan)"
    else:
        att_pct = 100.0
        att_text = "100% (Sepenuhnya)"

    st_dict["attendance_percentage"] = att_pct
    st_dict["attendance_text"] = att_text
    st_dict["total_sessions"] = total_sessions
    st_dict["total_present"] = total_present

    # External Participations & Events
    events = conn.execute("""
    SELECT 
        eps.*,
        ep.program_name, ep.event_date, ep.venue, ep.organizer, ep.activity_category, ep.participation_level,
        o.name as represented_org_name
    FROM external_participation_students eps
    JOIN external_participations ep ON eps.participation_id = ep.id
    LEFT JOIN organizations o ON ep.represented_org_id = o.id
    WHERE eps.student_id = ?
    ORDER BY ep.event_date DESC
    """, (student_id,)).fetchall()

    school = conn.execute("SELECT * FROM school_settings WHERE id = 1").fetchone()
    conn.close()

    ev_list = [dict(e) for e in events]
    total_score = sum(e.get("pajsk_score", 0) for e in ev_list)

    if total_score >= 80:
        gred = "A"
    elif total_score >= 60:
        gred = "B"
    elif total_score >= 40:
        gred = "C"
    elif total_score >= 20:
        gred = "D"
    else:
        gred = "E"

    # Highest Level
    level_order = ["Antarabangsa", "Kebangsaan", "Negeri", "Daerah", "Zon"]
    highest_level = "-"
    for lvl in level_order:
        if any(e.get("participation_level") == lvl for e in ev_list):
            highest_level = lvl
            break

    return {
        "student": st_dict,
        "events": ev_list,
        "total_events": len(ev_list),
        "highest_level": highest_level,
        "gred": gred,
        "attendance_percentage": att_pct,
        "attendance_text": att_text,
        "school": dict(school) if school else None
    }

@router.get("/sports-day/overview")
async def get_sports_day_overview(user: Dict[str, Any] = Depends(get_current_user)):
    conn = get_db_connection()
    events = conn.execute("""
        SELECT se.*, COUNT(sr.id) as total_placings
        FROM school_sports_events se
        LEFT JOIN school_sports_results sr ON se.id = sr.event_id
        GROUP BY se.id
        ORDER BY se.id ASC
    """).fetchall()

    event_list = []
    for ev in events:
        ed = dict(ev)
        results = conn.execute("""
            SELECT sr.*, s.full_name, s.class_name, s.gender, o.name as sport_house_name, o.color_code as house_color
            FROM school_sports_results sr
            JOIN students s ON sr.student_id = s.id
            JOIN organizations o ON sr.sport_house_id = o.id
            WHERE sr.event_id = ?
            ORDER BY sr.position_rank ASC
        """, (ed["id"],)).fetchall()
        ed["results"] = [dict(r) for r in results]
        event_list.append(ed)

    houses = conn.execute("SELECT id, name, color_code FROM organizations WHERE category = 'Rumah Sukan'").fetchall()
    house_tally = []
    for h in houses:
        hd = dict(h)
        stats = conn.execute("""
            SELECT 
                SUM(CASE WHEN position_rank = 1 THEN 1 ELSE 0 END) as gold,
                SUM(CASE WHEN position_rank = 2 THEN 1 ELSE 0 END) as silver,
                SUM(CASE WHEN position_rank = 3 THEN 1 ELSE 0 END) as bronze,
                SUM(CASE WHEN position_rank = 4 THEN 1 ELSE 0 END) as fourth,
                COALESCE(SUM(house_points), 0) as total_points
            FROM school_sports_results
            WHERE sport_house_id = ?
        """, (hd["id"],)).fetchone()
        hd["gold"] = dict(stats).get("gold") or 0
        hd["silver"] = dict(stats).get("silver") or 0
        hd["bronze"] = dict(stats).get("bronze") or 0
        hd["fourth"] = dict(stats).get("fourth") or 0
        hd["total_points"] = dict(stats).get("total_points") or 0
        house_tally.append(hd)

    house_tally.sort(key=lambda x: (x.get("total_points", 0), x.get("gold", 0)), reverse=True)
    school = conn.execute("SELECT * FROM school_settings WHERE id = 1").fetchone()
    conn.close()

    return {
        "events": event_list,
        "house_tally": house_tally,
        "total_events": len(event_list),
        "school": dict(school) if school else None
    }

@router.get("/cross-country/overview")
async def get_cross_country_overview(user: Dict[str, Any] = Depends(get_current_user)):
    conn = get_db_connection()
    cc_records = conn.execute("""
        SELECT ccr.*, s.full_name, s.ic_number, s.class_name, s.gender, o.name as sport_house_name, o.color_code as house_color
        FROM cross_country_records ccr
        JOIN students s ON ccr.student_id = s.id
        JOIN organizations o ON ccr.sport_house_id = o.id
        ORDER BY ccr.category ASC, ccr.rank_position ASC
    """).fetchall()

    houses = conn.execute("SELECT id, name, color_code FROM organizations WHERE category = 'Rumah Sukan'").fetchall()
    house_tally = []
    for h in houses:
        hd = dict(h)
        stats = conn.execute("""
            SELECT 
                SUM(CASE WHEN rank_position = 1 THEN 1 ELSE 0 END) as gold,
                SUM(CASE WHEN rank_position = 2 THEN 1 ELSE 0 END) as silver,
                SUM(CASE WHEN rank_position = 3 THEN 1 ELSE 0 END) as bronze,
                COUNT(id) as total_finishers,
                COALESCE(SUM(house_points), 0) as total_points
            FROM cross_country_records
            WHERE sport_house_id = ?
        """, (hd["id"],)).fetchone()
        hd["gold"] = dict(stats).get("gold") or 0
        hd["silver"] = dict(stats).get("silver") or 0
        hd["bronze"] = dict(stats).get("bronze") or 0
        hd["total_finishers"] = dict(stats).get("total_finishers") or 0
        hd["total_points"] = dict(stats).get("total_points") or 0
        house_tally.append(hd)

    house_tally.sort(key=lambda x: x.get("total_points", 0), reverse=True)
    school = conn.execute("SELECT * FROM school_settings WHERE id = 1").fetchone()
    conn.close()

    # Group by categories
    records_list = [dict(r) for r in cc_records]
    grouped_categories = {}
    for r in records_list:
        cat = r["category"]
        grouped_categories.setdefault(cat, []).append(r)

    return {
        "records": records_list,
        "grouped_categories": grouped_categories,
        "house_tally": house_tally,
        "total_finishers": len(records_list),
        "school": dict(school) if school else None
    }

@router.get("/audit-logs")
async def get_audit_logs(
    limit: int = 50,
    module: Optional[str] = None,
    user: Dict[str, Any] = Depends(require_roles("Admin", "GPK Kokurikulum", "Setiausaha Kokurikulum"))
):
    conn = get_db_connection()
    query = "SELECT * FROM audit_logs WHERE 1=1"
    params = []
    if module:
        query += " AND module = ?"
        params.append(module)
    query += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)

    rows = conn.execute(query, tuple(params)).fetchall()
    conn.close()
    return [dict(r) for r in rows]
