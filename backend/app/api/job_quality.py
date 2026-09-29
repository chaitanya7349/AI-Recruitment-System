from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.auth.dependencies import require_employer
from app.database.models import User
from app.services.job_quality import analyze_job_quality

router = APIRouter(
    prefix="/job-quality",
    tags=["Job Quality"],
)


class JobQualityRequest(BaseModel):
    title: str
    description: str
    location: str | None = None
    salary: str | None = None
    experience: str | None = None
    employment_type: str | None = None
    skills: list[str] = []


@router.post("/analyze")
def analyze_job(
    data: JobQualityRequest,
    employer: User = Depends(require_employer),
):
    result = analyze_job_quality(
        {
            "title": data.title,
            "description": data.description,
            "location": data.location,
            "salary": data.salary,
            "experience": data.experience,
            "employment_type": data.employment_type,
            "skills": data.skills,
        }
    )

    return {
        "message": "Job quality analysis completed",
        "quality": result,
    }
