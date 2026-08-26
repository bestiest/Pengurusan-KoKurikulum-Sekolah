from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pathlib import Path
from contextlib import asynccontextmanager

from app.database import init_db, get_db_connection
from app.seed_data import seed_demo_data
from app.routers import (
    auth_router,
    students_router,
    organizations_router,
    attendance_router,
    activities_router,
    permission_letters_router,
    pajsk_router,
    sports_router,
    cross_country_router,
    reports_router,
    settings_router
)

BASE_DIR = Path(__file__).resolve().parent

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB & demo data
    init_db()
    seed_demo_data(force=False)
    yield

app = FastAPI(
    title="Unit Kokurikulum Sekolah Kebangsaan Sungai Dendang",
    description="Sistem Pengurusan Lengkap Kokurikulum Sekolah Kebangsaan Sungai Dendang",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static and Templates
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")

# Include Routers
app.include_router(auth_router.router)
app.include_router(students_router.router)
app.include_router(organizations_router.router)
app.include_router(attendance_router.router)
app.include_router(activities_router.router)
app.include_router(permission_letters_router.router)
app.include_router(pajsk_router.router)
app.include_router(sports_router.router)
app.include_router(cross_country_router.router)
app.include_router(reports_router.router)
app.include_router(settings_router.router)

@app.get("/")
async def root(request: Request):
    return FileResponse(BASE_DIR / "templates" / "index.html")

@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "app": "Unit Kokurikulum Sekolah Kebangsaan Sungai Dendang",
        "school_code": "ABA6034",
        "version": "1.0.0"
    }
