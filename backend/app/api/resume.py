import hashlib
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.auth.token import verify_access_token
from app.database.database import get_db
from app.database.models import CandidateProfile, Resume, User
from app.services.resume_parser import extract_text
from app.services.ai_parser import parse_resume


router = APIRouter(tags=["Resume"])

security = HTTPBearer()

UPLOAD_DIR = Path("uploads/resumes")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

MAX_FILE_SIZE = 5 * 1024 * 1024

ALLOWED_EXTENSIONS = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


def get_current_candidate(
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
            detail="Invalid authentication token",
        )

    try:
        user_id = int(user_id)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=401,
            detail="Invalid user identity",
        )

    user = db.query(User).filter(User.id == user_id).first()

    if not user or user.role != "JOB_SEEKER":
        raise HTTPException(
            status_code=403,
            detail="Candidate access required",
        )

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


def validate_extension(filename: str) -> str:
    if not filename:
        raise HTTPException(
            status_code=400,
            detail="Filename is required",
        )

    extension = Path(filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Only PDF and DOCX resumes are allowed",
        )

    return extension


@router.post("/upload-resume")
async def upload_resume(
    file: UploadFile = File(...),
    candidate: CandidateProfile = Depends(get_current_candidate),
    db: Session = Depends(get_db),
):
    extension = validate_extension(file.filename or "")

    content_type = file.content_type or ""
    expected_content_type = ALLOWED_EXTENSIONS[extension]

    if content_type != expected_content_type:
        raise HTTPException(
            status_code=400,
            detail="File content type does not match the file extension",
        )

    content = await file.read()

    if not content:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty",
        )

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="Resume file is too large. Maximum size is 5 MB.",
        )

    if extension == ".pdf" and not content.startswith(b"%PDF"):
        raise HTTPException(
            status_code=400,
            detail="Invalid PDF file",
        )

    if extension == ".docx" and not content.startswith(b"PK"):
        raise HTTPException(
            status_code=400,
            detail="Invalid DOCX file",
        )

    uploaded_hash = hashlib.sha256(content).hexdigest()

    existing_resumes = (
        db.query(Resume)
        .filter(Resume.candidate_id == candidate.id)
        .all()
    )

    for existing_resume in existing_resumes:
        existing_path = Path(existing_resume.file_path)

        if existing_path.exists():
            existing_content = existing_path.read_bytes()
            existing_hash = hashlib.sha256(existing_content).hexdigest()

            if existing_hash == uploaded_hash:
                return {
                    "id": existing_resume.id,
                    "original_filename": existing_resume.original_filename,
                    "stored_filename": existing_resume.stored_filename,
                    "status": existing_resume.status,
                    "uploaded_at": existing_resume.uploaded_at,
                    "message": "This resume has already been uploaded.",
                }

    safe_filename = f"{uuid.uuid4().hex}{extension}"
    file_path = UPLOAD_DIR / safe_filename

    try:
        file_path.write_bytes(content)

        extracted_text = extract_text(str(file_path))

        if not extracted_text or not extracted_text.strip():
            file_path.unlink(missing_ok=True)

            raise HTTPException(
                status_code=400,
                detail="Could not extract text from the resume",
            )

        resume = Resume(
            candidate_id=candidate.id,
            original_filename=file.filename or safe_filename,
            stored_filename=safe_filename,
            file_path=str(file_path),
            extracted_text=extracted_text,
            status="UPLOADED",
        )

        db.add(resume)
        db.commit()
        db.refresh(resume)

    except HTTPException:
        raise

    except Exception as exc:
        db.rollback()
        file_path.unlink(missing_ok=True)

        raise HTTPException(
            status_code=400,
            detail=f"Resume processing failed: {str(exc)}",
        )

    return {
        "message": "Resume uploaded and processed successfully",
        "resume_id": resume.id,
        "original_filename": resume.original_filename,
        "stored_filename": resume.stored_filename,
        "status": resume.status,
        "extracted_text_length": len(extracted_text),
    }


@router.get("/my-resumes")
def get_my_resumes(
    candidate: CandidateProfile = Depends(get_current_candidate),
    db: Session = Depends(get_db),
):
    resumes = (
        db.query(Resume)
        .filter(Resume.candidate_id == candidate.id)
        .order_by(Resume.uploaded_at.desc())
        .all()
    )

    return [
        {
            "id": resume.id,
            "original_filename": resume.original_filename,
            "stored_filename": resume.stored_filename,
            "status": resume.status,
            "uploaded_at": resume.uploaded_at,
            "extracted_text_length": len(resume.extracted_text or ""),
        }
        for resume in resumes
    ]


@router.get("/{resume_id}/parse")
def parse_uploaded_resume(
    resume_id: int,
    candidate: CandidateProfile = Depends(get_current_candidate),
    db: Session = Depends(get_db),
):
    resume = (
        db.query(Resume)
        .filter(
            Resume.id == resume_id,
            Resume.candidate_id == candidate.id,
        )
        .first()
    )

    if not resume:
        raise HTTPException(
            status_code=404,
            detail="Resume not found",
        )

    if not resume.extracted_text:
        raise HTTPException(
            status_code=400,
            detail="Resume text has not been extracted",
        )

    parsed_resume = parse_resume(resume.extracted_text)

    return {
        "message": "Resume parsed successfully",
        "resume_id": resume.id,
        "parsed_resume": parsed_resume,
    }
