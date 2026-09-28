from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.database.models import Job, Company, EmployerUser, Skill
from app.schemas.job import JobCreate

router = APIRouter(
    prefix="/jobs",
    tags=["Jobs"]
)


@router.post("/")
def create_job(
    job_data: JobCreate,
    db: Session = Depends(get_db)
):
    # Temporary employer/company IDs for development.
    # Authentication will replace these later.
    employer = db.query(EmployerUser).first()

    if not employer:
        raise HTTPException(
            status_code=400,
            detail="No employer exists. Create an employer first."
        )

    company = db.query(Company).filter(
        Company.id == employer.company_id
    ).first()

    if not company:
        raise HTTPException(
            status_code=400,
            detail="Employer company not found."
        )

    job = Job(
        company_id=company.id,
        employer_id=employer.id,
        title=job_data.title,
        description=job_data.description,
        location=job_data.location,
        salary=job_data.salary,
        experience=job_data.experience,
        employment_type=job_data.employment_type,
        status="ACTIVE",
    )

    # Create/reuse skills
    for skill_name in job_data.skills:

        skill_name = skill_name.strip()

        if not skill_name:
            continue

        skill = db.query(Skill).filter(
            Skill.name.ilike(skill_name)
        ).first()

        if not skill:
            skill = Skill(name=skill_name)
            db.add(skill)
            db.flush()

        job.skills.append(skill)

    db.add(job)
    db.commit()
    db.refresh(job)

    return {
        "message": "Job created successfully",
        "job_id": job.id,
        "title": job.title,
    }


@router.get("/")
def get_jobs(
    db: Session = Depends(get_db)
):
    jobs = (
        db.query(Job)
        .filter(Job.status == "ACTIVE")
        .order_by(Job.created_at.desc())
        .all()
    )

    return {
        "total": len(jobs),
        "jobs": [
            {
                "id": job.id,
                "title": job.title,
                "description": job.description,
                "location": job.location,
                "salary": job.salary,
                "experience": job.experience,
                "employment_type": job.employment_type,
                "status": job.status,
                "created_at": job.created_at,
                "company_name": job.company.name,
                "skills": [
                    skill.name
                    for skill in job.skills
                ],
            }
            for job in jobs
        ],
    }


@router.get("/{job_id}")
def get_job(
    job_id: int,
    db: Session = Depends(get_db)
):
    job = db.query(Job).filter(
        Job.id == job_id,
        Job.status == "ACTIVE"
    ).first()

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job not found"
        )

    return {
        "id": job.id,
        "title": job.title,
        "description": job.description,
        "location": job.location,
        "salary": job.salary,
        "experience": job.experience,
        "employment_type": job.employment_type,
        "status": job.status,
        "created_at": job.created_at,
        "company_name": job.company.name,
        "skills": [
            skill.name
            for skill in job.skills
        ],
    }
