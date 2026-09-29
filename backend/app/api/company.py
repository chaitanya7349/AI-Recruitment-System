from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.database.models import Company, Job


router = APIRouter(
    prefix="/companies",
    tags=["Companies"],
)


@router.get("/")
def get_companies(
    db: Session = Depends(get_db),
):
    companies = (
        db.query(Company)
        .order_by(Company.name.asc())
        .all()
    )

    result = []

    for company in companies:
        active_jobs = (
            db.query(Job)
            .filter(
                Job.company_id == company.id,
                Job.status == "ACTIVE",
            )
            .count()
        )

        result.append(
            {
                "id": company.id,
                "name": company.name,
                "description": company.description,
                "website": company.website,
                "location": company.location,
                "active_jobs": active_jobs,
            }
        )

    return result


@router.get("/{company_id}")
def get_company(
    company_id: int,
    db: Session = Depends(get_db),
):
    company = (
        db.query(Company)
        .filter(Company.id == company_id)
        .first()
    )

    if not company:
        raise HTTPException(
            status_code=404,
            detail="Company not found",
        )

    jobs = (
        db.query(Job)
        .filter(
            Job.company_id == company.id,
            Job.status == "ACTIVE",
        )
        .order_by(Job.created_at.desc())
        .all()
    )

    return {
        "id": company.id,
        "name": company.name,
        "description": company.description,
        "website": company.website,
        "location": company.location,
        "active_jobs": len(jobs),
        "jobs": [
            {
                "id": job.id,
                "title": job.title,
                "location": job.location,
                "salary": job.salary,
                "experience": job.experience,
                "employment_type": job.employment_type,
                "created_at": job.created_at,
            }
            for job in jobs
        ],
    }
