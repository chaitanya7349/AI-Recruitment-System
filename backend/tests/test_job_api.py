from fastapi.testclient import TestClient

from app.auth.token import create_access_token
from app.database.database import SessionLocal
from app.database.models import Company, EmployerUser, Job, User
from app.main import app


client = TestClient(app)


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


def get_employer_context():
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

        assert user is not None, (
            "Expected test employer rahul.hr@techcorp.com "
            "was not found in the database."
        )

        employer = (
            db.query(EmployerUser)
            .filter(EmployerUser.user_id == user.id)
            .first()
        )

        assert employer is not None
        assert employer.company_id is not None

        return user.id, employer.id, employer.company_id

    finally:
        db.close()


def test_get_jobs_endpoint_is_available():
    response = client.get("/jobs/")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_nonexistent_job_returns_404():
    response = client.get("/jobs/999999999")

    assert response.status_code == 404


def test_get_existing_job_returns_job_details():
    db = SessionLocal()

    try:
        job = (
            db.query(Job)
            .filter(Job.status == "ACTIVE")
            .order_by(Job.id.asc())
            .first()
        )

        if job is None:
            return

        job_id = job.id

    finally:
        db.close()

    response = client.get(f"/jobs/{job_id}")

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == job_id
    assert "title" in data
    assert "description" in data
    assert "company_name" in data
    assert "skills" in data


def test_create_job_requires_authentication():
    response = client.post(
        "/jobs/",
        json={
            "title": "Test Backend Developer",
            "description": "Test job",
            "location": "Bengaluru",
            "salary": "₹5,00,000 - ₹8,00,000",
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


def test_job_update_requires_authentication():
    response = client.put(
        "/jobs/999999999",
        json={
            "title": "Updated Job",
            "description": "Updated description",
            "location": "Bengaluru",
            "salary": "₹5,00,000 - ₹8,00,000",
            "experience": "1-3 years",
            "employment_type": "Full-time",
            "skills": ["Python"],
        },
    )

    assert response.status_code in {401, 403}


def test_job_close_requires_authentication():
    response = client.patch(
        "/jobs/999999999/close"
    )

    assert response.status_code in {401, 403}


def test_employer_can_create_job():
    headers = get_employer_headers()

    response = client.post(
        "/jobs/",
        headers=headers,
        json={
            "title": "Automated Job Creation Test",
            "description": "Temporary job used for automated testing.",
            "location": "Bengaluru",
            "salary": "₹6,00,000 - ₹10,00,000",
            "experience": "1-3 years",
            "employment_type": "Full-time",
            "skills": [
                "Python",
                "FastAPI",
            ],
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["title"] == "Automated Job Creation Test"
    assert data["status"] == "ACTIVE"
    assert "Python" in data["skills"]
    assert "FastAPI" in data["skills"]

    job_id = data["id"]

    db = SessionLocal()

    try:
        job = db.query(Job).filter(Job.id == job_id).first()

        assert job is not None
        assert job.status == "ACTIVE"

        db.delete(job)
        db.commit()

    finally:
        db.close()


def test_employer_can_update_own_job():
    headers = get_employer_headers()

    user_id, employer_id, company_id = get_employer_context()

    db = SessionLocal()

    try:
        job = Job(
            company_id=company_id,
            employer_id=employer_id,
            title="Temporary Update Test",
            description="Original description",
            location="Bengaluru",
            salary="Test",
            experience="1-3 years",
            employment_type="Full-time",
            status="ACTIVE",
        )

        db.add(job)
        db.commit()
        db.refresh(job)

        job_id = job.id

    finally:
        db.close()

    response = client.put(
        f"/jobs/{job_id}",
        headers=headers,
        json={
            "title": "Updated Backend Engineer",
            "description": "Updated job description",
            "location": "Hyderabad",
            "salary": "₹8,00,000 - ₹12,00,000",
            "experience": "2-4 years",
            "employment_type": "Full-time",
            "skills": ["Python", "FastAPI"],
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["title"] == "Updated Backend Engineer"
    assert data["location"] == "Hyderabad"
    assert data["experience"] == "2-4 years"

    db = SessionLocal()

    try:
        job = db.query(Job).filter(Job.id == job_id).first()

        if job is not None:
            db.delete(job)
            db.commit()

    finally:
        db.close()


def test_employer_can_close_own_job():
    headers = get_employer_headers()

    user_id, employer_id, company_id = get_employer_context()

    db = SessionLocal()

    try:
        job = Job(
            company_id=company_id,
            employer_id=employer_id,
            title="Temporary Close Test",
            description="Temporary job.",
            location="Bengaluru",
            salary="Test",
            experience="Test",
            employment_type="Full-time",
            status="ACTIVE",
        )

        db.add(job)
        db.commit()
        db.refresh(job)

        job_id = job.id

    finally:
        db.close()

    response = client.patch(
        f"/jobs/{job_id}/close",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["job_id"] == job_id
    assert data["status"] == "CLOSED"

    db = SessionLocal()

    try:
        job = db.query(Job).filter(Job.id == job_id).first()

        if job is not None:
            db.delete(job)
            db.commit()

    finally:
        db.close()


def test_employer_cannot_update_another_company_job():
    headers = get_employer_headers()

    db = SessionLocal()

    try:
        employer_user = (
            db.query(User)
            .filter(
                User.email == "rahul.hr@techcorp.com",
                User.role == "EMPLOYER_USER",
            )
            .first()
        )

        assert employer_user is not None

        employer = (
            db.query(EmployerUser)
            .filter(EmployerUser.user_id == employer_user.id)
            .first()
        )

        assert employer is not None
        assert employer.company_id is not None

        other_company = (
            db.query(Company)
            .filter(Company.id != employer.company_id)
            .first()
        )

        if other_company is None:
            return

        other_employer = (
            db.query(EmployerUser)
            .filter(EmployerUser.company_id == other_company.id)
            .first()
        )

        if other_employer is None:
            return

        job = Job(
            company_id=other_company.id,
            employer_id=other_employer.id,
            title="Other Company Job",
            description="Temporary authorization test.",
            location="Bengaluru",
            salary="Test",
            experience="Test",
            employment_type="Full-time",
            status="ACTIVE",
        )

        db.add(job)
        db.commit()
        db.refresh(job)

        job_id = job.id

    finally:
        db.close()

    response = client.put(
        f"/jobs/{job_id}",
        headers=headers,
        json={
            "title": "Unauthorized Update",
            "description": "This update must be rejected.",
            "location": "Bengaluru",
            "salary": "Test",
            "experience": "Test",
            "employment_type": "Full-time",
            "skills": ["Python"],
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "You can only update your company's jobs"
    )

    db = SessionLocal()

    try:
        job = db.query(Job).filter(Job.id == job_id).first()

        if job is not None:
            db.delete(job)
            db.commit()

    finally:
        db.close()


def test_employer_cannot_close_another_company_job():
    headers = get_employer_headers()

    db = SessionLocal()

    try:
        employer_user = (
            db.query(User)
            .filter(
                User.email == "rahul.hr@techcorp.com",
                User.role == "EMPLOYER_USER",
            )
            .first()
        )

        assert employer_user is not None

        employer = (
            db.query(EmployerUser)
            .filter(EmployerUser.user_id == employer_user.id)
            .first()
        )

        assert employer is not None
        assert employer.company_id is not None

        other_company = (
            db.query(Company)
            .filter(Company.id != employer.company_id)
            .first()
        )

        if other_company is None:
            return

        other_employer = (
            db.query(EmployerUser)
            .filter(EmployerUser.company_id == other_company.id)
            .first()
        )

        if other_employer is None:
            return

        job = Job(
            company_id=other_company.id,
            employer_id=other_employer.id,
            title="Other Company Close Test",
            description="Temporary authorization test.",
            location="Bengaluru",
            salary="Test",
            experience="Test",
            employment_type="Full-time",
            status="ACTIVE",
        )

        db.add(job)
        db.commit()
        db.refresh(job)

        job_id = job.id

    finally:
        db.close()

    response = client.patch(
        f"/jobs/{job_id}/close",
        headers=headers,
    )

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "You can only close your company's jobs"
    )

    db = SessionLocal()

    try:
        job = db.query(Job).filter(Job.id == job_id).first()

        if job is not None:
            db.delete(job)
            db.commit()

    finally:
        db.close()


def test_update_nonexistent_job_returns_404():
    headers = get_employer_headers()

    response = client.put(
        "/jobs/999999999",
        headers=headers,
        json={
            "title": "Updated Job",
            "description": "Updated description",
            "location": "Bengaluru",
            "salary": "Test",
            "experience": "Test",
            "employment_type": "Full-time",
            "skills": ["Python"],
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Job not found"


def test_close_nonexistent_job_returns_404():
    headers = get_employer_headers()

    response = client.patch(
        "/jobs/999999999/close",
        headers=headers,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Job not found"
