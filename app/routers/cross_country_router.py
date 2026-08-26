from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
import re
from app.database import get_db_connection, log_audit
from app.auth import get_current_user, require_roles

router = APIRouter(prefix="/api/cross-country", tags=["cross-country"])

def parse_time_to_seconds(time_str: Optional[str]) -> Optional[float]:
    if not time_str:
        return None
    s = str(time_str).strip().lower()
    # Format 1: "14m 15s" or "14m15s" or "14m"
    m_match = re.search(r"(\d+)\s*m(?:in)?(?:\s*(\d+)\s*s)?", s)
    if m_match:
        mins = int(m_match.group(1))
        secs = int(m_match.group(2)) if m_match.group(2) else 0
        return float(mins * 60 + secs)
    
    # Format 2: "14:15"
    colon_match = re.search(r"(\d+)[:.](\d+)", s)
    if colon_match:
        mins = int(colon_match.group(1))
        secs = int(colon_match.group(2))
        return float(mins * 60 + secs)
    
    # Format 3: Raw seconds "855"
    digits = re.sub(r"[^\d.]", "", s)
    try:
        val = float(digits)
        return val if val > 0 else None
    except ValueError:
        return None

# ==========================================
# 1. OVERVIEW & STANDINGS
# ==========================================
@router.get("/overview")
async def get_cross_country_overview(user: Dict[str, Any] = Depends(get_current_user)):
    conn = get_db_connection()

    # 1. Ensure categories exist
    categories = conn.execute("SELECT * FROM cross_country_categories ORDER BY id ASC").fetchall()
    cat_list = [dict(c) for c in categories]

    # 2. Fetch all records
    records = conn.execute("""
        SELECT ccr.*, 
               s.full_name, s.ic_number, s.class_name, s.gender as student_gender,
               o.name as sport_house_name, o.color_code as house_color
        FROM cross_country_records ccr
        LEFT JOIN students s ON ccr.student_id = s.id
        JOIN organizations o ON ccr.sport_house_id = o.id
        ORDER BY ccr.category ASC, ccr.rank_position ASC
    """).fetchall()
    rec_list = [dict(r) for r in records]

    # 3. House Tally
    houses = conn.execute("SELECT id, name, color_code FROM organizations WHERE category = 'Rumah Sukan'").fetchall()
    house_tally = []
    for h in houses:
        hd = dict(h)
        hid = hd["id"]
        stats = conn.execute("""
            SELECT 
                SUM(CASE WHEN rank_position = 1 THEN 1 ELSE 0 END) as gold,
                SUM(CASE WHEN rank_position = 2 THEN 1 ELSE 0 END) as silver,
                SUM(CASE WHEN rank_position = 3 THEN 1 ELSE 0 END) as bronze,
                SUM(CASE WHEN rank_position <= 15 THEN 1 ELSE 0 END) as top_15_finishers,
                SUM(CASE WHEN rank_position > 15 THEN 1 ELSE 0 END) as zone_16_50_finishers,
                COUNT(id) as total_finishers,
                SUM(is_record_broken) as broken_records_count,
                COALESCE(SUM(house_points), 0) as total_points
            FROM cross_country_records
            WHERE sport_house_id = ?
        """, (hid,)).fetchone()
        st = dict(stats) if stats else {}
        hd["gold"] = st.get("gold") or 0
        hd["silver"] = st.get("silver") or 0
        hd["bronze"] = st.get("bronze") or 0
        hd["top_15_finishers"] = st.get("top_15_finishers") or 0
        hd["zone_16_50_finishers"] = st.get("zone_16_50_finishers") or 0
        hd["total_finishers"] = st.get("total_finishers") or 0
        hd["broken_records_count"] = st.get("broken_records_count") or 0
        hd["total_points"] = st.get("total_points") or 0
        house_tally.append(hd)

    house_tally.sort(key=lambda x: (x.get("total_points", 0), x.get("gold", 0)), reverse=True)

    # 4. Group by Category (Lelaki Tahap 2 & Perempuan Tahap 2)
    categories_data = []
    for cat in cat_list:
        cat_name = cat["category_name"]
        cat_recs = [r for r in rec_list if r["category"] == cat_name]

        # Top 15 Individual Placings
        ind_winners = [r for r in cat_recs if r["rank_position"] <= 15]

        # 16 to 50 Zone Breakdown by House
        zone_16_50 = [r for r in cat_recs if r["rank_position"] > 15]
        house_breakdown_16_50 = {}
        for h in houses:
            hd = dict(h)
            h_recs = [r for r in zone_16_50 if r["sport_house_id"] == hd["id"]]
            house_breakdown_16_50[hd["name"]] = {
                "house_id": hd["id"],
                "house_name": hd["name"],
                "color_code": hd["color_code"],
                "finishers_count": len(h_recs),
                "total_points": sum(r["house_points"] for r in h_recs)
            }

        categories_data.append({
            "category": cat,
            "total_finishers": len(cat_recs),
            "individual_winners": ind_winners,
            "zone_16_50_summary": house_breakdown_16_50,
            "all_records": cat_recs
        })

    # 5. Scoring Settings & School Info
    settings = conn.execute("SELECT * FROM cross_country_scoring_settings WHERE id = 1").fetchone()
    school = conn.execute("SELECT * FROM school_settings WHERE id = 1").fetchone()
    conn.close()

    return {
        "categories_data": categories_data,
        "house_tally": house_tally,
        "scoring_settings": dict(settings) if settings else None,
        "school": dict(school) if school else None
    }

# ==========================================
# 2. RECORD RESULTS (UP TO 15 INDIVIDUALS + 16-50 HOUSE PLACINGS)
# ==========================================
class IndividualPlacingItem(BaseModel):
    rank_position: int  # 1 to 15
    student_id: int
    time_recorded: Optional[str] = None # Only for Top 3 (1, 2, 3)
    remarks: Optional[str] = None

class HouseOnlyPlacingItem(BaseModel):
    rank_position: int  # 16 to 50
    sport_house_id: int

class CrossCountryResultsSubmission(BaseModel):
    category_name: str
    individual_placings: List[IndividualPlacingItem]
    house_only_placings: Optional[List[HouseOnlyPlacingItem]] = []

@router.post("/record-results")
async def record_cross_country_results(
    data: CrossCountryResultsSubmission,
    user: Dict[str, Any] = Depends(require_roles("Admin", "GPK Kokurikulum", "Setiausaha Kokurikulum", "Guru Pemimpin"))
):
    try:
        conn = get_db_connection()

        # 1. Fetch Scoring Settings
        settings_row = conn.execute("SELECT * FROM cross_country_scoring_settings WHERE id = 1").fetchone()
        s = dict(settings_row) if settings_row else {}
        pts_map = {
            1: s.get("points_rank_1", 20),
            2: s.get("points_rank_2", 18),
            3: s.get("points_rank_3", 16),
            4: s.get("points_rank_4", 14),
            5: s.get("points_rank_5", 12),
            6: s.get("points_rank_6", 10),
            7: s.get("points_rank_7", 9),
            8: s.get("points_rank_8", 8),
            9: s.get("points_rank_9", 7),
            10: s.get("points_rank_10", 6),
            11: s.get("points_rank_11", 5),
            12: s.get("points_rank_12", 4),
            13: s.get("points_rank_13", 3),
            14: s.get("points_rank_14", 2),
            15: s.get("points_rank_15", 1)
        }
        uniform_16_50_pts = s.get("points_rank_16_to_50", 1)
        bonus_rec_pts = s.get("record_broken_bonus", 2)

        # 2. Fetch Category School Record Info
        cat_row = conn.execute("SELECT * FROM cross_country_categories WHERE category_name = ?", (data.category_name,)).fetchone()
        cat_dict = dict(cat_row) if cat_row else {}
        school_rec_seconds = cat_dict.get("school_record_seconds")

        # 3. Delete existing records for this category
        conn.execute("DELETE FROM cross_country_records WHERE category = ?", (data.category_name,))

        new_school_record = None

        valid_houses = [dict(h)["id"] for h in conn.execute("SELECT id FROM organizations WHERE category = 'Rumah Sukan'").fetchall()]
        fallback_house_id = valid_houses[0] if valid_houses else 1

        # 4. Insert Top 15 Individual Placings
        for ind in data.individual_placings:
            if not ind.student_id or ind.rank_position > 15:
                continue
            st = conn.execute("SELECT sport_house_id, full_name, class_name FROM students WHERE id = ?", (ind.student_id,)).fetchone()
            if not st:
                continue
            st_dict = dict(st)
            st_house = st_dict["sport_house_id"]
            house_id = st_house if st_house in valid_houses else fallback_house_id

            # Parse time recorded for Top 3
            time_sec = None
            is_broken = 0
            bonus = 0
            if ind.rank_position <= 3 and ind.time_recorded:
                time_sec = parse_time_to_seconds(ind.time_recorded)
                if time_sec and school_rec_seconds and school_rec_seconds > 0:
                    if time_sec < school_rec_seconds:
                        is_broken = 1
                        bonus = bonus_rec_pts
                        if ind.rank_position == 1:
                            house_name_row = conn.execute("SELECT name FROM organizations WHERE id = ?", (house_id,)).fetchone()
                            h_name = dict(house_name_row)["name"] if house_name_row else ""
                            new_school_record = {
                                "holder": f"{st_dict['full_name']} ({h_name})",
                                "time": ind.time_recorded,
                                "seconds": time_sec,
                                "year": "2026"
                            }

            base_pts = pts_map.get(ind.rank_position, 1)
            tot_pts = base_pts + bonus
            pajsk_pts = 8.0 if ind.rank_position == 1 else (7.0 if ind.rank_position == 2 else (6.0 if ind.rank_position == 3 else 5.0))

            conn.execute("""
                INSERT INTO cross_country_records (
                    category, student_id, sport_house_id, rank_position, time_recorded, time_seconds,
                    is_record_broken, house_points, bonus_points, pajsk_score, event_date, academic_year, remarks
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, '2026-05-10', '2026/2027', ?)
            """, (
                data.category_name, ind.student_id, house_id, ind.rank_position, ind.time_recorded, time_sec,
                is_broken, tot_pts, bonus, pajsk_pts, ind.remarks or f"Pemenang Tempat Ke-{ind.rank_position}"
            ))

        # 5. Insert 16 to 50 House Only Placings
        for h_only in (data.house_only_placings or []):
            if h_only.rank_position < 16 or h_only.rank_position > 50 or not h_only.sport_house_id:
                continue
            h_id = h_only.sport_house_id if h_only.sport_house_id in valid_houses else fallback_house_id
            conn.execute("""
                INSERT INTO cross_country_records (
                    category, student_id, sport_house_id, rank_position, time_recorded, time_seconds,
                    is_record_broken, house_points, bonus_points, pajsk_score, event_date, academic_year, remarks
                ) VALUES (?, NULL, ?, ?, NULL, NULL, 0, ?, 0, 3.0, '2026-05-10', '2026/2027', ?)
            """, (
                data.category_name, h_id, h_only.rank_position, uniform_16_50_pts, f"Penamat Ke-{h_only.rank_position}"
            ))

        # 6. Update Category School Record if broken by 1st place
        if new_school_record:
            conn.execute("""
                UPDATE cross_country_categories
                SET school_record_holder = ?, school_record_time = ?, school_record_seconds = ?, school_record_year = ?
                WHERE category_name = ?
            """, (new_school_record["holder"], new_school_record["time"], new_school_record["seconds"], new_school_record["year"], data.category_name))

        conn.commit()
        conn.close()

        log_audit(user["id"], user["username"], user["role"], "REKOD_KEPUTUSAN_MERENTAS_DESA", "Merentas Desa", f"Merekod keputusan merentas desa bagi {data.category_name}")
        return {
            "message": "Keputusan Merentas Desa berjaya direkodkan!",
            "record_broken": bool(new_school_record)
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/results/{category_name}")
async def delete_cross_country_results(
    category_name: str,
    user: Dict[str, Any] = Depends(require_roles("Admin", "GPK Kokurikulum", "Setiausaha Kokurikulum", "Guru Pemimpin"))
):
    try:
        conn = get_db_connection()
        conn.execute("DELETE FROM cross_country_records WHERE category = ?", (category_name,))
        conn.commit()
        conn.close()

        log_audit(user["id"], user["username"], user["role"], "PADAM_KEPUTUSAN_MERENTAS_DESA", "Merentas Desa", f"Memadam semua keputusan merentas desa bagi {category_name}")
        return {"message": f"Keputusan bagi kategori {category_name} berjaya dipadam/dikosongkan."}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# ==========================================
# 3. SCORING SETTINGS
# ==========================================
class CrossCountryScoringUpdate(BaseModel):
    max_individual_placings: int = 15
    max_total_finishers: int = 50
    points_rank_1: int = 20
    points_rank_2: int = 18
    points_rank_3: int = 16
    points_rank_4: int = 14
    points_rank_5: int = 12
    points_rank_6: int = 10
    points_rank_7: int = 9
    points_rank_8: int = 8
    points_rank_9: int = 7
    points_rank_10: int = 6
    points_rank_11: int = 5
    points_rank_12: int = 4
    points_rank_13: int = 3
    points_rank_14: int = 2
    points_rank_15: int = 1
    points_rank_16_to_50: int = 1
    record_broken_bonus: int = 2

@router.get("/scoring-settings")
async def get_cross_country_scoring_settings(user: Dict[str, Any] = Depends(get_current_user)):
    conn = get_db_connection()
    row = conn.execute("SELECT * FROM cross_country_scoring_settings WHERE id = 1").fetchone()
    conn.close()
    return dict(row) if row else {}

@router.post("/scoring-settings")
async def update_cross_country_scoring_settings(
    settings: CrossCountryScoringUpdate,
    user: Dict[str, Any] = Depends(require_roles("Admin", "GPK Kokurikulum", "Setiausaha Kokurikulum"))
):
    conn = get_db_connection()
    conn.execute("""
        UPDATE cross_country_scoring_settings
        SET max_individual_placings = ?, max_total_finishers = ?,
            points_rank_1 = ?, points_rank_2 = ?, points_rank_3 = ?, points_rank_4 = ?, points_rank_5 = ?,
            points_rank_6 = ?, points_rank_7 = ?, points_rank_8 = ?, points_rank_9 = ?, points_rank_10 = ?,
            points_rank_11 = ?, points_rank_12 = ?, points_rank_13 = ?, points_rank_14 = ?, points_rank_15 = ?,
            points_rank_16_to_50 = ?, record_broken_bonus = ?
        WHERE id = 1
    """, (
        settings.max_individual_placings, settings.max_total_finishers,
        settings.points_rank_1, settings.points_rank_2, settings.points_rank_3, settings.points_rank_4, settings.points_rank_5,
        settings.points_rank_6, settings.points_rank_7, settings.points_rank_8, settings.points_rank_9, settings.points_rank_10,
        settings.points_rank_11, settings.points_rank_12, settings.points_rank_13, settings.points_rank_14, settings.points_rank_15,
        settings.points_rank_16_to_50, settings.record_broken_bonus
    ))
    conn.commit()
    conn.close()
    log_audit(user["id"], user["username"], user["role"], "KEMASKINI_MARKAH_MERENTAS_DESA", "Merentas Desa", "Mengemaskini penetapan markah kejohanan merentas desa")
    return {"message": "Tetapan markah Merentas Desa berjaya dikemaskini."}

# ==========================================
# 4. CATEGORIES
# ==========================================
@router.get("/categories")
async def list_cross_country_categories(user: Dict[str, Any] = Depends(get_current_user)):
    conn = get_db_connection()
    cats = conn.execute("SELECT * FROM cross_country_categories ORDER BY id ASC").fetchall()
    conn.close()
    return [dict(c) for c in cats]
