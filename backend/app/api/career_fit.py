from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.database.models import CandidateProfile, Job, Resume, User
from app.services.career_fit import calculate_career_fit
from app.auth.token import verify_access_token
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials


router = APIRouter(prefix="/career-fit", tags=["Career Fit"])

security = HTTPBearer()


def get_current_candidate(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    payload = verify_access_token(credentials.credentials)

    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user_id = payload.get("sub")

    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.query(User).filter(User.id == int(user_id)).first()

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    if user.role != "JOB_SEEKER":
        raise HTTPException(status_code=403, detail="Candidate access required")

    candidate = (
        db.query(CandidateProfile)
        .filter(CandidateProfile.user_id == user.id)
        .first()
    )

    if not candidate:
        raise HTTPException(
            status_code=404,
            detail="Candidate profile not found",
        )

    return candidate


def build_skill_actions(missing_skills: list[str]):
    actions = []

    action_templates = {
        "python": {
            "priority": "HIGH",
            "action": "Practice Python fundamentals, functions, OOP, error handling and backend scripting.",
            "project": "Build a small Python REST API or automation project.",
        },
        "fastapi": {
            "priority": "HIGH",
            "action": "Learn FastAPI routing, request validation, dependency injection and authentication.",
            "project": "Build a FastAPI CRUD API connected to PostgreSQL.",
        },
        "postgresql": {
            "priority": "HIGH",
            "action": "Practice SQL queries, joins, indexes, constraints and PostgreSQL database design.",
            "project": "Build a PostgreSQL-backed application with normalized tables.",
        },
        "sql": {
            "priority": "HIGH",
            "action": "Strengthen SELECT, JOIN, GROUP BY, subqueries, CTEs and window functions.",
            "project": "Solve a real-world SQL analytics dataset.",
        },
        "rest api": {
            "priority": "HIGH",
            "action": "Learn REST principles, HTTP methods, status codes, authentication and API design.",
            "project": "Design and implement a production-style REST API.",
        },
        "git": {
            "priority": "MEDIUM",
            "action": "Practice branching, commits, pull requests, merging and conflict resolution.",
            "project": "Maintain a project using feature branches and pull requests.",
        },
        "docker": {
            "priority": "MEDIUM",
            "action": "Learn Docker images, containers, Dockerfiles, volumes and networking.",
            "project": "Containerize a Python backend and PostgreSQL database.",
        },
        "javascript": {
            "priority": "MEDIUM",
            "action": "Strengthen JavaScript fundamentals, asynchronous code, DOM and API integration.",
            "project": "Build a frontend application consuming a REST API.",
        },
        "react": {
            "priority": "HIGH",
            "action": "Learn React components, state, props, hooks and API integration.",
            "project": "Build a dashboard consuming a backend API.",
        },
        "typescript": {
            "priority": "MEDIUM",
            "action": "Learn TypeScript types, interfaces, generics and typed API development.",
            "project": "Convert a JavaScript application to TypeScript.",
        },
        "java": {
            "priority": "HIGH",
            "action": "Strengthen Java OOP, collections, exception handling and backend development.",
            "project": "Build a Java REST API using Spring Boot.",
        },
        "spring boot": {
            "priority": "HIGH",
            "action": "Learn Spring Boot controllers, services, repositories and dependency injection.",
            "project": "Build a Spring Boot CRUD application.",
        },
        "aws": {
            "priority": "MEDIUM",
            "action": "Learn core AWS services, IAM, compute, storage and deployment basics.",
            "project": "Deploy a backend application to AWS.",
        },
        "machine learning": {
            "priority": "HIGH",
            "action": "Study supervised learning, model evaluation, feature engineering and common algorithms.",
            "project": "Build an end-to-end ML prediction project.",
        },
        "pandas": {
            "priority": "MEDIUM",
            "action": "Practice DataFrame operations, cleaning, grouping, merging and data transformation.",
            "project": "Build a data analysis pipeline using Pandas.",
        },
        "numpy": {
            "priority": "LOW",
            "action": "Practice arrays, vectorized operations, indexing and numerical computation.",
            "project": "Implement numerical analysis on a real dataset.",
        },
    }

    for skill in missing_skills:
        key = skill.lower().strip()

        template = action_templates.get(
            key,
            {
                "priority": "MEDIUM",
                "action": f"Build practical knowledge of {skill} through structured learning and hands-on practice.",
                "project": f"Create a small project demonstrating practical {skill} usage.",
            },
        )

        actions.append(
            {
                "skill": skill,
                "priority": template["priority"],
                "action": template["action"],
                "project": template["project"],
            }
        )

    priority_order = {
        "HIGH": 1,
        "MEDIUM": 2,
        "LOW": 3,
    }

    actions.sort(
        key=lambda item: priority_order.get(item["priority"], 4)
    )

    return actions


@router.get("/{job_id}")
def get_career_fit(
    job_id: int,
    candidate: CandidateProfile = Depends(get_current_candidate),
    db: Session = Depends(get_db),
):
    resume = (
        db.query(Resume)
        .filter(Resume.candidate_id == candidate.id)
        .order_by(Resume.uploaded_at.desc())
        .first()
    )

    if not resume:
        raise HTTPException(
            status_code=404,
            detail="Please upload a resume before checking career fit.",
        )

    job = db.query(Job).filter(Job.id == job_id).first()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

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

    return result


@router.get("/{job_id}/skill-gap")
def get_skill_gap(
    job_id: int,
    candidate: CandidateProfile = Depends(get_current_candidate),
    db: Session = Depends(get_db),
):
    resume = (
        db.query(Resume)
        .filter(Resume.candidate_id == candidate.id)
        .order_by(Resume.uploaded_at.desc())
        .first()
    )

    if not resume:
        raise HTTPException(
            status_code=404,
            detail="Please upload a resume before analyzing your skill gap.",
        )

    job = db.query(Job).filter(Job.id == job_id).first()

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job not found",
        )

    required_skills = [
        skill.name
        for skill in job.skills
        if skill.name
    ]

    fit = calculate_career_fit(
        resume_text=resume.extracted_text or "",
        job_title=job.title or "",
        job_description=job.description or "",
        required_skills=required_skills,
    )

    missing_skills = fit.get("missing_skills", [])
    matching_skills = fit.get("matching_skills", [])
    score = fit.get("score", 0)
    readiness = fit.get("readiness", "Needs Improvement")

    actions = build_skill_actions(missing_skills)

    if not missing_skills:
        message = (
            "Your resume currently covers the detected skills required for this job. "
            "Focus on demonstrating these skills through projects and experience."
        )
    else:
        message = (
            f"You are missing {len(missing_skills)} detected job skill"
            f"{'s' if len(missing_skills) != 1 else ''}. "
            "Use the action plan below to close the gaps."
        )

    return {
        "job_id": job.id,
        "job_title": job.title,
        "candidate_id": candidate.id,
        "career_fit_score": score,
        "readiness": readiness,
        "matching_skills": matching_skills,
        "missing_skills": missing_skills,
        "skill_gap_count": len(missing_skills),
        "message": message,
        "actions": actions,
    }
