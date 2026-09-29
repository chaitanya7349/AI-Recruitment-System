from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.database.models import (
    User,
    CandidateProfile,
    Job,
    Resume,
    Application,
    ApplicationStatusHistory,
    NotificationItem,
)

from app.schemas.candidate import (
    CandidateRegister,
    CandidateProfileCreate,
    ApplicationCreate,
)

from app.auth.security import hash_password
from app.auth.token import verify_access_token


router = APIRouter(
    prefix="/candidate",
    tags=["Candidate"],
)

security = HTTPBearer()


# ============================================================
# GET CURRENT CANDIDATE
# ============================================================

def get_current_candidate(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    payload = verify_access_token(
        credentials.credentials
    )

    if not payload:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
        )

    user_id = payload.get("sub")
    role = payload.get("role")

    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication token",
        )

    if role != "JOB_SEEKER":
        raise HTTPException(
            status_code=403,
            detail="Candidate access required",
        )

    candidate = (
        db.query(CandidateProfile)
        .filter(
            CandidateProfile.user_id == int(user_id)
        )
        .first()
    )

    if not candidate:
        raise HTTPException(
            status_code=404,
            detail="Candidate profile not found",
        )

    return candidate


# ============================================================
# CANDIDATE REGISTRATION
# ============================================================

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
        user_id=user.id
    )

    db.add(candidate)
    db.commit()
    db.refresh(candidate)

    return {
        "message": "Candidate registered successfully",
        "user_id": user.id,
        "candidate_id": candidate.id,
    }


# ============================================================
# GET PROFILE
# ============================================================

@router.get("/profile")
def get_profile(
    candidate: CandidateProfile = Depends(
        get_current_candidate
    ),
    db: Session = Depends(get_db),
):
    user = (
        db.query(User)
        .filter(
            User.id == candidate.user_id
        )
        .first()
    )

    return {
        "id": candidate.id,
        "name": user.name if user else "",
        "email": user.email if user else "",
        "phone": candidate.phone,
        "location": candidate.location,
        "bio": candidate.bio,
        "experience": candidate.experience,
        "education": candidate.education,
    }


# ============================================================
# UPDATE PROFILE
# ============================================================

@router.put("/profile")
def update_profile(
    data: CandidateProfileCreate,
    candidate: CandidateProfile = Depends(
        get_current_candidate
    ),
    db: Session = Depends(get_db),
):
    candidate.phone = data.phone
    candidate.location = data.location
    candidate.bio = data.bio
    candidate.experience = data.experience
    candidate.education = data.education

    db.commit()

    return {
        "message": "Candidate profile updated successfully"
    }


# ============================================================
# APPLY FOR JOB
# ============================================================

@router.post("/apply")
def apply_for_job(
    data: ApplicationCreate,
    candidate: CandidateProfile = Depends(
        get_current_candidate
    ),
    db: Session = Depends(get_db),
):
    job = (
        db.query(Job)
        .filter(
            Job.id == data.job_id,
            Job.status == "ACTIVE",
        )
        .first()
    )

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job not found or no longer active",
        )

    existing_application = (
        db.query(Application)
        .filter(
            Application.job_id == data.job_id,
            Application.candidate_id == candidate.id,
        )
        .first()
    )

    if existing_application:
        raise HTTPException(
            status_code=400,
            detail="You have already applied for this job",
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
        job_id=job.id,
        candidate_id=candidate.id,
        resume_id=resume.id if resume else None,
        status="APPLIED",
    )

    db.add(application)
    db.flush()

    # Notify employer users belonging to the job's company.
    employer_users = (
        db.query(User)
        .filter(
            User.role == "EMPLOYER_USER",
            User.company_id == job.company_id,
        )
        .all()
    )

    for employer_user in employer_users:
        db.add(
            NotificationItem(
                user_id=employer_user.id,
                application_id=application.id,
                title="New candidate application",
                message=(
                    f"{candidate_user.name} applied for "
                    f"{job.title}."
                ),
                notification_type="APPLICATION",
            )
        )

    # --------------------------------------------------------
    # FIRST APPLICATION HISTORY EVENT
    # --------------------------------------------------------

    history = ApplicationStatusHistory(
        application_id=application.id,
        old_status=None,
        new_status="APPLIED",
        feedback="Application submitted successfully.",
        changed_by_user_id=candidate.user_id,
    )

    db.add(history)

    db.commit()
    db.refresh(application)

    return {
        "message": "Application submitted successfully",
        "application_id": application.id,
        "job_id": job.id,
        "job_title": job.title,
        "status": application.status,
    }


# ============================================================
# GET MY APPLICATIONS
# ============================================================

@router.get("/applications")
def get_my_applications(
    candidate: CandidateProfile = Depends(
        get_current_candidate
    ),
    db: Session = Depends(get_db),
):
    applications = (
        db.query(Application)
        .filter(
            Application.candidate_id == candidate.id
        )
        .order_by(
            Application.applied_at.desc()
        )
        .all()
    )

    results = []

    for application in applications:

        history = (
            db.query(ApplicationStatusHistory)
            .filter(
                ApplicationStatusHistory.application_id
                == application.id
            )
            .order_by(
                ApplicationStatusHistory.changed_at.asc()
            )
            .all()
        )

        history_items = []

        for event in history:
            history_items.append(
                {
                    "id": event.id,
                    "old_status": event.old_status,
                    "new_status": event.new_status,
                    "feedback": event.feedback,
                    "changed_at": event.changed_at,
                    "changed_by": (
                        event.changed_by.name
                        if event.changed_by
                        else None
                    ),
                }
            )

        results.append(
            {
                "id": application.id,
                "job_id": application.job_id,
                "job_title": application.job.title,
                "company_name": application.job.company.name,
                "location": application.job.location,
                "status": application.status,
                "match_score": application.match_score,
                "applied_at": application.applied_at,
                "status_history": history_items,
            }
        )

    return {
        "total": len(results),
        "applications": results,
    }
