from fastapi.testclient import TestClient

from app.auth.token import create_access_token
from app.database.database import SessionLocal
from app.database.models import (
    CandidateProfile,
    TalentPoolEntry,
    User,
)
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


def get_candidate_id():
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

        assert user is not None

        candidate = (
            db.query(CandidateProfile)
            .filter(
                CandidateProfile.user_id == user.id
            )
            .first()
        )

        assert candidate is not None

        return candidate.id

    finally:
        db.close()


def test_talent_pool_requires_authentication():
    response = client.get("/talent-pool/")

    assert response.status_code in {401, 403}


def test_candidate_cannot_access_talent_pool():
    headers = get_headers(
        "arjun.test@example.com",
        "JOB_SEEKER",
    )

    response = client.get(
        "/talent-pool/",
        headers=headers,
    )

    assert response.status_code == 403


def test_employer_can_list_talent_pool():
    headers = get_headers(
        "rahul.hr@techcorp.com",
        "EMPLOYER_USER",
    )

    response = client.get(
        "/talent-pool/",
        headers=headers,
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_employer_can_add_update_and_delete_talent_pool_entry():
    headers = get_headers(
        "rahul.hr@techcorp.com",
        "EMPLOYER_USER",
    )

    candidate_id = get_candidate_id()

    # Remove any previous test entry for this candidate.
    db = SessionLocal()

    try:
        employer = get_user(
            "rahul.hr@techcorp.com",
            "EMPLOYER_USER",
        )

        existing = (
            db.query(TalentPoolEntry)
            .filter(
                TalentPoolEntry.employer_user_id == employer.id,
                TalentPoolEntry.candidate_id == candidate_id,
            )
            .all()
        )

        for entry in existing:
            db.delete(entry)

        db.commit()

    finally:
        db.close()

    # Add candidate.
    response = client.post(
        "/talent-pool/",
        headers=headers,
        json={
            "candidate_id": candidate_id,
            "notes": "Strong backend candidate.",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["message"] == "Candidate added to talent pool"
    assert data["candidate_id"] == candidate_id
    assert data["notes"] == "Strong backend candidate."

    entry_id = data["id"]

    # Duplicate should be rejected.
    duplicate_response = client.post(
        "/talent-pool/",
        headers=headers,
        json={
            "candidate_id": candidate_id,
            "notes": "Duplicate test.",
        },
    )

    assert duplicate_response.status_code == 409
    assert duplicate_response.json()["detail"] == (
        "Candidate is already in your talent pool"
    )

    # Update notes.
    update_response = client.patch(
        f"/talent-pool/{entry_id}",
        headers=headers,
        json={
            "notes": "Updated candidate assessment.",
        },
    )

    assert update_response.status_code == 200

    updated_data = update_response.json()

    assert updated_data["id"] == entry_id
    assert updated_data["notes"] == (
        "Updated candidate assessment."
    )

    # Delete entry.
    delete_response = client.delete(
        f"/talent-pool/{entry_id}",
        headers=headers,
    )

    assert delete_response.status_code == 200
    assert delete_response.json()["message"] == (
        "Candidate removed from talent pool"
    )

    # Verify it is gone.
    db = SessionLocal()

    try:
        deleted_entry = (
            db.query(TalentPoolEntry)
            .filter(
                TalentPoolEntry.id == entry_id
            )
            .first()
        )

        assert deleted_entry is None

    finally:
        db.close()
