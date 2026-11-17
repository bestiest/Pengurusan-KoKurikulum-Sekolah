from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
import re
from app.database import get_db_connection, log_audit
from app.auth import get_current_user, require_roles, require_deletion_roles

router = APIRouter(prefix="/api/sports", tags=["sports"])

def parse_record_num(val_str: Optional[str]) -> Optional[float]:
    if not val_str:
        return None
    cleaned = re.sub(r"[^\d.]", "", str(val_str).strip())
    try:
        return float(cleaned) if cleaned else None
    except ValueError:
        return None

# ==========================================
# 1. SPORTS EVENTS & SCHOOL RECORDS
# ==========================================
class SportsEventCreate(BaseModel):
    event_name: str
    category: str = "Balapan"  # Balapan, Padang, Sukaneka
    gender: str = "Lelaki"     # Lelaki, Perempuan, Campuran
    grade_level: str = "Tahap 2" # Tahap 1, Tahap 2, Terbuka
    event_type: str = "Individu" # Individu, Kumpulan
    metric_type: str = "Masa (Saat)" # Masa (Saat), Jarak/Ketinggian (Meter)
    school_record_holder: Optional[str] = None
    school_record_value: Optional[str] = None
    school_record_year: Optional[str] = None
    event_date: Optional[str] = "2026-07-15"
    academic_year: Optional[str] = "2026/2027"

@router.get("/events")
async def list_sports_events(user: Dict[str, Any] = Depends(get_current_user)):
    conn = get_db_connection()
    events = conn.execute("""
    SELECT se.*,
        COUNT(DISTINCT sp.student_id) as participants_count,
        COUNT(DISTINCT sr.id) as results_count
    FROM school_sports_events se
    LEFT JOIN school_sports_participants sp ON se.id = sp.event_id
    LEFT JOIN school_sports_results sr ON se.id = sr.event_id
    GROUP BY se.id
    ORDER BY se.id ASC
    """).fetchall()

    result = []
    for ev in events:
        ed = dict(ev)
        # Fetch placings if any
        results = conn.execute("""
        SELECT sr.*, s.full_name, s.class_name, s.gender, o.name as sport_house_name, o.color_code as house_color
        FROM school_sports_results sr
        JOIN students s ON sr.student_id = s.id
        JOIN organizations o ON sr.sport_house_id = o.id
        WHERE sr.event_id = ?
        ORDER BY sr.position_rank ASC
        """, (ed["id"],)).fetchall()
        ed["results"] = [dict(r) for r in results]
        result.append(ed)

    conn.close()
    return result

@router.post("/events")
async def create_or_update_sports_event(
    event: SportsEventCreate,
    event_id: Optional[int] = None,
    user: Dict[str, Any] = Depends(require_roles("Admin", "GPK Kokurikulum", "Setiausaha Kokurikulum", "Guru Pemimpin"))
):
    conn = get_db_connection()
    rec_num = parse_record_num(event.school_record_value)

    if event_id:
        conn.execute("""
        UPDATE school_sports_events
        SET event_name = ?, category = ?, gender = ?, grade_level = ?, event_type = ?,
            metric_type = ?, school_record_holder = ?, school_record_value = ?, school_record_year = ?,
            school_record_num = ?, event_date = ?, academic_year = ?
        WHERE id = ?
        """, (
            event.event_name, event.category, event.gender, event.grade_level, event.event_type,
            event.metric_type, event.school_record_holder, event.school_record_value, event.school_record_year,
            rec_num, event.event_date, event.academic_year, event_id
        ))
        action_name = "KEMASKINI_ACARA_SUKAN"
        action_desc = f"Mengemaskini acara {event.event_name}"
    else:
        cursor = conn.execute("""
        INSERT INTO school_sports_events (
            event_name, category, gender, grade_level, event_type, metric_type,
            school_record_holder, school_record_value, school_record_year, school_record_num,
            event_date, academic_year, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Pendaftaran')
        """, (
            event.event_name, event.category, event.gender, event.grade_level, event.event_type,
            event.metric_type, event.school_record_holder, event.school_record_value, event.school_record_year,
            rec_num, event.event_date, event.academic_year
        ))
        event_id = cursor.lastrowid
        action_name = "CIPTA_ACARA_SUKAN"
        action_desc = f"Mencipta acara {event.event_name}"

    conn.commit()
    conn.close()
    log_audit(user["id"], user["username"], user["role"], action_name, "Kejohanan Sukan", action_desc, event_id)
    return {"message": "Acara sukan berjaya disimpan.", "event_id": event_id}

@router.delete("/events/{event_id}")
async def delete_sports_event(
    event_id: int,
    user: Dict[str, Any] = Depends(require_deletion_roles())
):
    conn = get_db_connection()
    conn.execute("DELETE FROM school_sports_events WHERE id = ?", (event_id,))
    conn.commit()
    conn.close()
    log_audit(user["id"], user["username"], user["role"], "PADAM_ACARA_SUKAN", "Kejohanan Sukan", f"Memadam acara sukan ID {event_id}", event_id)
    return {"message": "Acara sukan berjaya dipadam."}

# ==========================================
# 2. HOUSE STUDENT ENROLLMENT (PENDAFTARAN ACARA MURID)
# ==========================================
@router.get("/house-enrollments/{sport_house_id}")
async def get_house_enrollments(sport_house_id: int, user: Dict[str, Any] = Depends(get_current_user)):
    conn = get_db_connection()
    house = conn.execute("SELECT * FROM organizations WHERE id = ? AND category = 'Rumah Sukan'", (sport_house_id,)).fetchone()
    if not house:
        conn.close()
        raise HTTPException(status_code=404, detail="Rumah sukan tidak dijumpai.")

    students = conn.execute("""
    SELECT id, full_name, ic_number, grade, class_name, gender
    FROM students
    WHERE sport_house_id = ?
    ORDER BY grade ASC, class_name ASC, full_name ASC
    """, (sport_house_id,)).fetchall()

    events = conn.execute("SELECT * FROM school_sports_events ORDER BY id ASC").fetchall()

    # Get enrolled event IDs per student
    enrollments = conn.execute("""
    SELECT student_id, event_id, lane_number, bib_number
    FROM school_sports_participants
    WHERE sport_house_id = ?
    """, (sport_house_id,)).fetchall()

    conn.close()

    st_enrolled_map = {}
    st_bib_map = {}
    for en in enrollments:
        d = dict(en)
        st_enrolled_map.setdefault(d["student_id"], []).append(d["event_id"])
        if d["bib_number"]:
            st_bib_map[d["student_id"]] = d["bib_number"]

    st_list = []
    for s in students:
        sd = dict(s)
        sd["enrolled_events"] = st_enrolled_map.get(sd["id"], [])
        sd["bib_number"] = st_bib_map.get(sd["id"], f"{dict(house)['name'][6] if len(dict(house)['name']) > 6 else 'R'}{sd['id']:02d}")
        st_list.append(sd)

    return {
        "house": dict(house),
        "students": st_list,
        "events": [dict(e) for e in events]
    }

class HouseEnrollmentItem(BaseModel):
    student_id: int
    event_ids: List[int]
    bib_number: Optional[str] = None

class HouseEnrollmentBatch(BaseModel):
    sport_house_id: int
    enrollments: List[HouseEnrollmentItem]

@router.post("/house-enrollments")
async def save_house_enrollments(
    data: HouseEnrollmentBatch,
    user: Dict[str, Any] = Depends(require_roles("Admin", "GPK Kokurikulum", "Setiausaha Kokurikulum", "Guru Pemimpin"))
):
    conn = get_db_connection()
    for item in data.enrollments:
        # Clear existing participant events for this student
        conn.execute("DELETE FROM school_sports_participants WHERE student_id = ?", (item.student_id,))
        for ev_id in item.event_ids:
            conn.execute("""
            INSERT OR REPLACE INTO school_sports_participants (event_id, student_id, sport_house_id, bib_number, academic_year)
            VALUES (?, ?, ?, ?, '2026/2027')
            """, (ev_id, item.student_id, data.sport_house_id, item.bib_number))

    conn.commit()
    conn.close()
    log_audit(user["id"], user["username"], user["role"], "DAFTAR_ACARA_RUMAH_SUKAN", "Kejohanan Sukan", f"Mendaftarkan acara murid untuk Rumah Sukan ID {data.sport_house_id}", data.sport_house_id)
    return {"message": "Pendaftaran acara murid berjaya disimpan."}

# ==========================================
# 3. JANAAN LORONG & GILIRAN (START LIST)
# ==========================================
@router.post("/generate-lanes/{event_id}")
async def generate_event_lanes(
    event_id: int,
    user: Dict[str, Any] = Depends(require_roles("Admin", "GPK Kokurikulum", "Setiausaha Kokurikulum", "Guru Pemimpin"))
):
    conn = get_db_connection()
    participants = conn.execute("""
    SELECT sp.*, o.name as house_name, s.full_name
    FROM school_sports_participants sp
    JOIN organizations o ON sp.sport_house_id = o.id
    JOIN students s ON sp.student_id = s.id
    WHERE sp.event_id = ?
    ORDER BY sp.sport_house_id ASC, sp.id ASC
    """, (event_id,)).fetchall()

    if not participants:
        conn.close()
        raise HTTPException(status_code=400, detail="Tiada peserta didaftarkan untuk acara ini.")

    # Assign lanes 1 to 8 in balanced house order
    for idx, p in enumerate(participants, start=1):
        lane_no = idx if idx <= 8 else ((idx - 1) % 8) + 1
        conn.execute("""
        UPDATE school_sports_participants
        SET lane_number = ?
        WHERE id = ?
        """, (lane_no, dict(p)["id"]))

    conn.commit()
    conn.close()
    return {"message": f"Janaan lorong berjaya untuk {len(participants)} peserta.", "event_id": event_id}

@router.get("/start-list/{event_id}")
async def get_event_start_list(event_id: int, user: Dict[str, Any] = Depends(get_current_user)):
    conn = get_db_connection()
    event = conn.execute("SELECT * FROM school_sports_events WHERE id = ?", (event_id,)).fetchone()
    if not event:
        conn.close()
        raise HTTPException(status_code=404, detail="Acara tidak dijumpai.")

    participants = conn.execute("""
    SELECT sp.*, s.full_name, s.ic_number, s.class_name, s.gender, o.name as sport_house_name, o.color_code as house_color
    FROM school_sports_participants sp
    JOIN students s ON sp.student_id = s.id
    JOIN organizations o ON sp.sport_house_id = o.id
    WHERE sp.event_id = ?
    ORDER BY COALESCE(sp.lane_number, 99) ASC, o.id ASC
    """, (event_id,)).fetchall()

    school = conn.execute("SELECT * FROM school_settings WHERE id = 1").fetchone()
    conn.close()

    return {
        "event": dict(event),
        "participants": [dict(p) for p in participants],
        "school": dict(school) if school else None
    }

# ==========================================
# 4. KEMASUKAN KEPUTUSAN & PENGESANAN PECAH REKOD
# ==========================================
class PlacingResultItem(BaseModel):
    position_rank: int # 1, 2, 3, 4
    student_id: int
    record_metric: Optional[str] = None # e.g. "11.8s" or "4.85m"
    remarks: Optional[str] = None

class EventResultsSubmission(BaseModel):
    event_id: int
    placings: List[PlacingResultItem]

@router.post("/record-results")
async def record_event_results(
    data: EventResultsSubmission,
    user: Dict[str, Any] = Depends(require_roles("Admin", "GPK Kokurikulum", "Setiausaha Kokurikulum", "Guru Pemimpin"))
):
    conn = get_db_connection()
    event = conn.execute("SELECT * FROM school_sports_events WHERE id = ?", (data.event_id,)).fetchone()
    if not event:
        conn.close()
        raise HTTPException(status_code=404, detail="Acara tidak dijumpai.")

    ev_dict = dict(event)
    settings = conn.execute("SELECT * FROM sports_scoring_settings WHERE id = 1").fetchone()
    set_dict = dict(settings) if settings else {
        "individual_1st": 7, "individual_2nd": 5, "individual_3rd": 3, "individual_4th": 1,
        "group_1st": 14, "group_2nd": 10, "group_3rd": 6, "group_4th": 2,
        "record_broken_bonus": 2
    }

    is_group = ev_dict.get("event_type") == "Kumpulan"
    pts_map = {
        1: set_dict["group_1st"] if is_group else set_dict["individual_1st"],
        2: set_dict["group_2nd"] if is_group else set_dict["individual_2nd"],
        3: set_dict["group_3rd"] if is_group else set_dict["individual_3rd"],
        4: set_dict["group_4th"] if is_group else set_dict["individual_4th"]
    }
    pajsk_map = { 1: 8.0, 2: 7.0, 3: 6.0, 4: 5.0 }
    medal_map = { 1: "Pingat Emas", 2: "Pingat Perak", 3: "Pingat Gangsa", 4: "Tempat Ke-4" }

    # Delete existing results for this event
    conn.execute("DELETE FROM school_sports_results WHERE event_id = ?", (data.event_id,))

    school_rec_num = ev_dict.get("school_record_num")
    metric_type = ev_dict.get("metric_type") or "Masa (Saat)"

    new_champ_record = None

    for item in data.placings:
        st = conn.execute("SELECT sport_house_id, full_name FROM students WHERE id = ?", (item.student_id,)).fetchone()
        if not st:
            continue
        house_id = dict(st)["sport_house_id"]
        rec_num = parse_record_num(item.record_metric)

        # Check record broken:
        # For time (Masa): lower is better (rec_num < school_rec_num)
        # For distance/height: higher is better (rec_num > school_rec_num)
        is_broken = 0
        bonus_pts = 0
        if rec_num is not None and school_rec_num is not None and school_rec_num > 0:
            if "Masa" in metric_type:
                if rec_num < school_rec_num:
                    is_broken = 1
                    bonus_pts = set_dict.get("record_broken_bonus", 2)
            else:
                if rec_num > school_rec_num:
                    is_broken = 1
                    bonus_pts = set_dict.get("record_broken_bonus", 2)

        base_pts = pts_map.get(item.position_rank, 1)
        total_pts = base_pts + bonus_pts
        p_score = pajsk_map.get(item.position_rank, 4.0)

        conn.execute("""
        INSERT INTO school_sports_results (
            event_id, student_id, sport_house_id, position_rank, medal_type,
            record_metric, record_num, is_record_broken, house_points, bonus_points, pajsk_score, remarks
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.event_id, item.student_id, house_id, item.position_rank, medal_map.get(item.position_rank, "Peserta"),
            item.record_metric, rec_num, is_broken, total_pts, bonus_pts, p_score, item.remarks
        ))

        # If 1st place broke the record, record for updating school record
        if item.position_rank == 1 and is_broken == 1:
            house_name = conn.execute("SELECT name FROM organizations WHERE id = ?", (house_id,)).fetchone()
            h_str = dict(house_name)["name"] if house_name else ""
            new_champ_record = {
                "holder": f"{dict(st)['full_name']} ({h_str})",
                "value": item.record_metric,
                "num": rec_num,
                "year": "2026"
            }

    # Update event status
    conn.execute("UPDATE school_sports_events SET status = 'Selesai' WHERE id = ?", (data.event_id,))

    # Update school record if broken by champion
    if new_champ_record:
        conn.execute("""
        UPDATE school_sports_events
        SET school_record_holder = ?, school_record_value = ?, school_record_num = ?, school_record_year = ?
        WHERE id = ?
        """, (new_champ_record["holder"], new_champ_record["value"], new_champ_record["num"], new_champ_record["year"], data.event_id))

    conn.commit()
    conn.close()
    log_audit(user["id"], user["username"], user["role"], "REKOD_KEPUTUSAN_SUKAN", "Kejohanan Sukan", f"Merekod keputusan bagi acara {ev_dict['event_name']}", data.event_id)
    return {"message": "Keputusan acara sukan berjaya direkodkan!", "record_broken": bool(new_champ_record)}

@router.delete("/results/{event_id}")
async def delete_sports_event_results(
    event_id: int,
    user: Dict[str, Any] = Depends(require_deletion_roles())
):
    conn = get_db_connection()
    ev = conn.execute("SELECT event_name FROM school_sports_events WHERE id = ?", (event_id,)).fetchone()
    ev_name = dict(ev)["event_name"] if ev else f"ID {event_id}"

    conn.execute("DELETE FROM school_sports_results WHERE event_id = ?", (event_id,))
    conn.execute("UPDATE school_sports_events SET status = 'Pendaftaran' WHERE id = ?", (event_id,))
    conn.commit()
    conn.close()

    log_audit(user["id"], user["username"], user["role"], "PADAM_KEPUTUSAN_SUKAN", "Kejohanan Sukan", f"Memadam keputusan acara sukan {ev_name}", event_id)
    return {"message": f"Keputusan acara '{ev_name}' berjaya dipadam dan status diset semula ke Pendaftaran."}

# ==========================================
# 5. KEDUDUKAN KESELURUHAN & OLAHRAGAWAN
# ==========================================
@router.get("/overall-standings")
async def get_sports_overall_standings(user: Dict[str, Any] = Depends(get_current_user)):
    conn = get_db_connection()
    houses = conn.execute("SELECT id, name, color_code FROM organizations WHERE category = 'Rumah Sukan'").fetchall()
    settings = conn.execute("SELECT * FROM sports_scoring_settings WHERE id = 1").fetchone()
    inc_cc = dict(settings).get("include_cross_country", 1) if settings else 1

    house_summary = []
    for h in houses:
        hd = dict(h)
        hid = hd["id"]

        # Sports Day tally
        sd_stats = conn.execute("""
        SELECT 
            SUM(CASE WHEN position_rank = 1 THEN 1 ELSE 0 END) as sd_gold,
            SUM(CASE WHEN position_rank = 2 THEN 1 ELSE 0 END) as sd_silver,
            SUM(CASE WHEN position_rank = 3 THEN 1 ELSE 0 END) as sd_bronze,
            SUM(CASE WHEN position_rank = 4 THEN 1 ELSE 0 END) as sd_fourth,
            SUM(is_record_broken) as sd_broken_records,
            COALESCE(SUM(house_points), 0) as sd_points
        FROM school_sports_results
        WHERE sport_house_id = ?
        """, (hid,)).fetchone()
        sd_d = dict(sd_stats) if sd_stats else {}

        # Cross Country tally
        cc_stats = conn.execute("""
        SELECT 
            SUM(CASE WHEN rank_position = 1 THEN 1 ELSE 0 END) as cc_gold,
            SUM(CASE WHEN rank_position = 2 THEN 1 ELSE 0 END) as cc_silver,
            SUM(CASE WHEN rank_position = 3 THEN 1 ELSE 0 END) as cc_bronze,
            COUNT(id) as cc_finishers,
            COALESCE(SUM(house_points), 0) as cc_points
        FROM cross_country_records
        WHERE sport_house_id = ?
        """, (hid,)).fetchone()
        cc_d = dict(cc_stats) if cc_stats else {}

        sd_pts = sd_d.get("sd_points") or 0
        cc_pts = (cc_d.get("cc_points") or 0) if inc_cc else 0
        total_pts = sd_pts + cc_pts

        gold_total = (sd_d.get("sd_gold") or 0) + ((cc_d.get("cc_gold") or 0) if inc_cc else 0)
        silver_total = (sd_d.get("sd_silver") or 0) + ((cc_d.get("cc_silver") or 0) if inc_cc else 0)
        bronze_total = (sd_d.get("sd_bronze") or 0) + ((cc_d.get("cc_bronze") or 0) if inc_cc else 0)

        hd.update({
            "sd_gold": sd_d.get("sd_gold") or 0,
            "sd_silver": sd_d.get("sd_silver") or 0,
            "sd_bronze": sd_d.get("sd_bronze") or 0,
            "sd_fourth": sd_d.get("sd_fourth") or 0,
            "sd_broken_records": sd_d.get("sd_broken_records") or 0,
            "sd_points": sd_pts,
            "cc_gold": cc_d.get("cc_gold") or 0,
            "cc_silver": cc_d.get("cc_silver") or 0,
            "cc_bronze": cc_d.get("cc_bronze") or 0,
            "cc_finishers": cc_d.get("cc_finishers") or 0,
            "cc_points": cc_pts,
            "total_gold": gold_total,
            "total_silver": silver_total,
            "total_bronze": bronze_total,
            "total_points": total_pts
        })
        house_summary.append(hd)

    # Sort by total points, then total gold
    house_summary.sort(key=lambda x: (x["total_points"], x["total_gold"], x["total_silver"]), reverse=True)

    # ==========================================
    # Calculate Best Athletes (Olahragawan & Olahragawati)
    # ==========================================
    def get_top_athlete(gender: str, grade_list: List[int]):
        query = """
        SELECT 
            s.id as student_id, s.full_name, s.ic_number, s.class_name, s.grade, s.gender,
            o.name as sport_house_name, o.color_code as house_color,
            SUM(CASE WHEN sr.position_rank = 1 THEN 1 ELSE 0 END) as gold_count,
            SUM(CASE WHEN sr.position_rank = 2 THEN 1 ELSE 0 END) as silver_count,
            SUM(CASE WHEN sr.position_rank = 3 THEN 1 ELSE 0 END) as bronze_count,
            SUM(sr.is_record_broken) as broken_records_count,
            SUM(sr.house_points) as total_points,
            GROUP_CONCAT(se.event_name || ' (' || sr.medal_type || ')') as achievements
        FROM school_sports_results sr
        JOIN students s ON sr.student_id = s.id
        JOIN school_sports_events se ON sr.event_id = se.id
        JOIN organizations o ON sr.sport_house_id = o.id
        WHERE s.gender = ? AND s.grade IN ({})
        GROUP BY s.id
        ORDER BY gold_count DESC, broken_records_count DESC, total_points DESC, silver_count DESC
        LIMIT 1
        """.format(",".join("?" * len(grade_list)))
        params = [gender] + grade_list
        row = conn.execute(query, tuple(params)).fetchone()
        return dict(row) if row else None

    olahragawan = get_top_athlete("Lelaki", [4, 5, 6])
    olahragawati = get_top_athlete("Perempuan", [4, 5, 6])
    olahragawan_harapan = get_top_athlete("Lelaki", [1, 2, 3])
    olahragawati_harapan = get_top_athlete("Perempuan", [1, 2, 3])

    school = conn.execute("SELECT * FROM school_settings WHERE id = 1").fetchone()
    conn.close()

    return {
        "house_summary": house_summary,
        "champion_house": house_summary[0] if house_summary else None,
        "olahragawan": olahragawan,
        "olahragawati": olahragawati,
        "olahragawan_harapan": olahragawan_harapan,
        "olahragawati_harapan": olahragawati_harapan,
        "scoring_settings": dict(settings) if settings else None,
        "school": dict(school) if school else None
    }

# ==========================================
# 6. SCORING SETTINGS CONFIG
# ==========================================
class ScoringSettingsUpdate(BaseModel):
    individual_1st: int = 7
    individual_2nd: int = 5
    individual_3rd: int = 3
    individual_4th: int = 1
    group_1st: int = 14
    group_2nd: int = 10
    group_3rd: int = 6
    group_4th: int = 2
    record_broken_bonus: int = 2
    include_cross_country: int = 1

@router.get("/scoring-settings")
async def get_scoring_settings(user: Dict[str, Any] = Depends(get_current_user)):
    conn = get_db_connection()
    row = conn.execute("SELECT * FROM sports_scoring_settings WHERE id = 1").fetchone()
    conn.close()
    return dict(row) if row else {}

@router.post("/scoring-settings")
async def update_scoring_settings(
    settings: ScoringSettingsUpdate,
    user: Dict[str, Any] = Depends(require_roles("Admin", "GPK Kokurikulum", "Setiausaha Kokurikulum"))
):
    conn = get_db_connection()
    conn.execute("""
    UPDATE sports_scoring_settings
    SET individual_1st = ?, individual_2nd = ?, individual_3rd = ?, individual_4th = ?,
        group_1st = ?, group_2nd = ?, group_3rd = ?, group_4th = ?,
        record_broken_bonus = ?, include_cross_country = ?
    WHERE id = 1
    """, (
        settings.individual_1st, settings.individual_2nd, settings.individual_3rd, settings.individual_4th,
        settings.group_1st, settings.group_2nd, settings.group_3rd, settings.group_4th,
        settings.record_broken_bonus, settings.include_cross_country
    ))
    conn.commit()
    conn.close()
    log_audit(user["id"], user["username"], user["role"], "KEMASKINI_MARKAH_SUKAN", "Kejohanan Sukan", "Mengemaskini penetapan markah sukan tahunan", 1)
    return {"message": "Tetapan markah kejohanan berjaya dikemaskini."}
