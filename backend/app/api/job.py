from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.database.models import (
    Job,
    Company,
    EmployerUser,
    Skill,
)
from app.schemas.job import JobCreate
from app.auth.token import verify_access_token

router = APIRouter(
    prefix="/jobs",
    tags=["Jobs"]
)

security = HTTPBearer()


def get_current_employer(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    token = credentials.credentials
    payload = verify_access_token(token)

    if not payload:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )

    user_id = payload.get("sub")
    role = payload.get("role")

    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication token"
        )

    if role != "EMPLOYER_USER":
        raise HTTPException(
            status_code=403,
            detail="Employer access required"
        )

    employer = (
        db.query(EmployerUser)
        .filter(
            EmployerUser.user_id == int(user_id)
        )
        .first()
    )

    if not employer:
        raise HTTPException(
            status_code=404,
            detail="Employer profile not found"
        )

    return employer


@router.post("/")
def create_job(
    job_data: JobCreate,
    employer: EmployerUser = Depends(get_current_employer),
    db: Session = Depends(get_db)
):
    company = (
        db.query(Company)
        .filter(
            Company.id == employer.company_id
        )
        .first()
    )

    if not company:
        raise HTTPException(
            status_code=404,
            detail="Company not found"
        )

    job = Job(
        company_id=company.id,
        employer_id=employer.id,
        title=job_data.title.strip(),
        description=job_data.description.strip(),
        location=job_data.location,
        salary=job_data.salary,
        experience=job_data.experience,
        employment_type=job_data.employment_type,
        status="ACTIVE",
    )

    db.add(job)
    db.flush()

    for skill_name in job_data.skills:
        skill_name = skill_name.strip()

        if not skill_name:
            continue

        skill = (
            db.query(Skill)
            .filter(
                Skill.name.ilike(skill_name)
            )
            .first()
        )

        if not skill:
            skill = Skill(name=skill_name)
            db.add(skill)
            db.flush()

        job.skills.append(skill)

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
    job = (
        db.query(Job)
        .filter(
            Job.id == job_id,
            Job.status == "ACTIVE"
        )
        .first()
    )

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


@router.put("/{job_id}")
def update_job(
    job_id: int,
    job_data: JobCreate,
    employer: EmployerUser = Depends(get_current_employer),
    db: Session = Depends(get_db)
):
    job = (
        db.query(Job)
        .filter(
            Job.id == job_id,
            Job.company_id == employer.company_id,
            Job.employer_id == employer.id
        )
        .first()
    )

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job not found or access denied"
        )

    job.title = job_data.title.strip()
    job.description = job_data.description.strip()
    job.location = job_data.location
    job.salary = job_data.salary
    job.experience = job_data.experience
    job.employment_type = job_data.employment_type

    job.skills.clear()

    for skill_name in job_data.skills:
        skill_name = skill_name.strip()

        if not skill_name:
            continue

        skill = (
            db.query(Skill)
            .filter(
                Skill.name.ilike(skill_name)
            )
            .first()
        )

        if not skill:
            skill = Skill(name=skill_name)
            db.add(skill)
            db.flush()

        job.skills.append(skill)

    db.commit()
    db.refresh(job)

    return {
        "message": "Job updated successfully",
        "job_id": job.id,
    }


@router.patch("/{job_id}/close")
def close_job(
    job_id: int,
    employer: EmployerUser = Depends(get_current_employer),
    db: Session = Depends(get_db)
):
    job = (
        db.query(Job)
        .filter(
            Job.id == job_id,
            Job.company_id == employer.company_id,
            Job.employer_id == employer.id
        )
        .first()
    )

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job not found or access denied"
        )

    job.status = "CLOSED"

    db.commit()

    return {
        "message": "Job closed successfully",
        "job_id": job.id,
    }
