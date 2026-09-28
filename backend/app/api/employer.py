from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.database.models import (
    User,
    Company,
    EmployerUser,
    Job,
)
from app.schemas.employer import EmployerRegister
from app.auth.security import hash_password
from app.auth.token import verify_access_token


router = APIRouter(
    prefix="/employer",
    tags=["Employer"]
)

security = HTTPBearer()


@router.post("/register")
def register_employer(
    data: EmployerRegister,
    db: Session = Depends(get_db)
):
    existing_user = db.query(User).filter(
        User.email == data.email
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    company = Company(
        name=data.company_name,
        description=data.company_description,
        website=data.company_website,
        location=data.company_location,
    )

    db.add(company)
    db.flush()

    user = User(
        name=data.name,
        email=data.email,
        password_hash=hash_password(data.password),
        role="EMPLOYER_USER",
    )

    db.add(user)
    db.flush()

    employer = EmployerUser(
        user_id=user.id,
        company_id=company.id,
        designation=data.designation,
        role_in_company=data.role_in_company,
    )

    db.add(employer)

    db.commit()

    return {
        "message": "Employer registered successfully",
        "user_id": user.id,
        "company_id": company.id,
        "employer_id": employer.id,
    }


@router.get("/dashboard")
def employer_dashboard(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    Return dashboard information for the currently
    authenticated employer.
    """

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

    employer = db.query(EmployerUser).filter(
        EmployerUser.user_id == int(user_id)
    ).first()

    if not employer:
        raise HTTPException(
            status_code=404,
            detail="Employer profile not found"
        )

    user = db.query(User).filter(
        User.id == employer.user_id
    ).first()

    company = db.query(Company).filter(
        Company.id == employer.company_id
    ).first()

    if not user or not company:
        raise HTTPException(
            status_code=404,
            detail="Employer or company not found"
        )

    jobs = db.query(Job).filter(
        Job.company_id == company.id
    ).order_by(
        Job.created_at.desc()
    ).all()

    active_jobs = [
        job for job in jobs
        if job.status == "ACTIVE"
    ]

    total_applications = sum(
        len(job.applications)
        for job in jobs
    )

    return {
        "employer": {
            "id": employer.id,
            "name": user.name,
            "email": user.email,
            "designation": employer.designation,
            "role_in_company": employer.role_in_company,
        },

        "company": {
            "id": company.id,
            "name": company.name,
            "description": company.description,
            "website": company.website,
            "location": company.location,
        },

        "statistics": {
            "total_jobs": len(jobs),
            "active_jobs": len(active_jobs),
            "total_applications": total_applications,
        },

        "jobs": [
            {
                "id": job.id,
                "title": job.title,
                "location": job.location,
                "salary": job.salary,
                "experience": job.experience,
                "employment_type": job.employment_type,
                "status": job.status,
                "created_at": job.created_at,
                "applications": len(job.applications),
                "skills": [
                    skill.name
                    for skill in job.skills
                ],
            }
            for job in jobs
        ],
    }
