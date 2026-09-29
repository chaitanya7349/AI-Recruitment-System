from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.auth.dependencies import require_employer
from app.auth.security import hash_password
from app.database.database import get_db
from app.database.models import (
    Application,
    ApplicationStatusHistory,
    CandidateProfile,
    Company,
    Job,
    NotificationItem,
    Resume,
    User,
    EmployerUser,
)
from app.services.career_fit import calculate_career_fit

router = APIRouter(
    prefix="/employer",
    tags=["Employer"],
)


class EmployerRegister(BaseModel):
    name: str
    email: EmailStr
    password: str
    company_name: str
    company_description: str | None = None
    company_website: str | None = None
    company_location: str | None = None
    designation: str | None = None
    role_in_company: str = "HR"


class ApplicationStatusUpdate(BaseModel):
    status: str
    feedback: str | None = None


ALLOWED_APPLICATION_STATUSES = {
    "APPLIED",
    "SCREENING",
    "SHORTLISTED",
    "INTERVIEW",
    "OFFER",
    "HIRED",
    "REJECTED",
}


def build_status_history(application):
    return [
        {
            "id": item.id,
            "old_status": item.old_status,
            "new_status": item.new_status,
            "feedback": item.feedback,
            "changed_at": item.changed_at,
            "changed_by": (
                {
                    "id": item.changed_by.id,
                    "name": item.changed_by.name,
                    "role": item.changed_by.role,
                }
                if item.changed_by
                else None
            ),
        }
        for item in application.status_history
    ]


def build_candidate_intelligence(
    application,
    job,
    candidate,
    resume,
):
    resume_text = resume.extracted_text if resume else ""

    required_skills = [
        skill.name
        for skill in job.skills
        if skill.name
    ]

    result = calculate_career_fit(
        resume_text=resume_text or "",
        job_title=job.title or "",
        job_description=job.description or "",
        required_skills=required_skills,
    )

    application.match_score = result["score"]

    return {
        "career_fit_score": result["score"],
        "readiness": result["readiness"],
        "matching_skills": result["matching_skills"],
        "missing_skills": result["missing_skills"],
        "recommendations": result["recommendations"],
        "has_resume": resume is not None,
        "explanation": (
            f"Candidate matches "
            f"{len(result['matching_skills'])} required skills "
            f"and is missing "
            f"{len(result['missing_skills'])} skills."
        ),
    }


@router.post("/register")
def register_employer(
    data: EmployerRegister,
    db: Session = Depends(get_db),
):
    existing_user = (
        db.query(User)
        .filter(User.email == data.email)
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered",
        )

    company = (
        db.query(Company)
        .filter(Company.name == data.company_name)
        .first()
    )

    if not company:
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

    employer_profile = EmployerUser(
        user_id=user.id,
        company_id=company.id,
        designation=data.designation,
        role_in_company=data.role_in_company,
    )

    db.add(employer_profile)
    db.commit()
    db.refresh(user)
    db.refresh(employer_profile)

    return {
        "message": "Employer registered successfully",
        "user_id": user.id,
        "company_id": company.id,
        "employer_profile_id": employer_profile.id,
    }


@router.get("/dashboard")
def employer_dashboard(
    employer: User = Depends(require_employer),
    db: Session = Depends(get_db),
):
    company = (
        db.query(Company)
        .filter(Company.id == employer.employer_profile.company_id)
        .first()
    )

    if not company:
        raise HTTPException(
            status_code=404,
            detail="Company not found",
        )

    jobs = (
        db.query(Job)
        .filter(Job.company_id == company.id)
        .order_by(Job.created_at.desc())
        .all()
    )

    total_applications = (
        db.query(Application)
        .join(Job, Application.job_id == Job.id)
        .filter(Job.company_id == company.id)
        .count()
    )

    active_jobs = sum(
        1 for job in jobs if job.status == "ACTIVE"
    )

    job_data = []

    for job in jobs:
        application_count = (
            db.query(Application)
            .filter(Application.job_id == job.id)
            .count()
        )

        job_data.append({
            "id": job.id,
            "title": job.title,
            "status": job.status,
            "created_at": job.created_at,
            "applications": application_count,
        })

    return {
        "employer": {
            "id": employer.id,
            "name": employer.name,
            "email": employer.email,
            "company_id": company.id,
            "designation": employer.employer_profile.designation,
            "role_in_company": employer.employer_profile.role_in_company,
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
            "active_jobs": active_jobs,
            "total_applications": total_applications,
        },
        "jobs": job_data,
    }


@router.get("/applications")
def get_employer_applications(
    employer: User = Depends(require_employer),
    db: Session = Depends(get_db),
):
    applications = (
        db.query(Application)
        .join(Job, Application.job_id == Job.id)
        .filter(Job.company_id == employer.employer_profile.company_id)
        .order_by(Application.applied_at.desc())
        .all()
    )

    result = []

    for application in applications:
        candidate = application.candidate

        candidate_user = (
            db.query(User)
            .filter(User.id == candidate.user_id)
            .first()
        )

        job = application.job

        resume = None

        if application.resume_id:
            resume = (
                db.query(Resume)
                .filter(Resume.id == application.resume_id)
                .first()
            )

        intelligence = build_candidate_intelligence(
            application=application,
            job=job,
            candidate=candidate,
            resume=resume,
        )

        result.append(
            {
                "application_id": application.id,
                "job_id": job.id,
                "job_title": job.title,
                "candidate_id": candidate.id,
                "candidate_name": (
                    candidate_user.name
                    if candidate_user
                    else None
                ),
                "candidate_email": (
                    candidate_user.email
                    if candidate_user
                    else None
                ),
                "resume": (
                    {
                        "id": resume.id,
                        "original_filename": resume.original_filename,
                        "stored_filename": resume.stored_filename,
                        "status": resume.status,
                    }
                    if resume
                    else None
                ),
                "match_score": intelligence["career_fit_score"],
                "readiness": intelligence["readiness"],
                "matching_skills": intelligence["matching_skills"],
                "missing_skills": intelligence["missing_skills"],
                "recommendations": intelligence["recommendations"],
                "status": application.status,
                "applied_at": application.applied_at,
                "status_history": build_status_history(
                    application
                ),
            }
        )

    db.commit()

    return result


@router.get("/applications/{application_id}")
def get_employer_application(
    application_id: int,
    employer: User = Depends(require_employer),
    db: Session = Depends(get_db),
):
    application = (
        db.query(Application)
        .filter(Application.id == application_id)
        .first()
    )

    if not application:
        raise HTTPException(
            status_code=404,
            detail="Application not found",
        )

    job = application.job

    if not job or job.company_id != employer.employer_profile.company_id:
        raise HTTPException(
            status_code=403,
            detail="You do not have access to this application",
        )

    candidate = application.candidate

    candidate_user = (
        db.query(User)
        .filter(User.id == candidate.user_id)
        .first()
    )

    resume = None

    if application.resume_id:
        resume = (
            db.query(Resume)
            .filter(Resume.id == application.resume_id)
            .first()
        )

    intelligence = build_candidate_intelligence(
        application=application,
        job=job,
        candidate=candidate,
        resume=resume,
    )

    db.commit()

    return {
        "application_id": application.id,
        "job": {
            "id": job.id,
            "title": job.title,
            "description": job.description,
            "skills": job.skills,
            "location": job.location,
            "experience": job.experience,
            "employment_type": job.employment_type,
        },
        "candidate": {
            "id": candidate.id,
            "name": (
                candidate_user.name
                if candidate_user
                else None
            ),
            "email": (
                candidate_user.email
                if candidate_user
                else None
            ),
            "phone": candidate.phone,
            "location": candidate.location,
            "experience": candidate.experience,
            "education": candidate.education,
            "bio": candidate.bio,
        },
        "resume": (
            {
                "id": resume.id,
                "original_filename": resume.original_filename,
                        "stored_filename": resume.stored_filename,
                "status": resume.status,
            }
            if resume
            else None
        ),
        "intelligence": intelligence,
        "status": application.status,
        "applied_at": application.applied_at,
        "status_history": build_status_history(
            application
        ),
    }


@router.patch("/applications/{application_id}/status")
def update_application_status(
    application_id: int,
    data: ApplicationStatusUpdate,
    employer: User = Depends(require_employer),
    db: Session = Depends(get_db),
):
    new_status = data.status.upper().strip()

    if new_status not in ALLOWED_APPLICATION_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid status. Allowed statuses: "
                + ", ".join(sorted(ALLOWED_APPLICATION_STATUSES))
            ),
        )

    if data.feedback and len(data.feedback) > 2000:
        raise HTTPException(
            status_code=400,
            detail="Feedback cannot exceed 2000 characters",
        )

    application = (
        db.query(Application)
        .filter(Application.id == application_id)
        .first()
    )

    if not application:
        raise HTTPException(
            status_code=404,
            detail="Application not found",
        )

    job = application.job

    if not job or job.company_id != employer.employer_profile.company_id:
        raise HTTPException(
            status_code=403,
            detail="You do not have access to this application",
        )

    old_status = application.status

    if old_status == new_status and not data.feedback:
        return {
            "message": "Application status is already set",
            "status": application.status,
        }

    application.status = new_status

    history = ApplicationStatusHistory(
        application_id=application.id,
        old_status=old_status,
        new_status=new_status,
        feedback=data.feedback,
        changed_by_user_id=employer.id,
        changed_at=datetime.utcnow(),
    )

    db.add(history)

    candidate = application.candidate

    if candidate:
        notification = NotificationItem(
            user_id=candidate.user_id,
            application_id=application.id,
            title="Application status updated",
            message=(
                f"Your application for {job.title} "
                f"moved from "
                f"{old_status or 'NEW'} to {new_status}."
            ),
            notification_type="STATUS_CHANGE",
            is_read=False,
        )

        db.add(notification)

    db.commit()
    db.refresh(application)

    return {
        "message": "Application status updated successfully",
        "application_id": application.id,
        "old_status": old_status,
        "new_status": new_status,
        "feedback": data.feedback,
    }


@router.get("/candidates")
def get_candidates(
    employer=Depends(require_employer),
    db: Session = Depends(get_db),
):
    employer_profile = employer.employer_profile

    if not employer_profile:
        raise HTTPException(
            status_code=400,
            detail="Employer profile not found",
        )

    company_id = employer_profile.company_id

    candidates = (
        db.query(CandidateProfile)
        .join(Application, Application.candidate_id == CandidateProfile.id)
        .join(Job, Application.job_id == Job.id)
        .filter(Job.company_id == company_id)
        .distinct()
        .all()
    )

    result = []

    for candidate in candidates:
        candidate_user = db.query(User).filter(
            User.id == candidate.user_id
        ).first()

        resume = (
            db.query(Resume)
            .filter(
                Resume.candidate_id == candidate.id,
                Resume.extracted_text.isnot(None),
            )
            .order_by(Resume.uploaded_at.desc())
            .first()
        )

        parsed = {
            "name": candidate_user.name if candidate_user else "",
            "email": candidate_user.email if candidate_user else "",
            "phone": candidate.phone or "",
            "skills": [],
        }

        score = 0

        if resume:
            from app.services.ai_parser import parse_resume
            from app.services.resume_score import calculate_score

            parsed = parse_resume(resume.extracted_text)

            if not parsed.get("name") and candidate_user:
                parsed["name"] = candidate_user.name

            if not parsed.get("email") and candidate_user:
                parsed["email"] = candidate_user.email

            if not parsed.get("phone"):
                parsed["phone"] = candidate.phone or ""

            score = calculate_score(parsed)

        result.append({
            "candidate_id": candidate.id,
            "resume_id": resume.id if resume else None,
            "name": parsed.get("name", ""),
            "email": parsed.get("email", ""),
            "phone": parsed.get("phone", ""),
            "score": score,
            "skills": parsed.get("skills", []),
        })

    return {"candidates": result}




@router.get("/candidates/{resume_id}")
def get_candidate_details(
    resume_id: int,
    employer=Depends(require_employer),
    db: Session = Depends(get_db),
):
    employer_profile = employer.employer_profile

    if not employer_profile:
        raise HTTPException(
            status_code=400,
            detail="Employer profile not found",
        )

    company_id = employer_profile.company_id

    resume = (
        db.query(Resume)
        .join(Application, Resume.candidate_id == Application.candidate_id)
        .join(Job, Application.job_id == Job.id)
        .filter(
            Resume.id == resume_id,
            Job.company_id == company_id,
        )
        .first()
    )

    if not resume:
        raise HTTPException(
            status_code=404,
            detail="Candidate resume not found",
        )

    candidate = (
        db.query(CandidateProfile)
        .filter(CandidateProfile.id == resume.candidate_id)
        .first()
    )

    if not candidate:
        raise HTTPException(
            status_code=404,
            detail="Candidate not found",
        )

    user = (
        db.query(User)
        .filter(User.id == candidate.user_id)
        .first()
    )

    from app.services.ai_parser import parse_resume
    from app.services.resume_score import calculate_score

    parsed = parse_resume(resume.extracted_text or "")
    score = calculate_score(parsed)

    applications = (
        db.query(Application)
        .join(Job, Application.job_id == Job.id)
        .filter(
            Application.candidate_id == candidate.id,
            Job.company_id == company_id,
        )
        .all()
    )

    return {
        "candidate_id": candidate.id,
        "resume_id": resume.id,
        "name": parsed.get("name") or (user.name if user else ""),
        "email": parsed.get("email") or (user.email if user else ""),
        "phone": parsed.get("phone") or candidate.phone or "",
        "skills": parsed.get("skills", []),
        "education": parsed.get("education", ""),
        "experience": parsed.get("experience", ""),
        "score": score,
        "resume_status": resume.status,
        "uploaded_at": resume.uploaded_at,
        "applications": [
            {
                "application_id": application.id,
                "job_id": application.job_id,
                "job_title": application.job.title,
                "status": application.status,
                "match_score": application.match_score,
                "applied_at": application.applied_at,
            }
            for application in applications
        ],
    }


@router.post("/rank-candidates")
def rank_candidates_api(
    data: dict,
    employer=Depends(require_employer),
    db: Session = Depends(get_db),
):
    employer_profile = employer.employer_profile

    if not employer_profile:
        raise HTTPException(
            status_code=400,
            detail="Employer profile not found",
        )

    skills = data.get("skills", [])

    if not isinstance(skills, list):
        raise HTTPException(
            status_code=400,
            detail="skills must be a list",
        )

    company_id = employer_profile.company_id

    resumes = (
        db.query(Resume)
        .join(Application, Resume.candidate_id == Application.candidate_id)
        .join(Job, Application.job_id == Job.id)
        .filter(
            Job.company_id == company_id,
            Resume.extracted_text.isnot(None),
        )
        .distinct()
        .all()
    )

    from app.services.ranking import rank_candidates

    ranking = rank_candidates(
        resumes=resumes,
        job_skills=skills,
    )

    return {"ranking": ranking}
