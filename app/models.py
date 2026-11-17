from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class UserLogin(BaseModel):
    username: str
    password: str

class UserCreate(BaseModel):
    username: str
    password: Optional[str] = "aba6038"
    full_name: str
    role: str
    email: Optional[str] = None
    phone: Optional[str] = None
    assigned_category: Optional[str] = None
    assigned_org_ids: Optional[str] = None

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    role: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    assigned_category: Optional[str] = None
    assigned_org_ids: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[int] = 1

class ResetPasswordRequest(BaseModel):
    new_password: Optional[str] = "aba6038"

class StudentCreate(BaseModel):
    full_name: Optional[str] = "MURID TANPA NAMA"
    ic_number: Optional[str] = None
    birth_date: Optional[str] = None
    gender: Optional[str] = "Lelaki"
    grade: Optional[int] = 1
    class_name: Optional[str] = None
    guardian_name: Optional[str] = None
    guardian_phone: Optional[str] = None
    address: Optional[str] = None
    health_info: Optional[str] = "Tiada"
    sport_house_id: Optional[int] = None
    uniform_unit_id: Optional[int] = None
    club_society_id: Optional[int] = None
    sports_game_id: Optional[int] = None
    status: Optional[str] = "Aktif"
    academic_year: Optional[str] = "2026/2027"

class StudentUpdate(BaseModel):
    full_name: Optional[str] = None
    ic_number: Optional[str] = None
    birth_date: Optional[str] = None
    gender: Optional[str] = None
    grade: Optional[int] = None
    class_name: Optional[str] = None
    guardian_name: Optional[str] = None
    guardian_phone: Optional[str] = None
    address: Optional[str] = None
    health_info: Optional[str] = None
    sport_house_id: Optional[int] = None
    uniform_unit_id: Optional[int] = None
    club_society_id: Optional[int] = None
    sports_game_id: Optional[int] = None
    status: Optional[str] = None
    academic_year: Optional[str] = None

class BulkAssignOrg(BaseModel):
    student_ids: List[int]
    category: str
    organization_id: int

class OrganizationCreate(BaseModel):
    name: str
    category: str
    code: Optional[str] = None
    advisor_teachers: Optional[str] = None
    coordinator_name: Optional[str] = None
    logo_icon: Optional[str] = None
    color_code: Optional[str] = "#1e40af"
    vision_mission: Optional[str] = None
    meeting_day: Optional[str] = "Rabu"
    meeting_time: Optional[str] = "2:00 PM - 4:00 PM"
    meeting_venue: Optional[str] = None
    academic_year: Optional[str] = "2026/2027"
    status: Optional[str] = "Aktif"

class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    code: Optional[str] = None
    advisor_teachers: Optional[str] = None
    coordinator_name: Optional[str] = None
    logo_icon: Optional[str] = None
    color_code: Optional[str] = None
    vision_mission: Optional[str] = None
    meeting_day: Optional[str] = None
    meeting_time: Optional[str] = None
    meeting_venue: Optional[str] = None
    status: Optional[str] = None

class CommitteeMemberAssign(BaseModel):
    student_id: int
    position: str
    notes: Optional[str] = None

class AttendanceRecordItem(BaseModel):
    student_id: int
    status: str
    remarks: Optional[str] = None

class AttendanceSessionCreate(BaseModel):
    organization_id: int
    session_date: str
    start_time: Optional[str] = "14:00"
    end_time: Optional[str] = "16:00"
    venue: Optional[str] = "Dewan Terbuka"
    activity_title: str
    advisor_teacher: Optional[str] = None
    notes: Optional[str] = None
    records: List[AttendanceRecordItem]

class ActivityAttendanceItem(BaseModel):
    student_id: int
    status: str = "Hadir"
    remarks: Optional[str] = None

class ActivityCreate(BaseModel):
    organization_id: int
    activity_date: str
    start_time: Optional[str] = "14:00"
    end_time: Optional[str] = "16:00"
    venue: Optional[str] = None
    title: str
    objectives: Optional[str] = None
    description_rundown: Optional[str] = None
    teachers_involved: Optional[str] = None
    attendees_count: Optional[int] = 0
    reflection: Optional[str] = None
    suggestions: Optional[str] = None
    photo_1: Optional[str] = None
    photo_2: Optional[str] = None
    photo_3: Optional[str] = None
    photo_4: Optional[str] = None
    attachment_file: Optional[str] = None
    status: Optional[str] = "Draf"
    attendance_records: Optional[List[ActivityAttendanceItem]] = None

class ActivityUpdate(BaseModel):
    organization_id: Optional[int] = None
    activity_date: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    venue: Optional[str] = None
    title: Optional[str] = None
    objectives: Optional[str] = None
    description_rundown: Optional[str] = None
    teachers_involved: Optional[str] = None
    attendees_count: Optional[int] = None
    reflection: Optional[str] = None
    suggestions: Optional[str] = None
    photo_1: Optional[str] = None
    photo_2: Optional[str] = None
    photo_3: Optional[str] = None
    photo_4: Optional[str] = None
    attachment_file: Optional[str] = None
    status: Optional[str] = None
    review_remarks: Optional[str] = None
    attendance_records: Optional[List[ActivityAttendanceItem]] = None

class ActivityStatusAction(BaseModel):
    status: str
    remarks: Optional[str] = None

class PermissionLetterCreate(BaseModel):
    letter_no: Optional[str] = None
    program_name: str
    destination_venue: str
    start_datetime: str
    end_datetime: str
    organizer: str
    transportation: Optional[str] = "Bas Sekolah"
    accompanying_teachers: Optional[str] = None
    fee_amount: Optional[float] = 0.0
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    special_instructions: Optional[str] = None
    participation_level: Optional[str] = "Daerah"
    activity_category: Optional[str] = "Sukan & Permainan"
    represented_org_id: Optional[int] = None
    student_ids: List[int] = []

class PermissionStatusUpdate(BaseModel):
    permission_status: Optional[str] = "Belum Diedarkan"
    parent_notes: Optional[str] = None
    jersey_no: Optional[str] = None

class StudentJerseyUpdate(BaseModel):
    jersey_no: str

class ExternalParticipationStudentItem(BaseModel):
    student_id: int
    role: str = "Peserta"
    achievement: str = "Penyertaan"
    pajsk_score: Optional[float] = 0.0
    remarks: Optional[str] = None

class ExternalParticipationCreate(BaseModel):
    program_name: str
    event_date: str
    venue: str
    organizer: str
    activity_category: str
    participation_level: str
    represented_org_id: Optional[int] = None
    notes: Optional[str] = None
    certificate_url: Optional[str] = None
    evidence_url: Optional[str] = None
    students: List[ExternalParticipationStudentItem] = []

class SchoolSettingsUpdate(BaseModel):
    school_name: Optional[str] = None
    school_code: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    principal_name: Optional[str] = None
    gpk_koko_name: Optional[str] = None
    su_koko_name: Optional[str] = None
    session_year: Optional[str] = None
    logo_url: Optional[str] = None
    letter_template: Optional[str] = None

class ClassCreate(BaseModel):
    grade: int
    class_name: str
    class_teacher: Optional[str] = None
    academic_year: Optional[str] = "2026/2027"

class TeacherCreate(BaseModel):
    name: str
    ic_number: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    designation: Optional[str] = "Guru Penolong"
