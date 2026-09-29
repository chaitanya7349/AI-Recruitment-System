from fastapi.testclient import TestClient

from app.auth.token import create_access_token
from app.database.database import SessionLocal
from app.database.models import CandidateProfile, Resume, User
from app.main import app


client = TestClient(app)


def get_existing_candidate():
    db = SessionLocal()

    try:
        user = (
            db.query(User)
            .filter(
                User.email == "arjun.test@example.com",
                User.role == "JOB_SEEKER",
            )
            .first()
        )

        return user

    finally:
        db.close()


def get_candidate_headers():
    user = get_existing_candidate()

    assert user is not None, (
        "Expected test candidate arjun.test@example.com "
        "was not found in the database."
    )

    token = create_access_token(
        {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role,
        }
    )

    return {
        "Authorization": f"Bearer {token}"
    }


def test_upload_resume_requires_authentication():
    response = client.post(
        "/upload-resume",
        files={
            "file": (
                "resume.pdf",
                b"test",
                "application/pdf",
            )
        },
    )

    assert response.status_code in {401, 403}


def test_upload_resume_rejects_invalid_extension():
    headers = get_candidate_headers()

    response = client.post(
        "/upload-resume",
        headers=headers,
        files={
            "file": (
                "resume.txt",
                b"plain text resume",
                "text/plain",
            )
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Only PDF and DOCX resumes are allowed"
    )


def test_upload_resume_rejects_empty_file():
    headers = get_candidate_headers()

    response = client.post(
        "/upload-resume",
        headers=headers,
        files={
            "file": (
                "resume.pdf",
                b"",
                "application/pdf",
            )
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Uploaded file is empty"


def test_upload_resume_rejects_wrong_content_type():
    headers = get_candidate_headers()

    response = client.post(
        "/upload-resume",
        headers=headers,
        files={
            "file": (
                "resume.pdf",
                b"%PDF-1.7 test",
                "text/plain",
            )
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "File content type does not match the file extension"
    )


def test_upload_resume_rejects_oversized_file():
    headers = get_candidate_headers()

    oversized_content = b"%PDF" + (b"A" * (5 * 1024 * 1024))

    response = client.post(
        "/upload-resume",
        headers=headers,
        files={
            "file": (
                "large-resume.pdf",
                oversized_content,
                "application/pdf",
            )
        },
    )

    assert response.status_code == 413
    assert response.json()["detail"] == (
        "Resume file is too large. Maximum size is 5 MB."
    )


def test_upload_resume_rejects_invalid_pdf_signature():
    headers = get_candidate_headers()

    response = client.post(
        "/upload-resume",
        headers=headers,
        files={
            "file": (
                "resume.pdf",
                b"this is not actually a PDF",
                "application/pdf",
            )
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid PDF file"


def test_upload_resume_rejects_invalid_docx_signature():
    headers = get_candidate_headers()

    response = client.post(
        "/upload-resume",
        headers=headers,
        files={
            "file": (
                "resume.docx",
                b"this is not actually a DOCX file",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid DOCX file"


def test_candidate_cannot_parse_another_candidates_resume():
    db = SessionLocal()

    resume = None

    try:
        candidate_one = (
            db.query(CandidateProfile)
            .filter(CandidateProfile.user_id == 2)
            .first()
        )

        candidate_two = (
            db.query(CandidateProfile)
            .filter(CandidateProfile.user_id == 3)
            .first()
        )

        assert candidate_one is not None
        assert candidate_two is not None

        user_two = (
            db.query(User)
            .filter(User.id == 3)
            .first()
        )

        assert user_two is not None

        resume = Resume(
            candidate_id=candidate_one.id,
            original_filename="ownership-test.pdf",
            stored_filename="ownership-test.pdf",
            file_path="uploads/resumes/ownership-test.pdf",
            extracted_text="Candidate One Python Developer",
            status="UPLOADED",
        )

        db.add(resume)
        db.commit()
        db.refresh(resume)

        resume_id = resume.id

        token = create_access_token(
            {
                "sub": str(user_two.id),
                "email": user_two.email,
                "role": user_two.role,
            }
        )

    finally:
        if resume is not None:
            db.delete(resume)
            db.commit()

        db.close()

    headers = {
        "Authorization": f"Bearer {token}"
    }

    response = client.get(
        f"/{resume_id}/parse",
        headers=headers,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Resume not found"

def get_existing_employer():
    db = SessionLocal()

    try:
        user = (
            db.query(User)
            .filter(
                User.email == "rahul.hr@techcorp.com",
                User.role == "EMPLOYER_USER",
            )
            .first()
        )

        return user

    finally:
        db.close()


def get_employer_headers():
    user = get_existing_employer()

    assert user is not None, (
        "Expected test employer rahul.hr@techcorp.com "
        "was not found in the database."
    )

    token = create_access_token(
        {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role,
        }
    )

    return {
        "Authorization": f"Bearer {token}"
    }


def test_employer_cannot_upload_resume():
    headers = get_employer_headers()

    response = client.post(
        "/upload-resume",
        headers=headers,
        files={
            "file": (
                "resume.pdf",
                b"test",
                "application/pdf",
            )
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Candidate access required"


def test_employer_cannot_parse_candidate_resume():
    db = SessionLocal()

    try:
        resume = (
            db.query(Resume)
            .order_by(Resume.id.asc())
            .first()
        )

        if resume is None:
            return

        resume_id = resume.id

    finally:
        db.close()

    headers = get_employer_headers()

    response = client.get(
        f"/{resume_id}/parse",
        headers=headers,
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Candidate access required"
