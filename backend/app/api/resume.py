from fastapi import APIRouter, UploadFile, File, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.database.models import Resume, CandidateProfile, User
from app.services.resume_parser import extract_text
from app.services.ai_parser import parse_resume
from app.services.job_matcher import match_resume
from app.services.resume_score import calculate_score

import os
import shutil
import uuid


router = APIRouter()

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ---------------------------------------------------------
# UPLOAD RESUME
# ---------------------------------------------------------

@router.post("/upload-resume")
async def upload_resume(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):

    extension = os.path.splitext(file.filename)[1]

    unique_filename = f"{uuid.uuid4()}{extension}"

    file_path = os.path.join(
        UPLOAD_FOLDER,
        unique_filename
    )

    # Save uploaded file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Extract text
    resume_text = extract_text(file_path)

    # Parse candidate information
    candidate = parse_resume(resume_text)

    email = candidate.get("email")

    if not email:
        os.remove(file_path)

        return {
            "error": "Could not extract candidate email from resume."
        }

    # -----------------------------------------------------
    # CHECK EXISTING USER
    # -----------------------------------------------------

    existing_user = db.query(User).filter(
        User.email == email
    ).first()

    if existing_user:

        existing_profile = db.query(
            CandidateProfile
        ).filter(
            CandidateProfile.user_id == existing_user.id
        ).first()

        if existing_profile:

            existing_resume = db.query(
                Resume
            ).filter(
                Resume.candidate_id == existing_profile.id
            ).first()

            if existing_resume:
                os.remove(file_path)

                return {
                    "message": "Resume already uploaded.",
                    "resume_id": existing_resume.id
                }

            candidate_profile = existing_profile

        else:

            candidate_profile = CandidateProfile(
                user_id=existing_user.id,
                phone=candidate.get("phone"),
                location=None,
                bio=None,
                experience=str(
                    candidate.get("experience", "")
                ),
                education=str(
                    candidate.get("education", "")
                )
            )

            db.add(candidate_profile)
            db.flush()

    else:

        # -------------------------------------------------
        # CREATE USER
        # -------------------------------------------------

        user = User(
            name=candidate.get(
                "name",
                "Unknown Candidate"
            ),
            email=email,
            password_hash="TEMPORARY",
            role="JOB_SEEKER"
        )

        db.add(user)
        db.flush()

        # -------------------------------------------------
        # CREATE CANDIDATE PROFILE
        # -------------------------------------------------

        candidate_profile = CandidateProfile(
            user_id=user.id,
            phone=candidate.get("phone"),
            location=None,
            bio=None,
            experience=str(
                candidate.get("experience", "")
            ),
            education=str(
                candidate.get("education", "")
            )
        )

        db.add(candidate_profile)
        db.flush()

    # -----------------------------------------------------
    # SAVE RESUME
    # -----------------------------------------------------

    resume = Resume(
        candidate_id=candidate_profile.id,
        original_filename=file.filename,
        stored_filename=unique_filename,
        file_path=file_path,
        extracted_text=resume_text,
        status="Uploaded"
    )

    db.add(resume)

    db.commit()

    db.refresh(resume)

    return {
        "message": "Resume uploaded successfully",
        "resume_id": resume.id,
        "filename": resume.original_filename,
        "preview": resume_text[:300],
        "candidate": candidate
    }


# ---------------------------------------------------------
# MATCH RESUME
# ---------------------------------------------------------

@router.post("/match-resume")
def match_resume_api(
    resume_id: int,
    skills: list[str],
    db: Session = Depends(get_db)
):

    resume = db.query(Resume).filter(
        Resume.id == resume_id
    ).first()

    if not resume:
        return {
            "error": "Resume not found"
        }

    candidate = parse_resume(
        resume.extracted_text
    )

    score = calculate_score(candidate)

    result = match_resume(
        candidate,
        skills
    )

    return {
        "candidate": candidate,
        "score": score,
        "result": result
    }


# ---------------------------------------------------------
# GET CANDIDATES
# ---------------------------------------------------------

@router.get("/candidates")
def get_candidates(
    db: Session = Depends(get_db)
):

    resumes = db.query(Resume).all()

    candidates = []

    for resume in resumes:

        candidate = parse_resume(
            resume.extracted_text
        )

        score = calculate_score(candidate)

        candidates.append({
            "resume_id": resume.id,
            "candidate_id": resume.candidate_id,
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


# ---------------------------------------------------------
# CANDIDATE RANKING
# ---------------------------------------------------------

@router.get("/candidate-ranking")
def candidate_ranking(
    db: Session = Depends(get_db)
):

    resumes = db.query(Resume).all()

    ranking = []

    for resume in resumes:

        candidate = parse_resume(
            resume.extracted_text
        )

        score = calculate_score(candidate)

        ranking.append({
            "resume_id": resume.id,
            "candidate_id": resume.candidate_id,
            "name": candidate["name"],
            "email": candidate["email"],
            "score": score
        })

    ranking = sorted(
        ranking,
        key=lambda x: x["score"],
        reverse=True
    )

    for index, candidate in enumerate(
        ranking,
        start=1
    ):
        candidate["rank"] = index

    return {
        "total_candidates": len(ranking),
        "ranking": ranking
    }


# ---------------------------------------------------------
# DOWNLOAD RESUME
# ---------------------------------------------------------

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

    if not os.path.exists(resume.file_path):
        return {
            "error": "Resume file not found on server"
        }

    return FileResponse(
        path=resume.file_path,
        filename=resume.original_filename,
        media_type="application/pdf"
    )
