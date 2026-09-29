from fastapi.testclient import TestClient

from app.auth.security import hash_password
from app.auth.token import create_access_token
from app.database.database import SessionLocal
from app.database.models import User
from app.main import app


client = TestClient(app)


def create_test_admin():
    db = SessionLocal()

    email = "temporary.admin.test@example.com"

    try:
        existing = (
            db.query(User)
            .filter(User.email == email)
            .first()
        )

        if existing:
            db.delete(existing)
            db.commit()

        admin = User(
            name="Temporary Admin",
            email=email,
            password_hash=hash_password("AdminTestPassword123"),
            role="ADMIN",
        )

        db.add(admin)
        db.commit()
        db.refresh(admin)

        return admin.id, admin.email, admin.role

    finally:
        db.close()


def delete_test_admin(admin_id):
    db = SessionLocal()

    try:
        admin = (
            db.query(User)
            .filter(User.id == admin_id)
            .first()
        )

        if admin:
            db.delete(admin)
            db.commit()

    finally:
        db.close()


def get_admin_headers():
    admin_id, email, role = create_test_admin()

    token = create_access_token(
        {
            "sub": str(admin_id),
            "email": email,
            "role": role,
        }
    )

    return {
        "Authorization": f"Bearer {token}"
    }, admin_id


def test_admin_analytics_requires_authentication():
    response = client.get("/admin/analytics")

    assert response.status_code in {401, 403}


def test_admin_users_requires_authentication():
    response = client.get("/admin/users")

    assert response.status_code in {401, 403}


def test_admin_analytics_is_accessible_to_admin():
    headers, admin_id = get_admin_headers()

    try:
        response = client.get(
            "/admin/analytics",
            headers=headers,
        )

        assert response.status_code == 200

        data = response.json()

        assert "total_users" in data
        assert "total_candidates" in data
        assert "total_employers" in data
        assert "total_admins" in data
        assert "total_companies" in data
        assert "total_jobs" in data
        assert "active_jobs" in data
        assert "closed_jobs" in data
        assert "total_applications" in data
        assert "application_status_counts" in data
        assert "daily_activity" in data
        assert "recent_users" in data
        assert "recent_applications" in data

        assert isinstance(data["application_status_counts"], dict)
        assert isinstance(data["daily_activity"], list)
        assert isinstance(data["recent_users"], list)
        assert isinstance(data["recent_applications"], list)

        # build_daily_analytics() always returns the previous
        # 7 calendar days including today.
        assert len(data["daily_activity"]) == 7

        for day in data["daily_activity"]:
            assert "date" in day
            assert "users" in day
            assert "jobs" in day
            assert "applications" in day

    finally:
        delete_test_admin(admin_id)


def test_admin_users_is_accessible_to_admin():
    headers, admin_id = get_admin_headers()

    try:
        response = client.get(
            "/admin/users",
            headers=headers,
        )

        assert response.status_code == 200

        data = response.json()

        assert isinstance(data, list)

        # The temporary admin should appear in the user listing.
        assert any(
            user["email"] == "temporary.admin.test@example.com"
            and user["role"] == "ADMIN"
            for user in data
        )

        for user in data:
            assert "id" in user
            assert "name" in user
            assert "email" in user
            assert "role" in user
            assert "created_at" in user

    finally:
        delete_test_admin(admin_id)


def test_employer_cannot_access_admin_users():
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
        "/admin/users",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 403


def test_candidate_cannot_access_admin_analytics():
    db = SessionLocal()

    try:
        candidate = (
            db.query(User)
            .filter(
                User.role == "JOB_SEEKER"
            )
            .first()
        )

        assert candidate is not None

        token = create_access_token(
            {
                "sub": str(candidate.id),
                "email": candidate.email,
                "role": candidate.role,
            }
        )

    finally:
        db.close()

    response = client.get(
        "/admin/analytics",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 403
