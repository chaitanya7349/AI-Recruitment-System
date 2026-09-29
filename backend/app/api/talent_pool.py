from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth.dependencies import require_employer
from app.database.database import get_db
from app.database.models import (
    Application,
    CandidateProfile,
    Job,
    TalentPoolEntry,
    User,
)

router = APIRouter(
    prefix="/talent-pool",
    tags=["Talent Pool"],
)


class TalentPoolCreate(BaseModel):
    candidate_id: int
    application_id: int | None = None
    notes: str | None = None


class TalentPoolUpdate(BaseModel):
    notes: str | None = None


def build_talent_pool_response(
    entry: TalentPoolEntry,
    db: Session,
):
    candidate = entry.candidate

    if not candidate:
        return {
            "id": entry.id,
            "candidate_id": entry.candidate_id,
            "candidate_name": None,
            "candidate_email": None,
            "source_application_id": entry.source_application_id,
            "source_job": None,
            "notes": entry.notes,
            "added_at": entry.added_at,
        }

    user = (
        db.query(User)
        .filter(User.id == candidate.user_id)
        .first()
    )

    source_job = None
    match_score = None
    status = None

    if entry.source_application:
        application = entry.source_application

        status = application.status
        match_score = application.match_score

        source_job = (
            db.query(Job)
            .filter(Job.id == application.job_id)
            .first()
        )

    return {
        "id": entry.id,
        "candidate_id": candidate.id,
        "candidate_name": user.name if user else None,
        "candidate_email": user.email if user else None,
        "source_application_id": entry.source_application_id,
        "source_job": (
            {
                "id": source_job.id,
                "title": source_job.title,
                "company_id": source_job.company_id,
            }
            if source_job
            else None
        ),
        "match_score": match_score,
        "application_status": status,
        "notes": entry.notes,
        "added_at": entry.added_at,
    }


@router.get("/")
def get_talent_pool(
    employer: User = Depends(require_employer),
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

    return [
        build_talent_pool_response(entry, db)
        for entry in entries
    ]


@router.post("/")
def add_to_talent_pool(
    data: TalentPoolCreate,
    employer: User = Depends(require_employer),
    db: Session = Depends(get_db),
):
    candidate = (
        db.query(CandidateProfile)
        .filter(CandidateProfile.id == data.candidate_id)
        .first()
    )

    if not candidate:
        raise HTTPException(
            status_code=404,
            detail="Candidate not found",
        )

    source_application = None

    if data.application_id:
        source_application = (
            db.query(Application)
            .filter(
                Application.id == data.application_id
            )
            .first()
        )

        if not source_application:
            raise HTTPException(
                status_code=404,
                detail="Application not found",
            )

        job = (
            db.query(Job)
            .filter(Job.id == source_application.job_id)
            .first()
        )

        if not job or job.company_id != employer.employer_profile.company_id:
            raise HTTPException(
                status_code=403,
                detail="You can only add candidates from your company's applications",
            )

        if source_application.candidate_id != candidate.id:
            raise HTTPException(
                status_code=400,
                detail="Application does not belong to the selected candidate",
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
            status_code=409,
            detail="Candidate is already in your talent pool",
        )

    entry = TalentPoolEntry(
        employer_user_id=employer.id,
        candidate_id=candidate.id,
        source_application_id=data.application_id,
        notes=data.notes,
    )

    db.add(entry)
    db.commit()
    db.refresh(entry)

    return {
        "message": "Candidate added to talent pool",
        **build_talent_pool_response(entry, db),
    }


@router.patch("/{entry_id}")
def update_talent_pool_entry(
    entry_id: int,
    data: TalentPoolUpdate,
    employer: User = Depends(require_employer),
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

    entry.notes = data.notes

    db.commit()
    db.refresh(entry)

    return {
        "message": "Talent pool entry updated",
        **build_talent_pool_response(entry, db),
    }


@router.delete("/{entry_id}")
def delete_talent_pool_entry(
    entry_id: int,
    employer: User = Depends(require_employer),
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
        "message": "Candidate removed from talent pool"
    }
