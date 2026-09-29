from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth.token import verify_access_token
from app.database.database import get_db
from app.database.models import (
    User,
    CandidateProfile,
    Application,
    Resume,
    TalentPoolEntry,
    Job,
)
from app.services.career_fit import calculate_career_fit


router = APIRouter(
    prefix="/talent-pool",
    tags=["Talent Pool"],
)

security = HTTPBearer()


class TalentPoolAddRequest(BaseModel):
    candidate_id: int
    application_id: int | None = None
    notes: str | None = None


class TalentPoolNotesRequest(BaseModel):
    notes: str | None = None


def get_current_employer(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    payload = verify_access_token(credentials.credentials)

    if not payload:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
        )

    user_id = payload.get("sub")

    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Invalid token",
        )

    user = (
        db.query(User)
        .filter(User.id == int(user_id))
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=401,
            detail="User not found",
        )

    if user.role != "EMPLOYER_USER":
        raise HTTPException(
            status_code=403,
            detail="Employer access required",
        )

    return user


def build_talent_entry(
    entry: TalentPoolEntry,
    db: Session,
):
    candidate = entry.candidate

    user = (
        db.query(User)
        .filter(User.id == candidate.user_id)
        .first()
    )

    resume = (
        db.query(Resume)
        .filter(Resume.candidate_id == candidate.id)
        .order_by(Resume.created_at.desc())
        .first()
    )

    source_application = entry.source_application

    source_job = None

    if source_application:
        source_job = (
            db.query(Job)
            .filter(Job.id == source_application.job_id)
            .first()
        )

    match_score = None
    readiness = None
    matching_skills = []
    missing_skills = []

    if resume and source_job:
        try:
            fit = calculate_career_fit(
                resume_text=resume.extracted_text or "",
                job=source_job,
            )

            match_score = fit.get("score")
            readiness = fit.get("readiness")
            matching_skills = fit.get(
                "matching_skills",
                [],
            )
            missing_skills = fit.get(
                "missing_skills",
                [],
            )
        except Exception:
            pass

    return {
        "id": entry.id,
        "candidate_id": candidate.id,
        "candidate_name": user.name if user else "Unknown",
        "candidate_email": user.email if user else None,
        "candidate_location": candidate.location,
        "candidate_experience": candidate.experience,
        "candidate_education": candidate.education,
        "has_resume": resume is not None,
        "source_application_id": entry.source_application_id,
        "source_job": source_job.title if source_job else None,
        "match_score": match_score,
        "readiness": readiness,
        "matching_skills": matching_skills,
        "missing_skills": missing_skills,
        "notes": entry.notes,
        "added_at": entry.added_at,
    }


@router.get("/")
def get_talent_pool(
    employer=Depends(get_current_employer),
    db: Session = Depends(get_db),
):
    entries = (
        db.query(TalentPoolEntry)
        .filter(
            TalentPoolEntry.employer_user_id == employer.id
        )
        .order_by(TalentPoolEntry.added_at.desc())
        .all()
    )

    return {
        "count": len(entries),
        "talent": [
            build_talent_entry(entry, db)
            for entry in entries
        ],
    }


@router.post("/")
def add_to_talent_pool(
    data: TalentPoolAddRequest,
    employer=Depends(get_current_employer),
    db: Session = Depends(get_db),
):
    candidate = (
        db.query(CandidateProfile)
        .filter(
            CandidateProfile.id == data.candidate_id
        )
        .first()
    )

    if not candidate:
        raise HTTPException(
            status_code=404,
            detail="Candidate not found",
        )

    existing = (
        db.query(TalentPoolEntry)
        .filter(
            TalentPoolEntry.employer_user_id == employer.id,
            TalentPoolEntry.candidate_id == candidate.id,
        )
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Candidate is already in your talent pool.",
        )

    application = None

    if data.application_id:
        application = (
            db.query(Application)
            .filter(
                Application.id == data.application_id
            )
            .first()
        )

        if not application:
            raise HTTPException(
                status_code=404,
                detail="Application not found",
            )

        if application.candidate_id != candidate.id:
            raise HTTPException(
                status_code=400,
                detail="Application does not belong to this candidate.",
            )

    entry = TalentPoolEntry(
        employer_user_id=employer.id,
        candidate_id=candidate.id,
        source_application_id=(
            application.id if application else None
        ),
        notes=data.notes,
    )

    db.add(entry)
    db.commit()
    db.refresh(entry)

    return {
        "message": "Candidate added to talent pool.",
        "talent": build_talent_entry(entry, db),
    }


@router.patch("/{entry_id}")
def update_talent_pool_entry(
    entry_id: int,
    data: TalentPoolNotesRequest,
    employer=Depends(get_current_employer),
    db: Session = Depends(get_db),
):
    entry = (
        db.query(TalentPoolEntry)
        .filter(
            TalentPoolEntry.id == entry_id,
            TalentPoolEntry.employer_user_id == employer.id,
        )
        .first()
    )

    if not entry:
        raise HTTPException(
            status_code=404,
            detail="Talent pool entry not found",
        )

    if data.notes and len(data.notes) > 2000:
        raise HTTPException(
            status_code=400,
            detail="Notes cannot exceed 2000 characters.",
        )

    entry.notes = data.notes

    db.commit()
    db.refresh(entry)

    return {
        "message": "Talent pool entry updated.",
        "talent": build_talent_entry(entry, db),
    }


@router.delete("/{entry_id}")
def remove_from_talent_pool(
    entry_id: int,
    employer=Depends(get_current_employer),
    db: Session = Depends(get_db),
):
    entry = (
        db.query(TalentPoolEntry)
        .filter(
            TalentPoolEntry.id == entry_id,
            TalentPoolEntry.employer_user_id == employer.id,
        )
        .first()
    )

    if not entry:
        raise HTTPException(
            status_code=404,
            detail="Talent pool entry not found",
        )

    db.delete(entry)
    db.commit()

    return {
        "message": "Candidate removed from talent pool."
    }
