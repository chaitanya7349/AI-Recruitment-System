from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.dependencies import require_employer
from app.database.database import get_db
from app.database.models import Company, EmployerUser, Job, Skill, User
from app.schemas.job import JobCreate, JobResponse


router = APIRouter(
    prefix="/jobs",
    tags=["Jobs"],
)


def get_or_create_skills(
    db: Session,
    skill_names: list[str],
) -> list[Skill]:
    """
    Convert skill names from the API request into Skill database objects.

    Existing skills are reused.
    New skills are created when necessary.
    """

    skills = []

    for skill_name in skill_names or []:
        name = skill_name.strip()

        if not name:
            continue

        skill = (
            db.query(Skill)
            .filter(Skill.name.ilike(name))
            .first()
        )

        if not skill:
            skill = Skill(name=name)
            db.add(skill)
            db.flush()

        skills.append(skill)

    return skills


def build_job_response(job: Job):
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
        "company_name": (
            job.company.name
            if job.company
            else None
        ),
        "skills": [
            skill.name
            for skill in job.skills
        ],
    }


@router.get("/")
def get_jobs(
    db: Session = Depends(get_db),
):
    jobs = (
        db.query(Job)
        .filter(Job.status == "ACTIVE")
        .order_by(Job.created_at.desc())
        .all()
    )

    return [
        build_job_response(job)
        for job in jobs
    ]


@router.get("/{job_id}")
def get_job(
    job_id: int,
    db: Session = Depends(get_db),
):
    job = (
        db.query(Job)
        .filter(Job.id == job_id)
        .first()
    )

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job not found",
        )

    return build_job_response(job)


@router.post("/")
def create_job(
    data: JobCreate,
    employer: User = Depends(require_employer),
    db: Session = Depends(get_db),
):
    employer_profile = employer.employer_profile

    if not employer_profile:
        raise HTTPException(
            status_code=400,
            detail="Employer profile not found",
        )

    if not employer_profile.company_id:
        raise HTTPException(
            status_code=400,
            detail="Employer is not associated with a company",
        )

    company = (
        db.query(Company)
        .filter(
            Company.id == employer_profile.company_id
        )
        .first()
    )

    if not company:
        raise HTTPException(
            status_code=404,
            detail="Company not found",
        )

    job_skills = get_or_create_skills(
        db,
        data.skills,
    )

    job = Job(
        company_id=company.id,
        employer_id=employer_profile.id,
        title=data.title,
        description=data.description,
        location=data.location,
        salary=data.salary,
        experience=data.experience,
        employment_type=data.employment_type,
        status="ACTIVE",
        skills=job_skills,
    )

    db.add(job)
    db.commit()
    db.refresh(job)

    return build_job_response(job)


@router.put("/{job_id}")
def update_job(
    job_id: int,
    data: JobCreate,
    employer: User = Depends(require_employer),
    db: Session = Depends(get_db),
):
    job = (
        db.query(Job)
        .filter(Job.id == job_id)
        .first()
    )

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job not found",
        )

    if job.company_id != employer.employer_profile.company_id:
        raise HTTPException(
            status_code=403,
            detail="You can only update your company's jobs",
        )

    job.title = data.title
    job.description = data.description
    job.location = data.location
    job.salary = data.salary
    job.experience = data.experience
    job.employment_type = data.employment_type

    job.skills = get_or_create_skills(
        db,
        data.skills,
    )

    db.commit()
    db.refresh(job)

    return build_job_response(job)


@router.patch("/{job_id}/close")
def close_job(
    job_id: int,
    employer: User = Depends(require_employer),
    db: Session = Depends(get_db),
):
    job = (
        db.query(Job)
        .filter(Job.id == job_id)
        .first()
    )

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job not found",
        )

    if job.company_id != employer.employer_profile.company_id:
        raise HTTPException(
            status_code=403,
            detail="You can only close your company's jobs",
        )

    job.status = "CLOSED"

    db.commit()
    db.refresh(job)

    return {
        "message": "Job closed successfully",
        "job_id": job.id,
        "status": job.status,
    }
