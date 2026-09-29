from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

from app.auth.token import verify_access_token
from app.database.models import User
from app.database.database import get_db
from app.services.job_quality import analyze_job_quality
from sqlalchemy.orm import Session


router = APIRouter(
    prefix="/job-quality",
    tags=["Job Quality Analyzer"],
)

security = HTTPBearer()


class JobQualityRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    location: str | None = None
    salary: str | None = None
    experience: str | None = None
    employment_type: str | None = None
    skills: list[str] = []


def get_current_employer(
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

    user = db.query(User).filter(User.id == int(user_id)).first()

    if not user:
        raise HTTPException(
            status_code=401,
            detail="User not found",
        )

    if user.role != "EMPLOYER_USER":
        raise HTTPException(
            status_code=403,
            detail="Employer access required",
        )

    return user


@router.post("/analyze")
def analyze_job(
    data: JobQualityRequest,
    employer=Depends(get_current_employer),
):
    result = analyze_job_quality(data.model_dump())

    return {
        "message": "Job quality analysis completed.",
        "analyzed_by": employer.name,
        **result,
    }
