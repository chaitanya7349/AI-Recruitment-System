from fastapi.testclient import TestClient

from app.auth.token import create_access_token
from app.database.database import SessionLocal
from app.database.models import (
    Application,
    ApplicationStatusHistory,
    EmployerUser,
    Job,
    NotificationItem,
    User,
)
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


def test_employer_dashboard_requires_authentication():
    response = client.get("/employer/dashboard")

    assert response.status_code in {401, 403}


def test_employer_applications_require_authentication():
    response = client.get("/employer/applications")

    assert response.status_code in {401, 403}


def test_employer_dashboard_is_accessible_to_employer():
    headers = get_employer_headers()

    response = client.get(
        "/employer/dashboard",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert "employer" in data
    assert "company" in data
    assert "jobs" in data


def test_employer_applications_are_accessible_to_employer():
    headers = get_employer_headers()

    response = client.get(
        "/employer/applications",
        headers=headers,
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_employer_can_access_job_quality():
    headers = get_employer_headers()

    response = client.post(
        "/job-quality/analyze",
        headers=headers,
        json={
            "title": "Python Backend Developer",
            "description": (
                "Build and maintain backend APIs using "
                "Python and FastAPI."
            ),
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

    assert response.status_code == 200

    data = response.json()

    assert "quality" in data


def test_employer_cannot_access_admin_analytics():
    headers = get_employer_headers()

    response = client.get(
        "/admin/analytics",
        headers=headers,
    )

    assert response.status_code == 403


def test_employer_cannot_access_candidate_profile():
    headers = get_employer_headers()

    response = client.get(
        "/candidate/profile",
        headers=headers,
    )

    assert response.status_code == 403


def test_employer_status_update_creates_history_and_notification():
    headers = get_employer_headers()

    db = SessionLocal()

    application_id = None
    old_status = None
    candidate_user_id = None
    new_status = None

    try:
        employer = (
            db.query(User)
            .filter(
                User.email == "rahul.hr@techcorp.com",
                User.role == "EMPLOYER_USER",
            )
            .first()
        )

        assert employer is not None

        employer_profile = (
            db.query(EmployerUser)
            .filter(EmployerUser.user_id == employer.id)
            .first()
        )

        assert employer_profile is not None

        application = (
            db.query(Application)
            .join(Job, Application.job_id == Job.id)
            .filter(
                Job.company_id == employer_profile.company_id
            )
            .first()
        )

        assert application is not None

        application_id = application.id
        old_status = application.status
        candidate_user_id = application.candidate.user_id

        new_status = (
            "SCREENING"
            if old_status != "SCREENING"
            else "SHORTLISTED"
        )

        history_count_before = (
            db.query(ApplicationStatusHistory)
            .filter(
                ApplicationStatusHistory.application_id
                == application_id
            )
            .count()
        )

        notification_count_before = (
            db.query(NotificationItem)
            .filter(
                NotificationItem.user_id == candidate_user_id,
                NotificationItem.application_id == application_id,
            )
            .count()
        )

    finally:
        db.close()

    response = client.patch(
        f"/employer/applications/{application_id}/status",
        headers=headers,
        json={
            "status": new_status,
            "feedback": "Status workflow test",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["application_id"] == application_id
    assert data["old_status"] == old_status
    assert data["new_status"] == new_status

    db = SessionLocal()

    try:
        application = (
            db.query(Application)
            .filter(Application.id == application_id)
            .first()
        )

        assert application is not None
        assert application.status == new_status

        history_count_after = (
            db.query(ApplicationStatusHistory)
            .filter(
                ApplicationStatusHistory.application_id
                == application_id
            )
            .count()
        )

        notification_count_after = (
            db.query(NotificationItem)
            .filter(
                NotificationItem.user_id == candidate_user_id,
                NotificationItem.application_id == application_id,
            )
            .count()
        )

        assert history_count_after == history_count_before + 1
        assert notification_count_after == notification_count_before + 1

    finally:
        application = (
            db.query(Application)
            .filter(Application.id == application_id)
            .first()
        )

        if application:
            application.status = old_status

        db.query(ApplicationStatusHistory).filter(
            ApplicationStatusHistory.application_id == application_id,
            ApplicationStatusHistory.new_status == new_status,
            ApplicationStatusHistory.feedback == "Status workflow test",
        ).delete(synchronize_session=False)

        db.query(NotificationItem).filter(
            NotificationItem.application_id == application_id,
            NotificationItem.user_id == candidate_user_id,
            NotificationItem.message.contains(new_status),
        ).delete(synchronize_session=False)

        db.commit()
        db.close()



def test_employer_cannot_access_application_from_another_company():
    db = SessionLocal()

    try:
        employer = (
            db.query(User)
            .filter(
                User.email == "rahul.hr@techcorp.com",
                User.role == "EMPLOYER_USER",
            )
            .first()
        )

        assert employer is not None

        employer_profile = (
            db.query(EmployerUser)
            .filter(EmployerUser.user_id == employer.id)
            .first()
        )

        assert employer_profile is not None

        application = (
            db.query(Application)
            .join(Job, Application.job_id == Job.id)
            .filter(
                Job.company_id != employer_profile.company_id
            )
            .first()
        )

        if application is None:
            return

        application_id = application.id

    finally:
        db.close()

    headers = get_employer_headers()

    response = client.get(
        f"/employer/applications/{application_id}",
        headers=headers,
    )

    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Additional employer branch and validation tests
# ---------------------------------------------------------------------------

def test_employer_registration_rejects_duplicate_email():
    response = client.post(
        "/employer/register",
        json={
            "name": "Duplicate Employer",
            "email": "rahul.hr@techcorp.com",
            "password": "TestPassword123",
            "company_name": "Duplicate Test Company",
            "company_description": "Test company",
            "company_website": "https://example.com",
            "company_location": "Bengaluru",
            "designation": "HR",
            "role_in_company": "HR",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered"


def test_employer_registration_creates_new_company_and_user():
    email = "temporary.employer.test@example.com"
    company_name = "Temporary Employer Test Company"

    db = SessionLocal()

    try:
        existing_user = (
            db.query(User)
            .filter(User.email == email)
            .first()
        )

        existing_company = (
            db.query(
                __import__("app.database.models", fromlist=["Company"]).Company
            )
            .filter(
                __import__("app.database.models", fromlist=["Company"]).Company.name
                == company_name
            )
            .first()
        )

        if existing_user:
            employer_profile = (
                db.query(EmployerUser)
                .filter(EmployerUser.user_id == existing_user.id)
                .first()
            )

            if employer_profile:
                db.delete(employer_profile)

            db.delete(existing_user)

        if existing_company:
            db.delete(existing_company)

        db.commit()

    finally:
        db.close()

    response = client.post(
        "/employer/register",
        json={
            "name": "Temporary Employer",
            "email": email,
            "password": "TestPassword123",
            "company_name": company_name,
            "company_description": "Temporary company for testing",
            "company_website": "https://temporary.example.com",
            "company_location": "Bengaluru",
            "designation": "Recruiter",
            "role_in_company": "RECRUITER",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["message"] == "Employer registered successfully"
    assert data["user_id"] is not None
    assert data["company_id"] is not None
    assert data["employer_profile_id"] is not None

    db = SessionLocal()

    try:
        user = db.query(User).filter(User.id == data["user_id"]).first()
        company = (
            db.query(
                __import__("app.database.models", fromlist=["Company"]).Company
            )
            .filter(
                __import__("app.database.models", fromlist=["Company"]).Company.id
                == data["company_id"]
            )
            .first()
        )
        employer_profile = (
            db.query(EmployerUser)
            .filter(EmployerUser.id == data["employer_profile_id"])
            .first()
        )

        assert user is not None
        assert company is not None
        assert employer_profile is not None
        assert employer_profile.user_id == user.id
        assert employer_profile.company_id == company.id

    finally:
        if employer_profile:
            db.delete(employer_profile)

        if user:
            db.delete(user)

        if company:
            db.delete(company)

        db.commit()
        db.close()


def test_employer_registration_uses_existing_company():
    email = "temporary.existing.company@example.com"
    company_name = "TechCorp"

    db = SessionLocal()

    try:
        company = (
            __import__("app.database.models", fromlist=["Company"]).Company
        )

        existing_company = (
            db.query(company)
            .filter(company.name == company_name)
            .first()
        )

        if existing_company is None:
            existing_company = company(
                name=company_name,
                description="Temporary existing company",
            )
            db.add(existing_company)
            db.commit()
            db.refresh(existing_company)

        company_id = existing_company.id

        existing_user = (
            db.query(User)
            .filter(User.email == email)
            .first()
        )

        if existing_user:
            profile = (
                db.query(EmployerUser)
                .filter(EmployerUser.user_id == existing_user.id)
                .first()
            )

            if profile:
                db.delete(profile)

            db.delete(existing_user)
            db.commit()

    finally:
        db.close()

    response = client.post(
        "/employer/register",
        json={
            "name": "Existing Company Employer",
            "email": email,
            "password": "TestPassword123",
            "company_name": company_name,
            "company_description": "Should not replace company",
            "company_website": "https://example.com",
            "company_location": "Bengaluru",
            "designation": "HR",
            "role_in_company": "HR",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["company_id"] == company_id

    db = SessionLocal()

    try:
        user = db.query(User).filter(User.id == data["user_id"]).first()
        profile = (
            db.query(EmployerUser)
            .filter(EmployerUser.id == data["employer_profile_id"])
            .first()
        )

        assert user is not None
        assert profile is not None
        assert profile.company_id == company_id

    finally:
        if profile:
            db.delete(profile)

        if user:
            db.delete(user)

        db.commit()
        db.close()


def test_employer_application_not_found():
    headers = get_employer_headers()

    response = client.get(
        "/employer/applications/999999999",
        headers=headers,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Application not found"


def test_employer_status_rejects_invalid_status():
    headers = get_employer_headers()

    response = client.patch(
        "/employer/applications/999999999/status",
        headers=headers,
        json={
            "status": "NOT_A_REAL_STATUS",
        },
    )

    assert response.status_code == 400
    assert "Invalid status" in response.json()["detail"]


def test_employer_status_rejects_excessive_feedback():
    headers = get_employer_headers()

    response = client.patch(
        "/employer/applications/999999999/status",
        headers=headers,
        json={
            "status": "SCREENING",
            "feedback": "x" * 2001,
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Feedback cannot exceed 2000 characters"
    )


def test_employer_status_application_not_found():
    headers = get_employer_headers()

    response = client.patch(
        "/employer/applications/999999999/status",
        headers=headers,
        json={
            "status": "SCREENING",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Application not found"


def test_employer_status_same_status_without_feedback():
    headers = get_employer_headers()

    db = SessionLocal()

    try:
        employer = (
            db.query(User)
            .filter(
                User.email == "rahul.hr@techcorp.com",
                User.role == "EMPLOYER_USER",
            )
            .first()
        )

        assert employer is not None

        employer_profile = (
            db.query(EmployerUser)
            .filter(EmployerUser.user_id == employer.id)
            .first()
        )

        assert employer_profile is not None

        application = (
            db.query(Application)
            .join(Job, Application.job_id == Job.id)
            .filter(
                Job.company_id == employer_profile.company_id
            )
            .first()
        )

        assert application is not None

        application_id = application.id
        current_status = application.status

    finally:
        db.close()

    response = client.patch(
        f"/employer/applications/{application_id}/status",
        headers=headers,
        json={
            "status": current_status,
        },
    )

    assert response.status_code == 200
    assert response.json()["message"] == (
        "Application status is already set"
    )
    assert response.json()["status"] == current_status


def test_employer_candidate_list_is_accessible():
    headers = get_employer_headers()

    response = client.get(
        "/employer/candidates",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert "candidates" in data
    assert isinstance(data["candidates"], list)


def test_employer_candidate_details_missing_resume():
    headers = get_employer_headers()

    response = client.get(
        "/employer/candidates/999999999",
        headers=headers,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Candidate resume not found"


def test_employer_rank_candidates_rejects_non_list_skills():
    headers = get_employer_headers()

    response = client.post(
        "/employer/rank-candidates",
        headers=headers,
        json={
            "skills": "Python",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "skills must be a list"


def test_employer_rank_candidates_accepts_skill_list():
    headers = get_employer_headers()

    response = client.post(
        "/employer/rank-candidates",
        headers=headers,
        json={
            "skills": [
                "Python",
                "FastAPI",
            ],
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert "ranking" in data
    assert isinstance(data["ranking"], list)


def test_employer_single_application_cross_company_is_forbidden_or_hidden():
    db = SessionLocal()

    try:
        employer = (
            db.query(User)
            .filter(
                User.email == "rahul.hr@techcorp.com",
                User.role == "EMPLOYER_USER",
            )
            .first()
        )

        assert employer is not None

        employer_profile = (
            db.query(EmployerUser)
            .filter(EmployerUser.user_id == employer.id)
            .first()
        )

        assert employer_profile is not None

        application = (
            db.query(Application)
            .join(Job, Application.job_id == Job.id)
            .filter(
                Job.company_id != employer_profile.company_id
            )
            .first()
        )

        if application is None:
            return

        application_id = application.id

    finally:
        db.close()

    headers = get_employer_headers()

    response = client.get(
        f"/employer/applications/{application_id}",
        headers=headers,
    )

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "You do not have access to this application"
    )
