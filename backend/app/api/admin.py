from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth.dependencies import require_admin
from app.database.database import get_db
from app.database.models import (
    Application,
    CandidateProfile,
    Company,
    Job,
    User,
)

router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
)


def build_daily_analytics(db: Session):
    today = datetime.utcnow().date()
    result = []

    for offset in range(6, -1, -1):
        current_day = today - timedelta(days=offset)

        start = datetime.combine(
            current_day,
            datetime.min.time(),
        )

        end = start + timedelta(days=1)

        users_count = (
            db.query(func.count(User.id))
            .filter(
                User.created_at >= start,
                User.created_at < end,
            )
            .scalar()
            or 0
        )

        jobs_count = (
            db.query(func.count(Job.id))
            .filter(
                Job.created_at >= start,
                Job.created_at < end,
            )
            .scalar()
            or 0
        )

        applications_count = (
            db.query(func.count(Application.id))
            .filter(
                Application.applied_at >= start,
                Application.applied_at < end,
            )
            .scalar()
            or 0
        )

        result.append(
            {
                "date": current_day.isoformat(),
                "users": users_count,
                "jobs": jobs_count,
                "applications": applications_count,
            }
        )

    return result


@router.get("/analytics")
def get_admin_analytics(
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    total_users = db.query(func.count(User.id)).scalar() or 0

    total_candidates = (
        db.query(func.count(User.id))
        .filter(User.role == "JOB_SEEKER")
        .scalar()
        or 0
    )

    total_employers = (
        db.query(func.count(User.id))
        .filter(User.role == "EMPLOYER_USER")
        .scalar()
        or 0
    )

    total_admins = (
        db.query(func.count(User.id))
        .filter(User.role == "ADMIN")
        .scalar()
        or 0
    )

    total_companies = (
        db.query(func.count(Company.id)).scalar() or 0
    )

    total_jobs = (
        db.query(func.count(Job.id)).scalar() or 0
    )

    active_jobs = (
        db.query(func.count(Job.id))
        .filter(Job.status == "ACTIVE")
        .scalar()
        or 0
    )

    closed_jobs = (
        db.query(func.count(Job.id))
        .filter(Job.status == "CLOSED")
        .scalar()
        or 0
    )

    total_applications = (
        db.query(func.count(Application.id)).scalar() or 0
    )

    status_rows = (
        db.query(
            Application.status,
            func.count(Application.id),
        )
        .group_by(Application.status)
        .all()
    )

    application_status_counts = {
        status: count
        for status, count in status_rows
    }

    recent_users = (
        db.query(User)
        .order_by(User.created_at.desc())
        .limit(10)
        .all()
    )

    recent_applications = (
        db.query(Application)
        .order_by(Application.applied_at.desc())
        .limit(10)
        .all()
    )

    daily_activity = build_daily_analytics(db)

    return {
        "total_users": total_users,
        "total_candidates": total_candidates,
        "total_employers": total_employers,
        "total_admins": total_admins,
        "total_companies": total_companies,
        "total_jobs": total_jobs,
        "active_jobs": active_jobs,
        "closed_jobs": closed_jobs,
        "total_applications": total_applications,
        "application_status_counts": application_status_counts,
        "daily_activity": daily_activity,
        "recent_users": [
            {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "role": user.role,
                "created_at": user.created_at,
            }
            for user in recent_users
        ],
        "recent_applications": [
            {
                "id": application.id,
                "candidate_id": application.candidate_id,
                "job_id": application.job_id,
                "status": application.status,
                "match_score": application.match_score,
                "applied_at": application.applied_at,
            }
            for application in recent_applications
        ],
    }


@router.get("/users")
def get_admin_users(
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    users = (
        db.query(User)
        .order_by(User.created_at.desc())
        .limit(100)
        .all()
    )

    return [
        {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "created_at": user.created_at,
        }
        for user in users
    ]
