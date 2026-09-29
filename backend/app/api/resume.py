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

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
)
from fastapi.security import (
    HTTPBearer,
    HTTPAuthorizationCredentials,
)
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.database.models import (
    User,
    CandidateProfile,
    Resume,
)
from app.auth.token import verify_access_token
from app.services.resume_parser import extract_text


router = APIRouter(
    tags=["Resume"]
)

security = HTTPBearer()

UPLOAD_FOLDER = "uploads/resumes"

os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True
)


def get_current_candidate(
    credentials: HTTPAuthorizationCredentials = Depends(
        security
    ),
    db: Session = Depends(get_db)
):
    payload = verify_access_token(
        credentials.credentials
    )

    if not payload:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )

    user_id = payload.get("sub")
    role = payload.get("role")

    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication token"
        )

    if role != "JOB_SEEKER":
        raise HTTPException(
            status_code=403,
            detail="Candidate access required"
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
            detail="Candidate profile not found"
        )

    return candidate


# ---------------------------------------------------------
# UPLOAD RESUME
# ---------------------------------------------------------

@router.post("/upload-resume")
async def upload_resume(
    file: UploadFile = File(...),
    candidate: CandidateProfile = Depends(
        get_current_candidate
    ),
    db: Session = Depends(get_db)
):
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No file selected"
        )

    extension = os.path.splitext(
        file.filename
    )[1].lower()

    allowed_extensions = {
        ".pdf",
        ".docx",
    }

    if extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail="Only PDF and DOCX files are supported"
        )

    unique_filename = (
        f"{uuid.uuid4()}{extension}"
    )

    file_path = os.path.join(
        UPLOAD_FOLDER,
        unique_filename
    )

    try:
        with open(
            file_path,
            "wb"
        ) as buffer:
            shutil.copyfileobj(
                file.file,
                buffer
            )

        resume_text = extract_text(
            file_path
        )

        if not resume_text:
            os.remove(file_path)

            raise HTTPException(
                status_code=400,
                detail="Could not extract text from resume"
            )

        resume = Resume(
            candidate_id=candidate.id,
            original_filename=file.filename,
            stored_filename=unique_filename,
            file_path=file_path,
            extracted_text=resume_text,
            status="PARSED",
        )

        db.add(resume)
        db.commit()
        db.refresh(resume)

        return {
            "message": "Resume uploaded and parsed successfully",
            "resume_id": resume.id,
            "filename": resume.original_filename,
            "status": resume.status,
            "text_length": len(resume_text),
        }

    except HTTPException:
        raise

    except Exception as error:
        db.rollback()

        if os.path.exists(file_path):
            os.remove(file_path)

        raise HTTPException(
            status_code=500,
            detail=f"Resume processing failed: {str(error)}"
        )


# ---------------------------------------------------------
# GET MY RESUMES
# ---------------------------------------------------------

@router.get("/my-resumes")
def get_my_resumes(
    candidate: CandidateProfile = Depends(
        get_current_candidate
    ),
    db: Session = Depends(get_db)
):
    resumes = (
        db.query(Resume)
        .filter(
            Resume.candidate_id == candidate.id
        )
        .order_by(
            Resume.uploaded_at.desc()
        )
        .all()
    )

    return {
        "total": len(resumes),
        "resumes": [
            {
                "id": resume.id,
                "filename": resume.original_filename,
                "status": resume.status,
                "uploaded_at": resume.uploaded_at,
            }
            for resume in resumes
        ],
    }
