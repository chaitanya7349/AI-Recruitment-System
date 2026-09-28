from fastapi import APIRouter, UploadFile, File, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.database.models import Resume, Candidate
from app.services.resume_parser import extract_text
from app.services.ai_parser import parse_resume
from app.schemas.job import JobDescription
from app.services.job_matcher import match_resume
from app.services.resume_score import calculate_score

import os
import shutil
import uuid


router = APIRouter()

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@router.post("/upload-resume")
async def upload_resume(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):

    # Get file extension
    extension = os.path.splitext(file.filename)[1]

    # Generate unique filename
    unique_filename = f"{uuid.uuid4()}{extension}"

    # File path
    file_path = os.path.join(UPLOAD_FOLDER, unique_filename)

    # Save uploaded file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Extract resume text
    resume_text = extract_text(file_path)

    # Parse candidate details
    candidate = parse_resume(resume_text)

    # Check duplicate email
    existing = db.query(Resume).filter(
        Resume.extracted_text.contains(candidate["email"])
    ).first()

    if existing:
        # Remove duplicate uploaded file
        os.remove(file_path)

        return {
            "message": "Resume already uploaded."
        }

    # Save resume
    resume = Resume(
        original_filename=file.filename,
        stored_filename=unique_filename,
        file_path=file_path,
        extracted_text=resume_text
    )

    db.add(resume)
    db.flush()

    # Save candidate
    candidate_record = Candidate(
        name=candidate["name"],
        email=candidate["email"],
        phone=candidate["phone"],
        skills=", ".join(candidate["skills"])
        if isinstance(candidate["skills"], list)
        else candidate["skills"],
        education=candidate["education"],
        experience=candidate["experience"],
        resume_path=file_path
    )

    db.add(candidate_record)

    # Save both Resume and Candidate
    db.commit()

    # Refresh database records
    db.refresh(resume)
    db.refresh(candidate_record)

    return {
        "message": "Resume uploaded successfully",
        "resume_id": resume.id,
        "filename": resume.original_filename,
        "preview": resume_text[:300],
        "candidate": candidate
    }


@router.post("/match-resume")
def match_resume_api(
    job: JobDescription,
    db: Session = Depends(get_db)
):

    resume = db.query(Resume).filter(
        Resume.id == job.resume_id
    ).first()

    if not resume:
        return {
            "error": "Resume not found"
        }

    candidate = parse_resume(resume.extracted_text)

    score = calculate_score(candidate)

    result = match_resume(
        candidate,
        job.skills
    )

    return {
        "candidate": candidate,
        "result": result
    }


@router.get("/candidates")
def get_candidates(db: Session = Depends(get_db)):

    resumes = db.query(Resume).all()

    candidates = []

    for resume in resumes:

        candidate = parse_resume(resume.extracted_text)

        score = calculate_score(candidate)

        candidates.append({
            "resume_id": resume.id,
            "name": candidate["name"],
            "email": candidate["email"],
            "phone": candidate["phone"],
            "skills": candidate["skills"],
            "education": candidate["education"],
            "experience": candidate["experience"],
            "score": score,
            "uploaded_at": resume.uploaded_at
        })

    return {
        "total_candidates": len(candidates),
        "candidates": candidates
    }


@router.get("/candidate-ranking")
def candidate_ranking(db: Session = Depends(get_db)):

    resumes = db.query(Resume).all()

    ranking = []

    for resume in resumes:

        candidate = parse_resume(resume.extracted_text)

        score = calculate_score(candidate)

        ranking.append({
            "name": candidate["name"],
            "email": candidate["email"],
            "score": score
        })

    ranking = sorted(
        ranking,
        key=lambda x: x["score"],
        reverse=True
    )

    for i, candidate in enumerate(ranking):
        candidate["rank"] = i + 1

    return {
        "total_candidates": len(ranking),
        "ranking": ranking
    }


@router.get("/download-resume/{resume_id}")
def download_resume(
    resume_id: int,
    db: Session = Depends(get_db)
):

    resume = db.query(Resume).filter(
        Resume.id == resume_id
    ).first()

    if not resume:
        return {
            "error": "Resume not found"
        }

    return FileResponse(
        path=resume.file_path,
        filename=resume.original_filename,
        media_type="application/pdf"
    )
