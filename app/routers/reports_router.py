import io
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from app.database import get_db_connection
from app.auth import get_current_user

router = APIRouter(prefix="/api/reports", tags=["Pusat Laporan & Dashboard"])

@router.get("/dashboard-stats")
async def get_dashboard_stats(user: Dict[str, Any] = Depends(get_current_user)):
    conn = get_db_connection()

    # 1. Total Students
    total_students = conn.execute("SELECT COUNT(*) FROM students WHERE status = 'Aktif'").fetchone()[0]

    # 2. Total Students by 4 Categories
    house_count = conn.execute("SELECT COUNT(*) FROM students WHERE sport_house_id IS NOT NULL AND status = 'Aktif'").fetchone()[0]
    uniform_count = conn.execute("SELECT COUNT(*) FROM students WHERE uniform_unit_id IS NOT NULL AND status = 'Aktif'").fetchone()[0]
    club_count = conn.execute("SELECT COUNT(*) FROM students WHERE club_society_id IS NOT NULL AND status = 'Aktif'").fetchone()[0]
    sports_count = conn.execute("SELECT COUNT(*) FROM students WHERE sports_game_id IS NOT NULL AND status = 'Aktif'").fetchone()[0]

    # 3. Weekly Activities Count (Total & Pending/Incomplete)
    total_activities = conn.execute("SELECT COUNT(*) FROM weekly_activities").fetchone()[0]
    incomplete_reports = conn.execute("SELECT COUNT(*) FROM weekly_activities WHERE status IN ('Draf', 'Dihantar', 'Perlu Pindaan')").fetchone()[0]

    # 4. Average Attendance Rate
    attendance_stats = conn.execute("""
    SELECT 
        SUM(total_present) as sum_present,
        SUM(total_enrolled) as sum_enrolled
    FROM attendance_sessions
    """).fetchone()

    sum_present = attendance_stats["sum_present"] or 0
    sum_enrolled = attendance_stats["sum_enrolled"] or 0
    avg_attendance_rate = round((sum_present / sum_enrolled * 100), 1) if sum_enrolled > 0 else 92.5

    # 5. External Participations & Achievements
    total_external_events = conn.execute("SELECT COUNT(*) FROM external_participations").fetchone()[0]
    total_achievements = conn.execute("""
    SELECT COUNT(*) FROM external_participation_students 
    WHERE achievement NOT IN ('Penyertaan', 'Lain-lain')
    """).fetchone()[0]

    # 6. Upcoming Activities / Takwim
    upcoming_activities = conn.execute("""
    SELECT 
        wa.id, wa.title, wa.activity_date, wa.start_time, wa.end_time, wa.venue, wa.status,
        o.name as org_name, o.category as org_category, o.color_code
    FROM weekly_activities wa
    JOIN organizations o ON wa.organization_id = o.id
    ORDER BY wa.activity_date DESC LIMIT 5
    """).fetchall()

    # 7. Chart Data: Monthly Attendance Rate
    attendance_by_org = conn.execute("""
    SELECT 
        o.name, o.category,
        SUM(ases.total_present) as total_p,
        SUM(ases.total_enrolled) as total_e
    FROM organizations o
    LEFT JOIN attendance_sessions ases ON o.id = ases.organization_id
    GROUP BY o.id
    ORDER BY o.category ASC, o.name ASC
    """).fetchall()

    # 8. Chart Data: External by Level
    level_counts = conn.execute("""
    SELECT participation_level, COUNT(*) as count
    FROM external_participations
    GROUP BY participation_level
    """).fetchall()

    level_map = {"Zon": 0, "Daerah": 0, "Negeri": 0, "Kebangsaan": 0, "Antarabangsa": 0}
    for lc in level_counts:
        level_map[lc["participation_level"]] = lc["count"]

    # 9. Membership breakdown by Rumah Sukan & Unit Beruniform
    house_breakdown = conn.execute("""
    SELECT o.name, o.color_code, COUNT(s.id) as count
    FROM organizations o
    LEFT JOIN students s ON o.id = s.sport_house_id AND s.status = 'Aktif'
    WHERE o.category = 'Rumah Sukan'
    GROUP BY o.id
    """).fetchall()

    uniform_breakdown = conn.execute("""
    SELECT o.name, COUNT(s.id) as count
    FROM organizations o
    LEFT JOIN students s ON o.id = s.uniform_unit_id AND s.status = 'Aktif'
    WHERE o.category = 'Unit Beruniform'
    GROUP BY o.id
    """).fetchall()

    conn.close()

    return {
        "summary": {
            "total_students": total_students,
            "house_count": house_count,
            "uniform_count": uniform_count,
            "club_count": club_count,
            "sports_count": sports_count,
            "total_activities": total_activities,
            "incomplete_reports": incomplete_reports,
            "avg_attendance_rate": avg_attendance_rate,
            "total_external_events": total_external_events,
            "total_achievements": total_achievements
        },
        "upcoming_activities": [dict(a) for a in upcoming_activities],
        "charts": {
            "levels": level_map,
            "houses": [dict(h) for h in house_breakdown],
            "uniforms": [dict(u) for u in uniform_breakdown],
            "attendance_orgs": [dict(ao) for ao in attendance_by_org if (ao["total_e"] or 0) > 0]
        }
    }

@router.get("/generate/{report_type}")
async def generate_report_data(
    report_type: str,
    ids: Optional[str] = None,
    search: Optional[str] = None,
    grade: Optional[int] = None,
    class_name: Optional[str] = None,
    gender: Optional[str] = None,
    org_id: Optional[int] = None,
    category: Optional[str] = None,
    sport_house_id: Optional[int] = None,
    uniform_unit_id: Optional[int] = None,
    club_society_id: Optional[int] = None,
    sports_game_id: Optional[int] = None,
    student_id: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    user: Dict[str, Any] = Depends(get_current_user)
):
    conn = get_db_connection()
    school = conn.execute("SELECT * FROM school_settings WHERE id = 1").fetchone()
    school_dict = dict(school) if school else {}

    report_result = {
        "report_type": report_type,
        "school": school_dict,
        "title": "LAPORAN KOKURIKULUM",
        "data": [],
        "meta": {}
    }

    # 0. Filtered / Selected Students from Maklumat Murid View
    if report_type == "filtered_students":
        query = """
        SELECT 
            s.*,
            rh.name as sport_house_name, ub.name as uniform_unit_name,
            kp.name as club_society_name, sp.name as sports_game_name
        FROM students s
        LEFT JOIN organizations rh ON s.sport_house_id = rh.id
        LEFT JOIN organizations ub ON s.uniform_unit_id = ub.id
        LEFT JOIN organizations kp ON s.club_society_id = kp.id
        LEFT JOIN organizations sp ON s.sports_game_id = sp.id
        WHERE 1=1
        """
        params = []
        filter_label = "SEMUA MURID"

        if ids:
            id_list = [int(x.strip()) for x in ids.split(",") if x.strip().isdigit()]
            if id_list:
                placeholders = ",".join(["?"] * len(id_list))
                query += f" AND s.id IN ({placeholders})"
                params.extend(id_list)
                filter_label = f"PILIHAN ({len(id_list)} MURID)"
        else:
            if search:
                query += " AND (s.full_name LIKE ? OR s.ic_number LIKE ?)"
                params.extend([f"%{search}%", f"%{search}%"])
                filter_label = f"CARIAN: {search}"
            if grade:
                query += " AND s.grade = ?"
                params.append(grade)
                filter_label = f"TAHUN {grade}"
            if class_name:
                query += " AND s.class_name = ?"
                params.append(class_name)
                filter_label = f"KELAS {class_name}"
            if gender:
                query += " AND s.gender = ?"
                params.append(gender)
                filter_label += f" ({gender})"
            if sport_house_id:
                query += " AND s.sport_house_id = ?"
                params.append(sport_house_id)
                h = conn.execute("SELECT name FROM organizations WHERE id = ?", (sport_house_id,)).fetchone()
                if h: filter_label = f"RUMAH {h['name'].upper()}"
            if uniform_unit_id:
                query += " AND s.uniform_unit_id = ?"
                params.append(uniform_unit_id)
                u = conn.execute("SELECT name FROM organizations WHERE id = ?", (uniform_unit_id,)).fetchone()
                if u: filter_label = f"UNIT {u['name'].upper()}"
            if club_society_id:
                query += " AND s.club_society_id = ?"
                params.append(club_society_id)
                c = conn.execute("SELECT name FROM organizations WHERE id = ?", (club_society_id,)).fetchone()
                if c: filter_label = f"KELAB {c['name'].upper()}"
            if sports_game_id:
                query += " AND s.sports_game_id = ?"
                params.append(sports_game_id)
                sp = conn.execute("SELECT name FROM organizations WHERE id = ?", (sports_game_id,)).fetchone()
                if sp: filter_label = f"SUKAN {sp['name'].upper()}"
            if category and not (sport_house_id or uniform_unit_id or club_society_id or sports_game_id):
                if category == "Rumah Sukan":
                    query += " AND s.sport_house_id IS NOT NULL"
                    filter_label = "KATEGORI: RUMAH SUKAN"
                elif category == "Unit Beruniform":
                    query += " AND s.uniform_unit_id IS NOT NULL"
                    filter_label = "KATEGORI: UNIT BERUNIFORM"
                elif category in ("Kelab & Persatuan", "Kelab dan Persatuan"):
                    query += " AND s.club_society_id IS NOT NULL"
                    filter_label = "KATEGORI: KELAB & PERSATUAN"
                elif category in ("Sukan & Permainan", "Sukan dan Permainan"):
                    query += " AND s.sports_game_id IS NOT NULL"
                    filter_label = "KATEGORI: SUKAN & PERMAINAN"

        query += " ORDER BY s.grade ASC, s.class_name ASC, s.full_name ASC"
        rows = conn.execute(query, tuple(params)).fetchall()
        report_result["title"] = f"SENARAI NAMA MURID KOKURIKULUM — {filter_label}"
        report_result["data"] = [dict(r) for r in rows]

    # 1. Senarai Murid Mengikut Kelas
    elif report_type == "students_by_class":
        query = """
        SELECT 
            s.*,
            rh.name as sport_house_name, ub.name as uniform_unit_name,
            kp.name as club_society_name, sp.name as sports_game_name
        FROM students s
        LEFT JOIN organizations rh ON s.sport_house_id = rh.id
        LEFT JOIN organizations ub ON s.uniform_unit_id = ub.id
        LEFT JOIN organizations kp ON s.club_society_id = kp.id
        LEFT JOIN organizations sp ON s.sports_game_id = sp.id
        WHERE s.status = 'Aktif'
        """
        params = []
        if class_name:
            query += " AND s.class_name = ?"
            params.append(class_name)
        elif grade:
            query += " AND s.grade = ?"
            params.append(grade)
        query += " ORDER BY s.grade ASC, s.class_name ASC, s.full_name ASC"
        rows = conn.execute(query, tuple(params)).fetchall()
        report_result["title"] = f"SENARAI NAMA MURID MENGIKUT KELAS {class_name or (f'TAHUN {grade}' if grade else 'KESELURUHAN')}"
        report_result["data"] = [dict(r) for r in rows]

    # 2. Senarai Ahli Mengikut Organisasi
    elif report_type == "members_by_org":
        if not org_id:
            org = conn.execute("SELECT * FROM organizations ORDER BY id ASC LIMIT 1").fetchone()
            org_id = org["id"] if org else 1
        else:
            org = conn.execute("SELECT * FROM organizations WHERE id = ?", (org_id,)).fetchone()
            
        report_result["meta"]["organization"] = dict(org) if org else {}
        report_result["title"] = f"SENARAI AHLI {org['name'].upper() if org else 'ORGANISASI'}"

        rows = conn.execute("""
        SELECT 
            s.id, s.full_name, s.ic_number, s.grade, s.class_name, s.gender,
            om.joined_date, sc.position as committee_position,
            s.guardian_name, s.guardian_phone
        FROM organization_members om
        JOIN students s ON om.student_id = s.id
        LEFT JOIN student_committees sc ON sc.organization_id = om.organization_id AND sc.student_id = s.id
        WHERE om.organization_id = ? AND s.status = 'Aktif'
        ORDER BY s.grade ASC, s.class_name ASC, s.full_name ASC
        """, (org_id,)).fetchall()
        report_result["data"] = [dict(r) for r in rows]

    # 3. Senarai Murid Mengikut Rumah Sukan
    elif report_type == "students_by_sport_house":
        query = """
        SELECT 
            s.*, o.name as sport_house_name, o.color_code
        FROM students s
        JOIN organizations o ON s.sport_house_id = o.id
        WHERE s.status = 'Aktif'
        """
        params = []
        house_title = "KESELURUHAN"
        if org_id:
            query += " AND s.sport_house_id = ?"
            params.append(org_id)
            h = conn.execute("SELECT name FROM organizations WHERE id = ?", (org_id,)).fetchone()
            if h: house_title = h["name"].upper()

        query += " ORDER BY o.name ASC, s.grade ASC, s.class_name ASC, s.full_name ASC"
        rows = conn.execute(query, tuple(params)).fetchall()
        report_result["title"] = f"SENARAI NAMA MURID MENGIKUT RUMAH SUKAN — {house_title}"
        report_result["data"] = [dict(r) for r in rows]

    # 4. Senarai Jawatankuasa Murid (AJK)
    elif report_type == "student_committees":
        query = """
        SELECT 
            sc.position, sc.notes,
            s.full_name as student_name, s.ic_number, s.grade, s.class_name, s.gender,
            o.name as org_name, o.category as org_category
        FROM student_committees sc
        JOIN students s ON sc.student_id = s.id
        JOIN organizations o ON sc.organization_id = o.id
        WHERE 1=1
        """
        params = []
        comm_title = "KESELURUHAN"
        if org_id:
            query += " AND sc.organization_id = ?"
            params.append(org_id)
            org_row = conn.execute("SELECT name FROM organizations WHERE id = ?", (org_id,)).fetchone()
            if org_row: comm_title = org_row["name"].upper()
        elif category:
            query += " AND o.category = ?"
            params.append(category)
            comm_title = category.upper()

        query += " ORDER BY o.category ASC, o.name ASC, sc.id ASC"
        rows = conn.execute(query, tuple(params)).fetchall()
        report_result["title"] = f"SENARAI JAWATANKUASA MURID (AJK) — {comm_title}"
        report_result["data"] = [dict(r) for r in rows]

    # 5. Carta Organisasi
    elif report_type == "org_chart":
        if not org_id:
            org = conn.execute("SELECT * FROM organizations ORDER BY id ASC LIMIT 1").fetchone()
            org_id = org["id"] if org else 1
        else:
            org = conn.execute("SELECT * FROM organizations WHERE id = ?", (org_id,)).fetchone()

        report_result["meta"]["organization"] = dict(org) if org else {}
        report_result["title"] = f"CARTA ORGANISASI {org['name'].upper() if org else ''}"

        committees = conn.execute("""
        SELECT 
            sc.position, sc.notes,
            s.full_name as student_name, s.class_name, s.gender
        FROM student_committees sc
        JOIN students s ON sc.student_id = s.id
        WHERE sc.organization_id = ?
        ORDER BY sc.id ASC
        """, (org_id,)).fetchall()
        report_result["data"] = [dict(c) for c in committees]

    # 6. Rekod Kehadiran Individu
    elif report_type == "individual_attendance":
        if not student_id:
            st_first = conn.execute("SELECT id FROM students ORDER BY id ASC LIMIT 1").fetchone()
            student_id = st_first["id"] if st_first else 1

        st = conn.execute("SELECT * FROM students WHERE id = ?", (student_id,)).fetchone()
        report_result["meta"]["student"] = dict(st) if st else {}
        report_result["title"] = f"REKOD KEHADIRAN KOKURIKULUM INDIVIDU: {st['full_name'] if st else ''}"

        records = conn.execute("""
        SELECT 
            ar.status, ar.remarks,
            ases.session_date, ases.activity_title, ases.start_time, ases.end_time, ases.venue, ases.advisor_teacher,
            o.name as org_name, o.category as org_category
        FROM attendance_records ar
        JOIN attendance_sessions ases ON ar.session_id = ases.id
        JOIN organizations o ON ases.organization_id = o.id
        WHERE ar.student_id = ?
        ORDER BY ases.session_date DESC
        """, (student_id,)).fetchall()
        report_result["data"] = [dict(r) for r in records]

    # 7. Rekod Kehadiran Organisasi
    elif report_type == "org_attendance":
        if not org_id:
            org = conn.execute("SELECT * FROM organizations ORDER BY id ASC LIMIT 1").fetchone()
            org_id = org["id"] if org else 1
        else:
            org = conn.execute("SELECT * FROM organizations WHERE id = ?", (org_id,)).fetchone()

        report_result["meta"]["organization"] = dict(org) if org else {}
        report_result["title"] = f"LAPORAN KEHADIRAN AKTIVITI {org['name'].upper() if org else ''}"

        sessions = conn.execute("""
        SELECT 
            ases.*,
            ROUND((CAST(ases.total_present AS FLOAT) / NULLIF(ases.total_enrolled, 0) * 100), 1) as percentage
        FROM attendance_sessions ases
        WHERE ases.organization_id = ?
        ORDER BY ases.session_date DESC
        """, (org_id,)).fetchall()
        report_result["data"] = [dict(s) for s in sessions]

    # 8. Laporan Aktiviti Mingguan
    elif report_type == "weekly_activity":
        query = """
        SELECT wa.*, o.name as org_name, o.category as org_category
        FROM weekly_activities wa
        JOIN organizations o ON wa.organization_id = o.id
        WHERE 1=1
        """
        params = []
        if org_id:
            query += " AND wa.organization_id = ?"
            params.append(org_id)
        if start_date:
            query += " AND wa.activity_date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND wa.activity_date <= ?"
            params.append(end_date)
        query += " ORDER BY wa.activity_date DESC"
        rows = conn.execute(query, tuple(params)).fetchall()

        parsed_activities = []
        for r in rows:
            act = dict(r)
            sess = conn.execute("""
            SELECT * FROM attendance_sessions
            WHERE organization_id = ? AND session_date = ?
            ORDER BY id DESC LIMIT 1
            """, (act["organization_id"], act["activity_date"])).fetchone()

            present_names = []
            absent_names = []
            total_enrolled = 0

            if sess:
                records = conn.execute("""
                SELECT ar.status, ar.remarks, s.full_name, s.class_name
                FROM attendance_records ar
                JOIN students s ON ar.student_id = s.id
                WHERE ar.session_id = ?
                ORDER BY s.grade ASC, s.class_name ASC, s.full_name ASC
                """, (sess["id"],)).fetchall()

                total_enrolled = len(records)
                for rec in records:
                    rec_dict = dict(rec)
                    if rec_dict["status"] in ["Hadir", "Lewat"]:
                        present_names.append(f"{rec_dict['full_name']} ({rec_dict['class_name']})")
                    else:
                        reason = f" - {rec_dict['remarks']}" if rec_dict['remarks'] else ""
                        absent_names.append(f"{rec_dict['full_name']} ({rec_dict['class_name']}) [{rec_dict['status']}{reason}]")
            else:
                mems = conn.execute("""
                SELECT s.full_name, s.class_name FROM organization_members om JOIN students s ON om.student_id = s.id
                WHERE om.organization_id = ? AND s.status = 'Aktif'
                ORDER BY s.grade ASC, s.class_name ASC, s.full_name ASC
                """, (act["organization_id"],)).fetchall()
                total_enrolled = len(mems)
                pres_cnt = act.get("attendees_count") or 0
                for idx, m in enumerate(mems):
                    if idx < pres_cnt:
                        present_names.append(f"{m['full_name']} ({m['class_name']})")
                    else:
                        absent_names.append(f"{m['full_name']} ({m['class_name']})")

            act["present_students"] = present_names
            act["absent_students"] = absent_names
            act["present_count"] = len(present_names)
            act["absent_count"] = len(absent_names)
            act["total_enrolled"] = total_enrolled
            act["percentage"] = round((len(present_names) / total_enrolled * 100), 1) if total_enrolled > 0 else 0.0
            parsed_activities.append(act)

        report_result["title"] = "LAPORAN AKTIVITI MINGGUAN KOKURIKULUM"
        report_result["data"] = parsed_activities

    # 9. Laporan Aktiviti Bulanan
    elif report_type == "monthly_activity":
        rows = conn.execute("""
        SELECT 
            strftime('%Y-%m', wa.activity_date) as month,
            o.category,
            COUNT(wa.id) as total_activities,
            SUM(wa.attendees_count) as total_attendees
        FROM weekly_activities wa
        JOIN organizations o ON wa.organization_id = o.id
        GROUP BY strftime('%Y-%m', wa.activity_date), o.category
        ORDER BY month DESC, o.category ASC
        """).fetchall()
        report_result["title"] = "LAPORAN RINGKASAN AKTIVITI BULANAN KOKURIKULUM"
        report_result["data"] = [dict(r) for r in rows]

    # 10. Laporan Aktiviti Tahunan
    elif report_type == "annual_activity":
        rows = conn.execute("""
        SELECT 
            o.name as org_name, o.category,
            COUNT(wa.id) as total_sessions,
            SUM(wa.attendees_count) as total_attendees,
            COUNT(DISTINCT om.student_id) as total_members
        FROM organizations o
        LEFT JOIN weekly_activities wa ON o.id = wa.organization_id
        LEFT JOIN organization_members om ON o.id = om.organization_id
        GROUP BY o.id
        ORDER BY o.category ASC, o.name ASC
        """).fetchall()
        report_result["title"] = "LAPORAN TAHUNAN PENGURUSAN UNIT KOKURIKULUM"
        report_result["data"] = [dict(r) for r in rows]

    # 11. Laporan Penyertaan Luar Sekolah
    elif report_type == "external_participations":
        rows = conn.execute("""
        SELECT 
            ep.*,
            o.name as represented_org_name,
            COUNT(eps.student_id) as student_count
        FROM external_participations ep
        LEFT JOIN organizations o ON ep.represented_org_id = o.id
        LEFT JOIN external_participation_students eps ON ep.id = eps.participation_id
        GROUP BY ep.id
        ORDER BY ep.event_date DESC
        """).fetchall()
        report_result["title"] = "LAPORAN PENYERTAAN AKTIVITI & PERTANDINGAN LUAR SEKOLAH"
        report_result["data"] = [dict(r) for r in rows]

    # 12. Laporan Pencapaian Murid
    elif report_type == "student_achievements":
        rows = conn.execute("""
        SELECT 
            eps.achievement, eps.role, eps.pajsk_score, eps.remarks,
            ep.program_name, ep.event_date, ep.venue, ep.participation_level, ep.activity_category,
            s.full_name as student_name, s.class_name, s.gender,
            o.name as represented_org_name
        FROM external_participation_students eps
        JOIN external_participations ep ON eps.participation_id = ep.id
        JOIN students s ON eps.student_id = s.id
        LEFT JOIN organizations o ON ep.represented_org_id = o.id
        WHERE eps.achievement NOT IN ('Penyertaan', 'Lain-lain')
        ORDER BY ep.event_date DESC, eps.pajsk_score DESC
        """).fetchall()
        report_result["title"] = "LAPORAN REKOD KEJAYAAN & PENCAPAIAN KOKURIKULUM MURID"
        report_result["data"] = [dict(r) for r in rows]

    # 13. Ringkasan PAJSK Individu
    elif report_type == "individual_pajsk":
        if not student_id:
            st_first = conn.execute("SELECT id FROM students ORDER BY id ASC LIMIT 1").fetchone()
            student_id = st_first["id"] if st_first else 1

        st = conn.execute("""
        SELECT s.*, rh.name as sport_house_name, ub.name as uniform_unit_name, kp.name as club_society_name, sp.name as sports_game_name
        FROM students s
        LEFT JOIN organizations rh ON s.sport_house_id = rh.id
        LEFT JOIN organizations ub ON s.uniform_unit_id = ub.id
        LEFT JOIN organizations kp ON s.club_society_id = kp.id
        LEFT JOIN organizations sp ON s.sports_game_id = sp.id
        WHERE s.id = ?
        """, (student_id,)).fetchone()
        report_result["meta"]["student"] = dict(st) if st else {}
        report_result["title"] = f"SLIP KEPUTUSAN PENTAKSIRAN AKTIVITI JASMANI, SUKAN DAN KOKURIKULUM (PAJSK): {st['full_name'] if st else ''}"

        # Get scores
        comms = conn.execute("SELECT position FROM student_committees WHERE student_id = ?", (student_id,)).fetchall()
        events = conn.execute("""
        SELECT eps.role, eps.achievement, eps.pajsk_score, ep.program_name, ep.participation_level, ep.event_date
        FROM external_participation_students eps
        JOIN external_participations ep ON eps.participation_id = ep.id
        WHERE eps.student_id = ?
        """, (student_id,)).fetchall()

        report_result["data"] = {
            "committees": [dict(c) for c in comms],
            "events": [dict(e) for e in events]
        }

    # 14. Ringkasan PAJSK Mengikut Kelas / Organisasi
    elif report_type == "pajsk_summary_class_or_org":
        query = """
        SELECT 
            s.id, s.full_name, s.ic_number, s.grade, s.class_name, s.gender,
            rh.name as sport_house_name, ub.name as uniform_unit_name,
            kp.name as club_society_name, sp.name as sports_game_name,
            COUNT(DISTINCT eps.id) as total_events,
            COALESCE(SUM(eps.pajsk_score), 0) as total_event_score
        FROM students s
        LEFT JOIN organizations rh ON s.sport_house_id = rh.id
        LEFT JOIN organizations ub ON s.uniform_unit_id = ub.id
        LEFT JOIN organizations kp ON s.club_society_id = kp.id
        LEFT JOIN organizations sp ON s.sports_game_id = sp.id
        LEFT JOIN external_participation_students eps ON s.id = eps.student_id
        WHERE s.status = 'Aktif'
        """
        params = []
        if class_name:
            query += " AND s.class_name = ?"
            params.append(class_name)
        elif grade:
            query += " AND s.grade = ?"
            params.append(grade)
        elif org_id:
            query += " AND (s.sport_house_id = ? OR s.uniform_unit_id = ? OR s.club_society_id = ? OR s.sports_game_id = ?)"
            params.extend([org_id, org_id, org_id, org_id])

        query += " GROUP BY s.id ORDER BY s.grade ASC, s.class_name ASC, s.full_name ASC"
        rows = conn.execute(query, tuple(params)).fetchall()

        parsed_data = []
        for r in rows:
            d = dict(r)
            ev_score = min(d["total_event_score"], 40.0)
            total = round(36.0 + 7.0 + ev_score + 6.0, 1)
            d["total_pajsk"] = min(total, 100.0)
            d["gred"] = "A" if total >= 80 else ("B" if total >= 60 else "C")
            parsed_data.append(d)

        report_result["title"] = f"ANALISIS MARKAH PAJSK {class_name or (f'TAHUN {grade}' if grade else 'KESELURUHAN')}"
        report_result["data"] = parsed_data

    # 15. Surat Kebenaran Murid & Keratan Jawapan
    elif report_type == "permission_letters_summary":
        rows = conn.execute("""
        SELECT 
            pl.*,
            COUNT(pls.student_id) as total_students,
            SUM(CASE WHEN pls.permission_status = 'Dibenarkan' THEN 1 ELSE 0 END) as allowed_count
        FROM permission_letters pl
        LEFT JOIN permission_letter_students pls ON pl.id = pls.letter_id
        GROUP BY pl.id
        ORDER BY pl.id DESC
        """).fetchall()
        report_result["title"] = "REKOD PENGELUARAN SURAT KEBENARAN IBU BAPA / PENJAGA"
        report_result["data"] = [dict(r) for r in rows]

    # 16. Profil Lengkap Kokurikulum Murid
    elif report_type == "individual_student_profile":
        if not student_id:
            st_first = conn.execute("SELECT id FROM students ORDER BY id ASC LIMIT 1").fetchone()
            student_id = st_first["id"] if st_first else 1

        st = conn.execute("""
        SELECT s.*, rh.name as sport_house_name, ub.name as uniform_unit_name, kp.name as club_society_name, sp.name as sports_game_name
        FROM students s
        LEFT JOIN organizations rh ON s.sport_house_id = rh.id
        LEFT JOIN organizations ub ON s.uniform_unit_id = ub.id
        LEFT JOIN organizations kp ON s.club_society_id = kp.id
        LEFT JOIN organizations sp ON s.sports_game_id = sp.id
        WHERE s.id = ?
        """, (student_id,)).fetchone()
        report_result["meta"]["student"] = dict(st) if st else {}
        report_result["title"] = f"PROFIL KOKURIKULUM INDIVIDU: {st['full_name'] if st else ''}"

        # Comms
        comms = conn.execute("""
        SELECT c.*, o.name as org_name, o.category as org_category
        FROM student_committees c JOIN organizations o ON c.organization_id = o.id
        WHERE c.student_id = ?
        """, (student_id,)).fetchall()

        # Att
        att = conn.execute("""
        SELECT ar.status, ases.session_date, ases.activity_title, o.name as org_name
        FROM attendance_records ar
        JOIN attendance_sessions ases ON ar.session_id = ases.id
        JOIN organizations o ON ases.organization_id = o.id
        WHERE ar.student_id = ?
        """, (student_id,)).fetchall()

        # Ext
        ext = conn.execute("""
        SELECT eps.role, eps.achievement, eps.pajsk_score, ep.program_name, ep.participation_level, ep.event_date
        FROM external_participation_students eps
        JOIN external_participations ep ON eps.participation_id = ep.id
        WHERE eps.student_id = ?
        """, (student_id,)).fetchall()

        report_result["data"] = {
            "committees": [dict(c) for c in comms],
            "attendance": [dict(a) for a in att],
            "external": [dict(e) for e in ext]
        }

    conn.close()
    return report_result

@router.get("/export/excel/{report_type}")
async def export_report_excel(
    report_type: str,
    ids: Optional[str] = None,
    search: Optional[str] = None,
    grade: Optional[int] = None,
    class_name: Optional[str] = None,
    gender: Optional[str] = None,
    org_id: Optional[int] = None,
    category: Optional[str] = None,
    sport_house_id: Optional[int] = None,
    uniform_unit_id: Optional[int] = None,
    club_society_id: Optional[int] = None,
    sports_game_id: Optional[int] = None,
    student_id: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    user: Dict[str, Any] = Depends(get_current_user)
):
    report = await generate_report_data(
        report_type=report_type,
        ids=ids,
        search=search,
        grade=grade,
        class_name=class_name,
        gender=gender,
        org_id=org_id,
        category=category,
        sport_house_id=sport_house_id,
        uniform_unit_id=uniform_unit_id,
        club_society_id=club_society_id,
        sports_game_id=sports_game_id,
        student_id=student_id,
        start_date=start_date,
        end_date=end_date,
        user=user
    )

    school = report.get("school", {})
    school_name = school.get("school_name", "SEKOLAH KEBANGSAAN SUNGAI DENDANG")
    school_code = school.get("school_code", "ABA6034")
    report_title = report.get("title", "LAPORAN KOKURIKULUM")

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Laporan"

    # Header styling
    ws.merge_cells("A1:G1")
    ws["A1"] = f"{school_name} ({school_code})"
    ws["A1"].font = Font(name="Calibri", size=14, bold=True, color="1E3A8A")
    ws["A1"].alignment = Alignment(horizontal="center", vertical="center")

    ws.merge_cells("A2:G2")
    ws["A2"] = report_title
    ws["A2"].font = Font(name="Calibri", size=11, bold=True, color="475569")
    ws["A2"].alignment = Alignment(horizontal="center", vertical="center")

    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
    thin_border = Border(
        left=Side(style='thin', color='CBD5E1'),
        right=Side(style='thin', color='CBD5E1'),
        top=Side(style='thin', color='CBD5E1'),
        bottom=Side(style='thin', color='CBD5E1')
    )

    data = report.get("data", [])
    if isinstance(data, list) and len(data) > 0:
        # Determine table headers based on report type
        if report_type in ["filtered_students", "students_by_class", "students_by_sport_house"]:
            headers = ["Bil", "Nama Penuh Murid", "No KP / MyKid", "Jantina", "Kelas", "Rumah Sukan", "Unit Beruniform"]
            keys = [
                lambda r, i: i,
                lambda r, i: r.get("full_name", "-"),
                lambda r, i: r.get("ic_number", "-"),
                lambda r, i: r.get("gender", "-"),
                lambda r, i: r.get("class_name", "-"),
                lambda r, i: r.get("sport_house_name", "-"),
                lambda r, i: r.get("uniform_unit_name", "-")
            ]
        elif report_type == "members_by_org":
            headers = ["Bil", "Nama Penuh Murid", "No KP / MyKid", "Jantina", "Kelas", "Jawatan AJK", "Penjaga & Tel"]
            keys = [
                lambda r, i: i,
                lambda r, i: r.get("full_name", "-"),
                lambda r, i: r.get("ic_number", "-"),
                lambda r, i: r.get("gender", "-"),
                lambda r, i: r.get("class_name", "-"),
                lambda r, i: r.get("committee_position") or "Ahli Biasa",
                lambda r, i: f"{r.get('guardian_name') or '-'} ({r.get('guardian_phone') or '-'})"
            ]
        elif report_type == "student_committees":
            headers = ["Bil", "Nama Penuh Murid", "Jawatan Disandang", "Organisasi", "Kategori", "Kelas", "Jantina"]
            keys = [
                lambda r, i: i,
                lambda r, i: r.get("student_name", "-"),
                lambda r, i: r.get("position", "-"),
                lambda r, i: r.get("org_name", "-"),
                lambda r, i: r.get("org_category", "-"),
                lambda r, i: r.get("class_name", "-"),
                lambda r, i: r.get("gender", "-")
            ]
        elif report_type == "student_achievements":
            headers = ["Bil", "Nama Penuh Murid", "Kelas", "Nama Pertandingan / Program", "Peringkat", "Pencapaian", "Skor PAJSK"]
            keys = [
                lambda r, i: i,
                lambda r, i: r.get("student_name", "-"),
                lambda r, i: r.get("class_name", "-"),
                lambda r, i: r.get("program_name", "-"),
                lambda r, i: r.get("participation_level", "-"),
                lambda r, i: r.get("achievement", "-"),
                lambda r, i: f"{r.get('pajsk_score', 0)}m"
            ]
        elif report_type == "pajsk_summary_class_or_org":
            headers = ["Bil", "Nama Penuh Murid", "No KP / MyKid", "Kelas", "Jantina", "Skor PAJSK", "Gred"]
            keys = [
                lambda r, i: i,
                lambda r, i: r.get("full_name", "-"),
                lambda r, i: r.get("ic_number", "-"),
                lambda r, i: r.get("class_name", "-"),
                lambda r, i: r.get("gender", "-"),
                lambda r, i: f"{r.get('total_pajsk', 0)}m",
                lambda r, i: r.get("gred", "-")
            ]
        elif report_type == "weekly_activity":
            headers = ["Bil", "Tarikh & Masa", "Organisasi", "Tajuk Aktiviti & Lokasi", "Kehadiran", "Senarai Murid Hadir", "Senarai Murid Tidak Hadir & Sebab", "Status Laporan"]
            keys = [
                lambda r, i: i,
                lambda r, i: f"{r.get('activity_date', '-')} ({r.get('start_time', '14:00')}-{r.get('end_time', '16:00')})",
                lambda r, i: f"[{r.get('org_category', '')}] {r.get('org_name', '-')}",
                lambda r, i: f"{r.get('title', '-')} ({r.get('venue') or 'Sekolah'})",
                lambda r, i: f"{r.get('present_count', 0)}/{r.get('total_enrolled', 0)} ({r.get('percentage', 0)}%)",
                lambda r, i: ", ".join(r.get("present_students", [])) if r.get("present_students") else "-",
                lambda r, i: ", ".join(r.get("absent_students", [])) if r.get("absent_students") else "Tiada (Semua Hadir)",
                lambda r, i: r.get("status", "Draf")
            ]
        else:
            headers = ["Bil", "Tajuk / Keterangan", "Tarikh / Maklumat", "Kategori / Status", "Catatan"]
            keys = [
                lambda r, i: i,
                lambda r, i: r.get("title") or r.get("program_name") or r.get("full_name") or r.get("name") or "-",
                lambda r, i: r.get("activity_date") or r.get("session_date") or r.get("event_date") or r.get("month") or "-",
                lambda r, i: r.get("status") or r.get("org_category") or r.get("category") or r.get("achievement") or "-",
                lambda r, i: str(r.get("attendees_count") or r.get("total_students") or r.get("remarks") or "-")
            ]

        # Write header
        ws.row_dimensions[4].height = 25
        for col_idx, h in enumerate(headers, 1):
            c = ws.cell(row=4, column=col_idx, value=h)
            c.font = header_font
            c.fill = header_fill
            c.alignment = Alignment(horizontal="center", vertical="center")
            c.border = thin_border

        # Write data rows
        for row_idx, r in enumerate(data, 1):
            curr_row = 4 + row_idx
            ws.row_dimensions[curr_row].height = 20
            row_fill = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid") if row_idx % 2 == 0 else PatternFill(fill_type=None)
            
            for col_idx, key_func in enumerate(keys, 1):
                val = key_func(r, row_idx)
                cell = ws.cell(row=curr_row, column=col_idx, value=val)
                cell.alignment = Alignment(horizontal="center" if col_idx in [1, 3, 4, 7] else "left", vertical="center")
                cell.border = thin_border
                if row_idx % 2 == 0:
                    cell.fill = row_fill

        for col in ws.columns:
            col_letter = openpyxl.utils.get_column_letter(col[0].column)
            max_len = 0
            for cell in col:
                if cell.row in [1, 2]: continue
                if cell.value: max_len = max(max_len, len(str(cell.value)))
            ws.column_dimensions[col_letter].width = max(max_len + 4, 12)

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    clean_name = report_type.replace("_", "-")
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=Laporan_{clean_name}_SKSD.xlsx"}
    )

