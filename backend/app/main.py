from app.api.career_fit import router as career_fit_router
from app.api.job_quality import router as job_quality_router
from app.api.talent_pool import router as talent_pool_router
from app.api.notifications import router as notifications_router
from app.api.admin import router as admin_router
from app.api.candidate import router as candidate_router
from fastapi import FastAPI
from app.database.database import engine
from app.database.models import Base
from app.api.resume import router as resume_router
import app.database.models
from app.api.job import router as job_router
from fastapi.middleware.cors import CORSMiddleware
from app.api.login import router as login_router
from app.api.employer import router as employer_router
Base.metadata.create_all(bind=engine)
app = FastAPI(
    title="AI Recruitment System",
    description="MCA Final Year Project by Chaitanya",
    version="1.0.0"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
    "http://localhost:5173",
    "http://localhost:5174",
],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(career_fit_router)
app.include_router(job_quality_router)
app.include_router(talent_pool_router)
app.include_router(notifications_router)
app.include_router(admin_router)
app.include_router(candidate_router)
app.include_router(resume_router)
app.include_router(job_router)
app.include_router(login_router)
app.include_router(employer_router)
Base.metadata.create_all(bind=engine)

@app.get("/")
def home():
    return {
        "project": "AI Recruitment System",
        "developer": "Chaitanya",
        "message": "Backend is running successfully!"
    }
