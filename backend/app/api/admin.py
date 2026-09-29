from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth.token import verify_access_token
from app.database.database import get_db
from app.database.models import (
    User,
    Company,
    Job,
    Application,
    CandidateProfile,
    EmployerUser,
)


router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
)

security = HTTPBearer()


def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    payload = verify_access_token(credentials.credentials)

    if not payload:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
        )

    user_id = payload.get("sub")

    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Invalid token",
        )

    user = (
        db.query(User)
        .filter(User.id == int(user_id))
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=401,
            detail="User not found",
        )

    if user.role != "ADMIN":
        raise HTTPException(
            status_code=403,
            detail="Admin access required",
        )

    return user


def build_daily_analytics(db: Session):
    today = datetime.utcnow().date()
    start_date = today - timedelta(days=6)

    daily = []

    for offset in range(7):
        current_date = start_date + timedelta(days=offset)

        start_datetime = datetime.combine(
            current_date,
            datetime.min.time(),
        )

        end_datetime = start_datetime + timedelta(days=1)

        users = (
            db.query(User)
            .filter(
                User.created_at >= start_datetime,
                User.created_at < end_datetime,
            )
            .count()
        )

        jobs = (
            db.query(Job)
            .filter(
                Job.created_at >= start_datetime,
                Job.created_at < end_datetime,
            )
            .count()
        )

        applications = (
            db.query(Application)
            .filter(
                Application.applied_at >= start_datetime,
                Application.applied_at < end_datetime,
            )
            .count()
        )

        daily.append(
            {
                "date": current_date.isoformat(),
                "label": current_date.strftime("%d %b"),
                "users": users,
                "jobs": jobs,
                "applications": applications,
            }
        )

    return daily


@router.get("/analytics")
def get_admin_analytics(
    admin=Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    total_users = db.query(User).count()

    total_candidates = (
        db.query(User)
        .filter(User.role == "JOB_SEEKER")
        .count()
    )

    total_employers = (
        db.query(User)
        .filter(User.role == "EMPLOYER_USER")
        .count()
    )

    total_admins = (
        db.query(User)
        .filter(User.role == "ADMIN")
        .count()
    )

    total_companies = db.query(Company).count()

    total_jobs = db.query(Job).count()

    active_jobs = (
        db.query(Job)
        .filter(Job.status == "ACTIVE")
        .count()
    )

    closed_jobs = (
        db.query(Job)
        .filter(Job.status == "CLOSED")
        .count()
    )

    total_applications = db.query(Application).count()

    status_rows = (
        db.query(
            Application.status,
            func.count(Application.id),
        )
        .group_by(Application.status)
        .all()
    )

    applications_by_status = {
        status: count
        for status, count in status_rows
    }

    recent_cutoff = datetime.utcnow() - timedelta(days=7)

    recent_applications = (
        db.query(Application)
        .filter(
            Application.applied_at >= recent_cutoff
        )
        .count()
    )

    recent_users = (
        db.query(User)
        .filter(
            User.created_at >= recent_cutoff
        )
        .count()
    )

    recent_jobs = (
        db.query(Job)
        .filter(
            Job.created_at >= recent_cutoff
        )
        .count()
    )

    recent_application_items = (
        db.query(Application)
        .order_by(Application.applied_at.desc())
        .limit(10)
        .all()
    )

    recent_items = []

    for application in recent_application_items:
        candidate = application.candidate

        candidate_user = None

        if candidate:
            candidate_user = (
                db.query(User)
                .filter(
                    User.id == candidate.user_id
                )
                .first()
            )

        job = application.job
        company = job.company if job else None

        recent_items.append(
            {
                "application_id": application.id,
                "candidate_name": (
                    candidate_user.name
                    if candidate_user
                    else "Unknown"
                ),
                "job_title": (
                    job.title
                    if job
                    else "Unknown"
                ),
                "company_name": (
                    company.name
                    if company
                    else "Unknown"
                ),
                "status": application.status,
                "match_score": application.match_score,
                "applied_at": application.applied_at,
            }
        )

    return {
        "admin": {
            "id": admin.id,
            "name": admin.name,
            "email": admin.email,
        },
        "overview": {
            "total_users": total_users,
            "total_candidates": total_candidates,
            "total_employers": total_employers,
            "total_admins": total_admins,
            "total_companies": total_companies,
            "total_jobs": total_jobs,
            "active_jobs": active_jobs,
            "closed_jobs": closed_jobs,
            "total_applications": total_applications,
        },
        "applications_by_status": applications_by_status,
        "last_7_days": {
            "new_users": recent_users,
            "new_jobs": recent_jobs,
            "new_applications": recent_applications,
        },
        "daily_activity": build_daily_analytics(db),
        "recent_applications": recent_items,
    }


@router.get("/users")
def get_admin_users(
    admin=Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    users = (
        db.query(User)
        .order_by(User.created_at.desc())
        .limit(100)
        .all()
    )

    return {
        "users": [
            {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "role": user.role,
                "created_at": user.created_at,
            }
            for user in users
        ]
    }
