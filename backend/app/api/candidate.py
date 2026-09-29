from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.dependencies import require_candidate
from app.auth.security import hash_password
from app.database.database import get_db
from app.database.models import (
    EmployerUser,
    Application,
    ApplicationStatusHistory,
    CandidateProfile,
    Job,
    NotificationItem,
    Resume,
    User,
)
from app.schemas.candidate import (
    ApplicationCreate,
    CandidateProfileCreate,
    CandidateRegister,
)

router = APIRouter(
    prefix="/candidate",
    tags=["Candidate"],
)


@router.post("/register")
def register_candidate(
    data: CandidateRegister,
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

    user = User(
        name=data.name,
        email=data.email,
        password_hash=hash_password(data.password),
        role="JOB_SEEKER",
    )

    db.add(user)
    db.flush()

    candidate = CandidateProfile(
        user_id=user.id,
    )

    db.add(candidate)
    db.commit()
    db.refresh(candidate)

    return {
        "message": "Candidate registered successfully",
        "candidate_id": candidate.id,
    }


@router.get("/profile")
def get_candidate_profile(
    candidate_user: User = Depends(require_candidate),
    db: Session = Depends(get_db),
):
    candidate = (
        db.query(CandidateProfile)
        .filter(
            CandidateProfile.user_id == candidate_user.id
        )
        .first()
    )

    if not candidate:
        raise HTTPException(
            status_code=404,
            detail="Candidate profile not found",
        )

    return {
        "id": candidate.id,
        "name": candidate_user.name,
        "email": candidate_user.email,
        "phone": candidate.phone,
        "location": candidate.location,
        "bio": candidate.bio,
        "experience": candidate.experience,
        "education": candidate.education,
    }


@router.put("/profile")
def update_candidate_profile(
    data: CandidateProfileCreate,
    candidate_user: User = Depends(require_candidate),
    db: Session = Depends(get_db),
):
    candidate = (
        db.query(CandidateProfile)
        .filter(
            CandidateProfile.user_id == candidate_user.id
        )
        .first()
    )

    if not candidate:
        raise HTTPException(
            status_code=404,
            detail="Candidate profile not found",
        )

    if data.phone is not None:
        candidate.phone = data.phone

    if data.location is not None:
        candidate.location = data.location

    if data.bio is not None:
        candidate.bio = data.bio

    if data.experience is not None:
        candidate.experience = data.experience

    if data.education is not None:
        candidate.education = data.education

    db.commit()
    db.refresh(candidate)

    return {
        "message": "Candidate profile updated successfully",
        "profile": {
            "phone": candidate.phone,
            "location": candidate.location,
            "bio": candidate.bio,
            "experience": candidate.experience,
            "education": candidate.education,
        },
    }


@router.post("/apply")
def apply_for_job(
    data: ApplicationCreate,
    candidate_user: User = Depends(require_candidate),
    db: Session = Depends(get_db),
):
    candidate = (
        db.query(CandidateProfile)
        .filter(
            CandidateProfile.user_id == candidate_user.id
        )
        .first()
    )

    if not candidate:
        raise HTTPException(
            status_code=404,
            detail="Candidate profile not found",
        )

    job = (
        db.query(Job)
        .filter(Job.id == data.job_id)
        .first()
    )

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job not found",
        )

    if job.status != "ACTIVE":
        raise HTTPException(
            status_code=400,
            detail="This job is no longer accepting applications",
        )

    existing_application = (
        db.query(Application)
        .filter(
            Application.candidate_id == candidate.id,
            Application.job_id == job.id,
        )
        .first()
    )

    if existing_application:
        raise HTTPException(
            status_code=409,
            detail="You have already applied to this job",
        )

    resume = None

    if data.resume_id:
        resume = (
            db.query(Resume)
            .filter(
                Resume.id == data.resume_id,
                Resume.candidate_id == candidate.id,
            )
            .first()
        )

        if not resume:
            raise HTTPException(
                status_code=404,
                detail="Resume not found",
            )

    application = Application(
        candidate_id=candidate.id,
        job_id=job.id,
        resume_id=resume.id if resume else None,
        status="APPLIED",
    )

    db.add(application)
    db.flush()

    history = ApplicationStatusHistory(
        application_id=application.id,
        old_status=None,
        new_status="APPLIED",
        feedback="Application submitted successfully.",
        changed_by_user_id=candidate_user.id,
        changed_at=datetime.utcnow(),
    )

    db.add(history)

    employer_users = (
        db.query(User)
        .join(
            EmployerUser,
            EmployerUser.user_id == User.id,
        )
        .filter(
            User.role == "EMPLOYER_USER",
            EmployerUser.company_id == job.company_id,
        )
        .all()
    )

    for employer_user in employer_users:
        notification = NotificationItem(
            user_id=employer_user.id,
            application_id=application.id,
            title="New candidate application",
            message=(
                f"{candidate_user.name} applied for "
                f"{job.title}."
            ),
            notification_type="APPLICATION",
            is_read=False,
        )

        db.add(notification)

    db.commit()
    db.refresh(application)

    return {
        "message": "Application submitted successfully",
        "application_id": application.id,
        "job_id": job.id,
        "status": application.status,
    }


@router.get("/applications")
def get_candidate_applications(
    candidate_user: User = Depends(require_candidate),
    db: Session = Depends(get_db),
):
    candidate = (
        db.query(CandidateProfile)
        .filter(
            CandidateProfile.user_id == candidate_user.id
        )
        .first()
    )

    if not candidate:
        raise HTTPException(
            status_code=404,
            detail="Candidate profile not found",
        )

    applications = (
        db.query(Application)
        .filter(
            Application.candidate_id == candidate.id
        )
        .order_by(Application.applied_at.desc())
        .all()
    )

    result = []

    for application in applications:
        job = (
            db.query(Job)
            .filter(Job.id == application.job_id)
            .first()
        )

        history = []

        for item in application.status_history:
            changed_by = item.changed_by

            history.append(
                {
                    "id": item.id,
                    "old_status": item.old_status,
                    "new_status": item.new_status,
                    "feedback": item.feedback,
                    "changed_at": item.changed_at,
                    "changed_by": (
                        {
                            "id": changed_by.id,
                            "name": changed_by.name,
                            "role": changed_by.role,
                        }
                        if changed_by
                        else None
                    ),
                }
            )

        result.append(
            {
                "id": application.id,
                "job_id": application.job_id,
                "job_title": job.title if job else None,
                "company_name": (
                    job.company.name
                    if job and job.company
                    else None
                ),
                "location": (
                    job.location
                    if job
                    else None
                ),
                "status": application.status,
                "match_score": application.match_score,
                "applied_at": application.applied_at,
                "status_history": history,
            }
        )

    return result


@router.get("/jobs/{job_id}/fit")
def get_job_fit(
    job_id: int,
    candidate_user: User = Depends(require_candidate),
    db: Session = Depends(get_db),
):
    from app.services.career_fit import calculate_career_fit

    candidate = (
        db.query(CandidateProfile)
        .filter(CandidateProfile.user_id == candidate_user.id)
        .first()
    )

    if not candidate:
        raise HTTPException(
            status_code=404,
            detail="Candidate profile not found",
        )

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

    resume = (
        db.query(Resume)
        .filter(
            Resume.candidate_id == candidate.id,
            Resume.extracted_text.isnot(None),
        )
        .order_by(Resume.uploaded_at.desc())
        .first()
    )

    if not resume:
        raise HTTPException(
            status_code=404,
            detail="No processed resume found. Upload a resume first.",
        )

    required_skills = [
        skill.name
        for skill in job.skills
        if skill.name
    ]

    result = calculate_career_fit(
        resume_text=resume.extracted_text or "",
        job_title=job.title or "",
        job_description=job.description or "",
        required_skills=required_skills,
    )

    return {
        "job_id": job.id,
        "job_title": job.title,
        "resume_id": resume.id,
        "fit": result,
    }
