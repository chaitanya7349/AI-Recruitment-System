from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.database.models import (
    User,
    Company,
    EmployerUser,
    Job,
    Application,
    CandidateProfile,
    Resume,
    ApplicationStatusHistory,
    NotificationItem,
)

from app.auth.token import verify_access_token
from app.auth.security import hash_password
from app.services.career_fit import calculate_career_fit


router = APIRouter(
    prefix="/employer",
    tags=["Employer"],
)

security = HTTPBearer()


# ============================================================
# GET CURRENT EMPLOYER
# ============================================================

def get_current_employer(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    token = credentials.credentials

    payload = verify_access_token(token)

    if not payload:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
        )

    if payload.get("role") != "EMPLOYER_USER":
        raise HTTPException(
            status_code=403,
            detail="Employer access required",
        )

    user_id = payload.get("sub")

    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Invalid token",
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
            detail="Employer profile not found",
        )

    return employer


# ============================================================
# EMPLOYER REGISTRATION
# ============================================================

@router.post("/register")
def register_employer(
    data: dict,
    db: Session = Depends(get_db),
):
    required_fields = [
        "name",
        "email",
        "password",
        "company_name",
        "company_description",
        "company_website",
        "company_location",
        "designation",
        "role_in_company",
    ]

    for field in required_fields:
        if not data.get(field):
            raise HTTPException(
                status_code=400,
                detail=f"{field} is required",
            )

    existing_user = (
        db.query(User)
        .filter(
            User.email == data["email"]
        )
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered",
        )

    company = (
        db.query(Company)
        .filter(
            Company.name == data["company_name"]
        )
        .first()
    )

    if not company:
        company = Company(
            name=data["company_name"],
            description=data["company_description"],
            website=data["company_website"],
            location=data["company_location"],
        )

        db.add(company)
        db.flush()

    user = User(
        name=data["name"],
        email=data["email"],
        password_hash=hash_password(data["password"]),
        role="EMPLOYER_USER",
    )

    db.add(user)
    db.flush()

    employer = EmployerUser(
        user_id=user.id,
        company_id=company.id,
        designation=data["designation"],
        role_in_company=data["role_in_company"],
    )

    db.add(employer)

    db.commit()

    return {
        "message": "Employer registered successfully",
        "user_id": user.id,
        "employer_id": employer.id,
        "company_id": company.id,
    }


# ============================================================
# EMPLOYER DASHBOARD
# ============================================================

@router.get("/dashboard")
def employer_dashboard(
    employer: EmployerUser = Depends(get_current_employer),
    db: Session = Depends(get_db),
):
    company = (
        db.query(Company)
        .filter(
            Company.id == employer.company_id
        )
        .first()
    )

    jobs = (
        db.query(Job)
        .filter(
            Job.employer_id == employer.id
        )
        .order_by(
            Job.created_at.desc()
        )
        .all()
    )

    job_ids = [
        job.id
        for job in jobs
    ]

    total_applications = 0

    if job_ids:
        total_applications = (
            db.query(Application)
            .filter(
                Application.job_id.in_(job_ids)
            )
            .count()
        )

    active_jobs = len(
        [
            job
            for job in jobs
            if job.status == "ACTIVE"
        ]
    )

    return {
        "employer": {
            "id": employer.id,
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
            "active_jobs": active_jobs,
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
            }
            for job in jobs
        ],
    }


# ============================================================
# BUILD AI CANDIDATE INTELLIGENCE
# ============================================================

def build_candidate_intelligence(
    application,
    job,
    candidate,
    resume,
):
    if not resume or not resume.extracted_text:
        return {
            "score": None,
            "readiness": "Not Calculated",
            "resume_skills": [],
            "job_skills": [
                skill.name
                for skill in (job.skills or [])
            ],
            "matching_skills": [],
            "missing_skills": [],
            "recommendations": [],
            "has_resume": False,
            "explanation": (
                "AI fit cannot be calculated because "
                "this application does not have a parsed resume."
            ),
        }

    required_skills = [
        skill.name
        for skill in (job.skills or [])
    ]

    intelligence = calculate_career_fit(
        resume_text=resume.extracted_text,
        job_title=job.title,
        job_description=job.description,
        required_skills=required_skills,
    )

    application.match_score = intelligence["score"]

    return {
        **intelligence,
        "has_resume": True,
        "explanation": (
            f"Candidate matches "
            f"{len(intelligence['matching_skills'])} of "
            f"{len(intelligence['job_skills'])} detected job skills."
        ),
    }


# ============================================================
# BUILD STATUS HISTORY
# ============================================================

def build_status_history(
    application_id,
    db: Session,
):
    history = (
        db.query(ApplicationStatusHistory)
        .filter(
            ApplicationStatusHistory.application_id
            == application_id
        )
        .order_by(
            ApplicationStatusHistory.changed_at.asc()
        )
        .all()
    )

    return [
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
        for event in history
    ]


# ============================================================
# EMPLOYER APPLICATIONS
# ============================================================

@router.get("/applications")
def get_employer_applications(
    employer: EmployerUser = Depends(get_current_employer),
    db: Session = Depends(get_db),
):
    applications = (
        db.query(Application)
        .join(
            Job,
            Application.job_id == Job.id,
        )
        .filter(
            Job.employer_id == employer.id
        )
        .order_by(
            Application.applied_at.desc()
        )
        .all()
    )

    results = []

    for application in applications:

        candidate = (
            db.query(CandidateProfile)
            .filter(
                CandidateProfile.id
                == application.candidate_id
            )
            .first()
        )

        user = None

        if candidate:
            user = (
                db.query(User)
                .filter(
                    User.id == candidate.user_id
                )
                .first()
            )

        job = (
            db.query(Job)
            .filter(
                Job.id == application.job_id
            )
            .first()
        )

        resume = None

        if application.resume_id:
            resume = (
                db.query(Resume)
                .filter(
                    Resume.id == application.resume_id
                )
                .first()
            )

        intelligence = None

        if job and candidate:
            intelligence = build_candidate_intelligence(
                application,
                job,
                candidate,
                resume,
            )

        results.append(
            {
                "application_id": application.id,

                "job_id": (
                    job.id
                    if job
                    else None
                ),

                "job_title": (
                    job.title
                    if job
                    else None
                ),

                "candidate_id": (
                    candidate.id
                    if candidate
                    else None
                ),

                "candidate_name": (
                    user.name
                    if user
                    else None
                ),

                "candidate_email": (
                    user.email
                    if user
                    else None
                ),

                "candidate_location": (
                    candidate.location
                    if candidate
                    else None
                ),

                "candidate_experience": (
                    candidate.experience
                    if candidate
                    else None
                ),

                "candidate_education": (
                    candidate.education
                    if candidate
                    else None
                ),

                "resume_id": (
                    resume.id
                    if resume
                    else None
                ),

                "resume_filename": (
                    resume.original_filename
                    if resume
                    else None
                ),

                "match_score": (
                    intelligence["score"]
                    if intelligence
                    else application.match_score
                ),

                "readiness": (
                    intelligence["readiness"]
                    if intelligence
                    else "Not Calculated"
                ),

                "matching_skills": (
                    intelligence["matching_skills"]
                    if intelligence
                    else []
                ),

                "missing_skills": (
                    intelligence["missing_skills"]
                    if intelligence
                    else []
                ),

                "status": application.status,

                "applied_at": application.applied_at,

                "status_history": build_status_history(
                    application.id,
                    db,
                ),
            }
        )

    db.commit()

    return {
        "total": len(results),
        "applications": results,
    }


# ============================================================
# APPLICATION DETAILS + AI INTELLIGENCE
# ============================================================

@router.get("/applications/{application_id}")
def get_application_details(
    application_id: int,
    employer: EmployerUser = Depends(get_current_employer),
    db: Session = Depends(get_db),
):
    application = (
        db.query(Application)
        .filter(
            Application.id == application_id
        )
        .first()
    )

    if not application:
        raise HTTPException(
            status_code=404,
            detail="Application not found",
        )

    job = (
        db.query(Job)
        .filter(
            Job.id == application.job_id
        )
        .first()
    )

    if not job or job.employer_id != employer.id:
        raise HTTPException(
            status_code=403,
            detail="You do not have access to this application",
        )

    candidate = (
        db.query(CandidateProfile)
        .filter(
            CandidateProfile.id
            == application.candidate_id
        )
        .first()
    )

    if not candidate:
        raise HTTPException(
            status_code=404,
            detail="Candidate not found",
        )

    user = (
        db.query(User)
        .filter(
            User.id == candidate.user_id
        )
        .first()
    )

    resume = None

    if application.resume_id:
        resume = (
            db.query(Resume)
            .filter(
                Resume.id == application.resume_id
            )
            .first()
        )

    intelligence = build_candidate_intelligence(
        application,
        job,
        candidate,
        resume,
    )

    db.commit()

    return {
        "application": {
            "id": application.id,
            "status": application.status,
            "match_score": intelligence["score"],
            "applied_at": application.applied_at,
        },

        "job": {
            "id": job.id,
            "title": job.title,
            "description": job.description,
            "location": job.location,
            "salary": job.salary,
            "experience": job.experience,
            "employment_type": job.employment_type,

            "required_skills": [
                skill.name
                for skill in (job.skills or [])
            ],
        },

        "candidate": {
            "id": candidate.id,
            "name": user.name if user else None,
            "email": user.email if user else None,
            "phone": candidate.phone,
            "location": candidate.location,
            "bio": candidate.bio,
            "experience": candidate.experience,
            "education": candidate.education,
        },

        "resume": (
            {
                "id": resume.id,
                "filename": resume.original_filename,
                "status": resume.status,
            }
            if resume
            else None
        ),

        "intelligence": intelligence,

        "status_history": build_status_history(
            application.id,
            db,
        ),
    }


# ============================================================
# UPDATE APPLICATION STATUS + EMPLOYER FEEDBACK
# ============================================================

@router.patch("/applications/{application_id}/status")
def update_application_status(
    application_id: int,
    data: dict,
    employer: EmployerUser = Depends(get_current_employer),
    db: Session = Depends(get_db),
):
    allowed_statuses = {
        "APPLIED",
        "SCREENING",
        "SHORTLISTED",
        "INTERVIEW",
        "OFFER",
        "HIRED",
        "REJECTED",
    }

    status = data.get("status")
    feedback = data.get("feedback")

    if status not in allowed_statuses:
        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid status. Allowed statuses: "
                + ", ".join(sorted(allowed_statuses))
            ),
        )

    if feedback is not None:
        feedback = str(feedback).strip()

        if len(feedback) > 2000:
            raise HTTPException(
                status_code=400,
                detail="Feedback cannot exceed 2000 characters",
            )

        if not feedback:
            feedback = None

    application = (
        db.query(Application)
        .filter(
            Application.id == application_id
        )
        .first()
    )

    if not application:
        raise HTTPException(
            status_code=404,
            detail="Application not found",
        )

    job = (
        db.query(Job)
        .filter(
            Job.id == application.job_id
        )
        .first()
    )

    if not job or job.employer_id != employer.id:
        raise HTTPException(
            status_code=403,
            detail="You do not have access to this application",
        )

    old_status = application.status

    # Avoid creating duplicate history events when
    # neither the status nor feedback has changed.
    if old_status == status and not feedback:
        return {
            "message": "Application status unchanged",
            "application_id": application.id,
            "status": application.status,
        }

    application.status = status

    history = ApplicationStatusHistory(
        application_id=application.id,
        old_status=old_status,
        new_status=status,
        feedback=feedback,
        changed_by_user_id=employer.user_id,
    )

    db.add(history)

    # Notify the candidate about the status change.
    candidate_profile = application.candidate

    if candidate_profile:
        db.add(
            NotificationItem(
                user_id=candidate_profile.user_id,
                application_id=application.id,
                title="Application status updated",
                message=(
                    f"Your application for {job.title} "
                    f"moved from {old_status or 'NEW'} "
                    f"to {new_status}."
                ),
                notification_type="STATUS_CHANGE",
            )
        )

    db.commit()

    db.refresh(application)
    db.refresh(history)

    return {
        "message": "Application status updated",
        "application_id": application.id,
        "old_status": old_status,
        "status": application.status,
        "feedback": history.feedback,
        "changed_at": history.changed_at,
    }
