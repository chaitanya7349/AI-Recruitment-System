from fastapi.testclient import TestClient

from app.auth.token import create_access_token
from app.database.database import SessionLocal
from app.database.models import CandidateProfile, Job, Resume, User
from app.main import app

client = TestClient(app)


def get_existing_candidate():
    db = SessionLocal()
    try:
        return (
            db.query(User)
            .filter(
                User.email == "arjun.test@example.com",
                User.role == "JOB_SEEKER",
            )
            .first()
        )
    finally:
        db.close()


def get_candidate_headers():
    user = get_existing_candidate()
    assert user is not None

    token = create_access_token(
        {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role,
        }
    )

    return {"Authorization": f"Bearer {token}"}


def get_active_job():
    db = SessionLocal()
    try:
        return (
            db.query(Job)
            .filter(Job.status == "ACTIVE")
            .order_by(Job.id.asc())
            .first()
        )
    finally:
        db.close()


def get_candidate_resume():
    user = get_existing_candidate()
    assert user is not None

    db = SessionLocal()
    try:
        candidate = (
            db.query(CandidateProfile)
            .filter(CandidateProfile.user_id == user.id)
            .first()
        )
        assert candidate is not None

        return (
            db.query(Resume)
            .filter(
                Resume.candidate_id == candidate.id,
                Resume.extracted_text.isnot(None),
            )
            .order_by(Resume.uploaded_at.desc())
            .first()
        )
    finally:
        db.close()


def test_career_fit_requires_authentication():
    job = get_active_job()
    assert job is not None

    response = client.get(f"/career-fit/{job.id}")

    assert response.status_code in {401, 403}


def test_skill_gap_requires_authentication():
    job = get_active_job()
    assert job is not None

    response = client.get(f"/career-fit/{job.id}/skill-gap")

    assert response.status_code in {401, 403}


def test_invalid_token_returns_401():
    response = client.get(
        "/career-fit/1",
        headers={"Authorization": "Bearer invalid-token"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or expired token"


def test_token_without_sub_returns_401():
    token = create_access_token(
        {
            "email": "test@example.com",
            "role": "JOB_SEEKER",
        }
    )

    response = client.get(
        "/career-fit/1",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or expired token"


def test_token_for_missing_user_returns_401():
    token = create_access_token(
        {
            "sub": "999999999",
            "email": "missing@example.com",
            "role": "JOB_SEEKER",
        }
    )

    response = client.get(
        "/career-fit/1",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "User not found"


def test_employer_cannot_access_career_fit():
    db = SessionLocal()
    try:
        employer = (
            db.query(User)
            .filter(User.role == "EMPLOYER_USER")
            .first()
        )
        assert employer is not None

        token = create_access_token(
            {
                "sub": str(employer.id),
                "email": employer.email,
                "role": employer.role,
            }
        )
    finally:
        db.close()

    response = client.get(
        "/career-fit/1",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Candidate access required"


def test_candidate_without_profile_returns_404():
    db = SessionLocal()

    try:
        temporary_user = User(
            name="Temporary No Profile User",
            email="temporary-no-profile@example.com",
            password_hash="temporary-test-password",
            role="JOB_SEEKER",
        )

        db.add(temporary_user)
        db.commit()

        user_id = temporary_user.id
        user_email = temporary_user.email

    finally:
        db.close()

    try:
        token = create_access_token(
            {
                "sub": str(user_id),
                "email": user_email,
                "role": "JOB_SEEKER",
            }
        )

        response = client.get(
            "/career-fit/1",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Candidate profile not found"

    finally:
        db = SessionLocal()
        try:
            user = (
                db.query(User)
                .filter(User.id == user_id)
                .first()
            )

            if user is not None:
                db.delete(user)

            db.commit()

        finally:
            db.close()



def test_career_fit_without_resume():
    db = SessionLocal()

    temporary_user = None
    temporary_candidate = None

    try:
        temporary_user = User(
            name="Temporary Career Fit User",
            email="temporary-career-fit@example.com",
            password_hash="temporary-test-password",
            role="JOB_SEEKER",
        )

        db.add(temporary_user)
        db.flush()

        temporary_candidate = CandidateProfile(
            user_id=temporary_user.id,
        )

        db.add(temporary_candidate)
        db.commit()

        user_id = temporary_user.id

        token = create_access_token(
            {
                "sub": str(user_id),
                "email": temporary_user.email,
                "role": temporary_user.role,
            }
        )

    finally:
        db.close()

    try:
        job = get_active_job()
        assert job is not None

        response = client.get(
            f"/career-fit/{job.id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 404
        assert response.json()["detail"] == (
            "Please upload a resume before checking career fit."
        )

    finally:
        db = SessionLocal()
        try:
            candidate = (
                db.query(CandidateProfile)
                .filter(CandidateProfile.user_id == user_id)
                .first()
            )

            user = (
                db.query(User)
                .filter(User.id == user_id)
                .first()
            )

            if candidate is not None:
                db.delete(candidate)

            if user is not None:
                db.delete(user)

            db.commit()

        finally:
            db.close()


def test_skill_gap_without_resume():
    db = SessionLocal()

    temporary_user = None
    temporary_candidate = None

    try:
        temporary_user = User(
            name="Temporary Skill Gap User",
            email="temporary-skill-gap@example.com",
            password_hash="temporary-test-password",
            role="JOB_SEEKER",
        )

        db.add(temporary_user)
        db.flush()

        temporary_candidate = CandidateProfile(
            user_id=temporary_user.id,
        )

        db.add(temporary_candidate)
        db.commit()

        user_id = temporary_user.id

        token = create_access_token(
            {
                "sub": str(user_id),
                "email": temporary_user.email,
                "role": temporary_user.role,
            }
        )

    finally:
        db.close()

    try:
        job = get_active_job()
        assert job is not None

        response = client.get(
            f"/career-fit/{job.id}/skill-gap",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 404
        assert response.json()["detail"] == (
            "Please upload a resume before analyzing your skill gap."
        )

    finally:
        db = SessionLocal()
        try:
            candidate = (
                db.query(CandidateProfile)
                .filter(CandidateProfile.user_id == user_id)
                .first()
            )

            user = (
                db.query(User)
                .filter(User.id == user_id)
                .first()
            )

            if candidate is not None:
                db.delete(candidate)

            if user is not None:
                db.delete(user)

            db.commit()

        finally:
            db.close()



def test_career_fit_nonexistent_job_returns_404():
    headers = get_candidate_headers()

    response = client.get(
        "/career-fit/999999999",
        headers=headers,
    )

    assert response.status_code == 404


def test_skill_gap_nonexistent_job_returns_404():
    headers = get_candidate_headers()

    response = client.get(
        "/career-fit/999999999/skill-gap",
        headers=headers,
    )

    assert response.status_code == 404


def test_career_fit_success():
    job = get_active_job()
    resume = get_candidate_resume()

    assert job is not None
    assert resume is not None

    headers = get_candidate_headers()

    response = client.get(
        f"/career-fit/{job.id}",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert "score" in data
    assert "readiness" in data
    assert "matching_skills" in data
    assert "missing_skills" in data
    assert "recommendations" in data

    assert isinstance(data["score"], (int, float))
    assert isinstance(data["matching_skills"], list)
    assert isinstance(data["missing_skills"], list)
    assert isinstance(data["recommendations"], list)


def test_skill_gap_success():
    job = get_active_job()
    resume = get_candidate_resume()

    assert job is not None
    assert resume is not None

    headers = get_candidate_headers()

    response = client.get(
        f"/career-fit/{job.id}/skill-gap",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["job_id"] == job.id
    assert data["job_title"] == job.title
    assert "candidate_id" in data
    assert "career_fit_score" in data
    assert "readiness" in data
    assert "matching_skills" in data
    assert "missing_skills" in data
    assert "skill_gap_count" in data
    assert "message" in data
    assert "actions" in data

    assert isinstance(data["matching_skills"], list)
    assert isinstance(data["missing_skills"], list)
    assert isinstance(data["actions"], list)


def test_skill_gap_no_missing_skills_branch():
    user = get_existing_candidate()
    assert user is not None

    db = SessionLocal()
    try:
        candidate = (
            db.query(CandidateProfile)
            .filter(CandidateProfile.user_id == user.id)
            .first()
        )
        assert candidate is not None

        resume = (
            db.query(Resume)
            .filter(
                Resume.candidate_id == candidate.id,
                Resume.extracted_text.isnot(None),
            )
            .order_by(Resume.uploaded_at.desc())
            .first()
        )
        assert resume is not None

        job = (
            db.query(Job)
            .filter(Job.status == "ACTIVE")
            .order_by(Job.id.asc())
            .first()
        )
        assert job is not None

        job_id = job.id

        headers = get_candidate_headers()

    finally:
        db.close()

    response = client.get(
        f"/career-fit/{job_id}/skill-gap",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    if data["missing_skills"]:
        return

    assert data["missing_skills"] == []
    assert data["skill_gap_count"] == 0
    assert (
        "currently covers the detected skills required"
        in data["message"]
    )
