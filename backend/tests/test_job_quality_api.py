from fastapi.testclient import TestClient

from app.auth.token import create_access_token
from app.database.database import SessionLocal
from app.database.models import User
from app.main import app


client = TestClient(app)


def get_user(email: str, role: str):
    db = SessionLocal()

    try:
        return (
            db.query(User)
            .filter(
                User.email == email,
                User.role == role,
            )
            .first()
        )
    finally:
        db.close()


def get_headers(email: str, role: str):
    user = get_user(email, role)

    assert user is not None

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


def test_job_quality_requires_authentication():
    response = client.post(
        "/job-quality/analyze",
        json={
            "title": "Python Backend Developer",
            "description": "Build backend services using Python and FastAPI.",
            "location": "Bengaluru",
            "salary": "₹6,00,000 - ₹10,00,000",
            "experience": "1-3 years",
            "employment_type": "Full-time",
            "skills": [
                "Python",
                "FastAPI",
                "PostgreSQL",
            ],
        },
    )

    assert response.status_code in {401, 403}


def test_candidate_cannot_analyze_job_quality():
    headers = get_headers(
        "arjun.test@example.com",
        "JOB_SEEKER",
    )

    response = client.post(
        "/job-quality/analyze",
        headers=headers,
        json={
            "title": "Python Backend Developer",
            "description": "Build backend services using Python and FastAPI.",
            "location": "Bengaluru",
            "salary": "₹6,00,000 - ₹10,00,000",
            "experience": "1-3 years",
            "employment_type": "Full-time",
            "skills": [
                "Python",
                "FastAPI",
                "PostgreSQL",
            ],
        },
    )

    assert response.status_code == 403


def test_employer_can_analyze_job_quality():
    headers = get_headers(
        "rahul.hr@techcorp.com",
        "EMPLOYER_USER",
    )

    response = client.post(
        "/job-quality/analyze",
        headers=headers,
        json={
            "title": "Python Backend Developer",
            "description": (
                "Build scalable backend services using Python and FastAPI. "
                "Work with PostgreSQL databases, REST APIs, authentication, "
                "testing, deployment and production monitoring. "
                "Collaborate with frontend developers and product teams "
                "to deliver reliable software systems."
            ),
            "location": "Bengaluru",
            "salary": "₹6,00,000 - ₹10,00,000",
            "experience": "1-3 years",
            "employment_type": "Full-time",
            "skills": [
                "Python",
                "FastAPI",
                "PostgreSQL",
                "REST API",
                "Git",
            ],
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["message"] == (
        "Job quality analysis completed"
    )

    quality = data["quality"]

    assert "score" in quality
    assert "quality" in quality
    assert "checks" in quality
    assert "suggestions" in quality
    assert "skills_count" in quality
    assert "description_word_count" in quality

    assert isinstance(quality["score"], int)
    assert 0 <= quality["score"] <= 100
    assert quality["skills_count"] == 5
    assert quality["description_word_count"] > 0


def test_job_quality_identifies_missing_information():
    headers = get_headers(
        "rahul.hr@techcorp.com",
        "EMPLOYER_USER",
    )

    response = client.post(
        "/job-quality/analyze",
        headers=headers,
        json={
            "title": "",
            "description": "",
            "location": None,
            "salary": None,
            "experience": None,
            "employment_type": None,
            "skills": [],
        },
    )

    assert response.status_code == 200

    quality = response.json()["quality"]

    assert quality["score"] == 5
    assert quality["quality"] == "INCOMPLETE"
    assert quality["skills_count"] == 0
    assert len(quality["suggestions"]) > 0
