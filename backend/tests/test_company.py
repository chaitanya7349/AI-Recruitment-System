from fastapi.testclient import TestClient

from app.main import app
from app.database.database import SessionLocal
from app.database.models import Company

client = TestClient(app)


def test_get_companies():
    response = client.get("/companies/")

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)

    if data:
        company = data[0]

        assert "id" in company
        assert "name" in company
        assert "description" in company
        assert "website" in company
        assert "location" in company
        assert "active_jobs" in company


def test_get_company_details():
    db = SessionLocal()

    company = db.query(Company).first()

    if company is None:
        db.close()
        return

    company_id = company.id

    db.close()

    response = client.get(f"/companies/{company_id}")

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == company_id
    assert "name" in data
    assert "description" in data
    assert "website" in data
    assert "location" in data
    assert "active_jobs" in data
    assert "jobs" in data

    assert isinstance(data["jobs"], list)


def test_company_not_found():
    response = client.get("/companies/999999999")

    assert response.status_code == 404

    data = response.json()

    assert data["detail"] == "Company not found"


def test_company_only_returns_active_jobs():
    db = SessionLocal()

    company = db.query(Company).first()

    if company is None:
        db.close()
        return

    company_id = company.id

    db.close()

    response = client.get(f"/companies/{company_id}")

    assert response.status_code == 200

    data = response.json()

    for job in data["jobs"]:
        assert "id" in job
        assert "title" in job
        assert "location" in job
        assert "salary" in job
        assert "experience" in job
        assert "employment_type" in job
        assert "created_at" in job
