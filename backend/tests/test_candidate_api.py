from fastapi.testclient import TestClient

from app.auth.token import create_access_token
from app.database.database import SessionLocal
from app.database.models import (
    Job,
    User,
)
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


def test_candidate_profile_requires_authentication():
    response = client.get("/candidate/profile")

    assert response.status_code in {401, 403}


def test_candidate_applications_requires_authentication():
    response = client.get("/candidate/applications")

    assert response.status_code in {401, 403}


def test_candidate_profile_is_accessible_to_candidate():
    headers = get_candidate_headers()

    response = client.get(
        "/candidate/profile",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["email"] == "arjun.test@example.com"


def test_candidate_applications_are_accessible_to_candidate():
    headers = get_candidate_headers()

    response = client.get(
        "/candidate/applications",
        headers=headers,
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_candidate_cannot_access_admin_analytics():
    headers = get_candidate_headers()

    response = client.get(
        "/admin/analytics",
        headers=headers,
    )

    assert response.status_code == 403


def test_candidate_cannot_create_job():
    headers = get_candidate_headers()

    response = client.post(
        "/jobs/",
        headers=headers,
        json={
            "title": "Unauthorized Test Job",
            "description": "This job must not be created.",
            "location": "Bengaluru",
            "salary": "₹5,00,000",
            "experience": "1-3 years",
            "employment_type": "Full-time",
            "skills": ["Python"],
        },
    )

    assert response.status_code == 403


def test_candidate_can_apply_to_active_job():
    db = SessionLocal()

    try:
        from app.database.models import Job

        job = (
            db.query(Job)
            .filter(Job.status == "ACTIVE")
            .order_by(Job.id.asc())
            .first()
        )

        assert job is not None, "Expected at least one active job."

        job_id = job.id

    finally:
        db.close()

    headers = get_candidate_headers()

    response = client.post(
        "/candidate/apply",
        headers=headers,
        json={
            "job_id": job_id,
        },
    )

    assert response.status_code in {200, 201, 409}

    if response.status_code == 409:
        assert response.json()["detail"] == (
            "You have already applied to this job"
        )
        return

    data = response.json()

    assert data["message"] == "Application submitted successfully"
    assert data["application_id"] is not None
    assert data["job_id"] == job_id
    assert data["status"] == "APPLIED"


def test_application_creates_history_and_employer_notification():
    from app.database.models import (
        Application,
        ApplicationStatusHistory,
        Company,
        EmployerUser,
        NotificationItem,
    )

    db = SessionLocal()

    try:
        candidate_user = get_existing_candidate()

        assert candidate_user is not None

        candidate = (
            db.query(__import__(
                "app.database.models",
                fromlist=["CandidateProfile"]
            ).CandidateProfile)
            .filter(
                __import__(
                    "app.database.models",
                    fromlist=["CandidateProfile"]
                ).CandidateProfile.user_id == candidate_user.id
            )
            .first()
        )

        assert candidate is not None

        employer_profile = (
            db.query(EmployerUser)
            .filter(
                EmployerUser.company_id.isnot(None)
            )
            .first()
        )

        assert employer_profile is not None

        company = (
            db.query(Company)
            .filter(
                Company.id == employer_profile.company_id
            )
            .first()
        )

        assert company is not None

        from app.database.models import Skill

        test_job = Job(
            company_id=company.id,
            employer_id=employer_profile.id,
            title="Automated Application Workflow Test",
            description="Temporary job used for automated testing.",
            location="Bengaluru",
            salary="Test",
            experience="Test",
            employment_type="Full-time",
            status="ACTIVE",
        )

        skill = (
            db.query(Skill)
            .filter(Skill.name == "Python")
            .first()
        )

        if skill:
            test_job.skills = [skill]

        db.add(test_job)
        db.commit()
        db.refresh(test_job)

        job_id = test_job.id

    finally:
        db.close()

    headers = get_candidate_headers()

    response = client.post(
        "/candidate/apply",
        headers=headers,
        json={
            "job_id": job_id,
        },
    )

    assert response.status_code in {200, 201}

    application_id = response.json()["application_id"]

    db = SessionLocal()

    try:
        application = (
            db.query(Application)
            .filter(Application.id == application_id)
            .first()
        )

        assert application is not None
        assert application.status == "APPLIED"
        assert application.job_id == job_id

        history = (
            db.query(ApplicationStatusHistory)
            .filter(
                ApplicationStatusHistory.application_id
                == application_id
            )
            .first()
        )

        assert history is not None
        assert history.new_status == "APPLIED"

        notification = (
            db.query(NotificationItem)
            .filter(
                NotificationItem.application_id
                == application_id
            )
            .first()
        )

        assert notification is not None
        assert notification.notification_type == "APPLICATION"

    finally:
        db.close()

        # Clean up the temporary test data.
        db = SessionLocal()

        try:
            application = (
                db.query(Application)
                .filter(Application.id == application_id)
                .first()
            )

            if application:
                db.delete(application)

            history_records = (
                db.query(ApplicationStatusHistory)
                .filter(
                    ApplicationStatusHistory.application_id
                    == application_id
                )
                .all()
            )

            for record in history_records:
                db.delete(record)

            notifications = (
                db.query(NotificationItem)
                .filter(
                    NotificationItem.application_id
                    == application_id
                )
                .all()
            )

            for notification in notifications:
                db.delete(notification)

            test_job = (
                db.query(Job)
                .filter(Job.id == job_id)
                .first()
            )

            if test_job:
                db.delete(test_job)

            db.commit()

        finally:
            db.close()



def test_candidate_cannot_apply_to_same_job_twice():
    from app.database.models import (
        Application,
        CandidateProfile,
        Company,
        EmployerUser,
        Skill,
    )

    db = SessionLocal()

    job_id = None
    application_id = None
    candidate_id = None

    try:
        candidate_user = get_existing_candidate()

        assert candidate_user is not None

        candidate = (
            db.query(CandidateProfile)
            .filter(
                CandidateProfile.user_id == candidate_user.id
            )
            .first()
        )

        assert candidate is not None

        candidate_id = candidate.id

        employer_profile = (
            db.query(EmployerUser)
            .filter(
                EmployerUser.company_id.isnot(None)
            )
            .first()
        )

        assert employer_profile is not None

        company = (
            db.query(Company)
            .filter(
                Company.id == employer_profile.company_id
            )
            .first()
        )

        assert company is not None

        test_job = Job(
            company_id=company.id,
            employer_id=employer_profile.id,
            title="Duplicate Application Test Job",
            description="Temporary job for duplicate application testing.",
            location="Bengaluru",
            salary="Test",
            experience="Test",
            employment_type="Full-time",
            status="ACTIVE",
        )

        skill = (
            db.query(Skill)
            .filter(Skill.name == "Python")
            .first()
        )

        if skill:
            test_job.skills = [skill]

        db.add(test_job)
        db.commit()
        db.refresh(test_job)

        job_id = test_job.id

    finally:
        db.close()

    headers = get_candidate_headers()

    first_response = client.post(
        "/candidate/apply",
        headers=headers,
        json={"job_id": job_id},
    )

    assert first_response.status_code in {200, 201}

    application_id = first_response.json()["application_id"]

    second_response = client.post(
        "/candidate/apply",
        headers=headers,
        json={"job_id": job_id},
    )

    assert second_response.status_code == 409

    assert second_response.json()["detail"] == (
        "You have already applied to this job"
    )

    db = SessionLocal()

    try:
        application_count = (
            db.query(Application)
            .filter(
                Application.job_id == job_id,
                Application.candidate_id == candidate_id,
            )
            .count()
        )

        assert application_count == 1

    finally:
        from app.database.models import (
            ApplicationStatusHistory,
            NotificationItem,
        )

        db.query(NotificationItem).filter(
            NotificationItem.application_id == application_id
        ).delete(synchronize_session=False)

        db.query(ApplicationStatusHistory).filter(
            ApplicationStatusHistory.application_id == application_id
        ).delete(synchronize_session=False)

        application = (
            db.query(Application)
            .filter(Application.id == application_id)
            .first()
        )

        if application:
            db.delete(application)

        test_job = (
            db.query(Job)
            .filter(Job.id == job_id)
            .first()
        )

        if test_job:
            db.delete(test_job)

        db.commit()
        db.close()


def test_candidate_registration_rejects_duplicate_email():
    response = client.post(
        "/candidate/register",
        json={
            "name": "Duplicate Candidate",
            "email": "arjun.test@example.com",
            "password": "TestPassword123",
        },
    )

    assert response.status_code == 400
    assert "already registered" in response.json()["detail"].lower()


def test_candidate_profile_can_be_updated():
    headers = get_candidate_headers()

    response = client.put(
        "/candidate/profile",
        headers=headers,
        json={
            "phone": "9876543210",
            "location": "Bengaluru",
            "bio": "Updated candidate profile for testing.",
        },
    )

    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, dict)


def test_candidate_cannot_apply_to_nonexistent_job():
    headers = get_candidate_headers()

    response = client.post(
        "/candidate/apply",
        headers=headers,
        json={
            "job_id": 999999999,
        },
    )

    assert response.status_code == 404


def test_candidate_cannot_apply_to_inactive_job():
    from app.database.models import Company, EmployerUser

    db = SessionLocal()
    job_id = None

    try:
        employer_profile = (
            db.query(EmployerUser)
            .filter(EmployerUser.company_id.isnot(None))
            .first()
        )

        assert employer_profile is not None

        company = (
            db.query(Company)
            .filter(Company.id == employer_profile.company_id)
            .first()
        )

        assert company is not None

        test_job = Job(
            company_id=company.id,
            employer_id=employer_profile.id,
            title="Inactive Candidate Application Test",
            description="Temporary inactive job.",
            location="Bengaluru",
            salary="Test",
            experience="Test",
            employment_type="Full-time",
            status="CLOSED",
        )

        db.add(test_job)
        db.commit()
        db.refresh(test_job)

        job_id = test_job.id

    finally:
        db.close()

    headers = get_candidate_headers()

    response = client.post(
        "/candidate/apply",
        headers=headers,
        json={
            "job_id": job_id,
        },
    )

    assert response.status_code == 400

    data = response.json()
    assert "no longer accepting" in data["detail"].lower()

    db = SessionLocal()

    try:
        test_job = (
            db.query(Job)
            .filter(Job.id == job_id)
            .first()
        )

        if test_job:
            db.delete(test_job)

        db.commit()

    finally:
        db.close()


def test_candidate_cannot_apply_with_nonexistent_resume():
    from app.database.models import Company, EmployerUser

    db = SessionLocal()
    job_id = None

    try:
        employer_profile = (
            db.query(EmployerUser)
            .filter(EmployerUser.company_id.isnot(None))
            .first()
        )

        assert employer_profile is not None

        company = (
            db.query(Company)
            .filter(Company.id == employer_profile.company_id)
            .first()
        )

        assert company is not None

        test_job = Job(
            company_id=company.id,
            employer_id=employer_profile.id,
            title="Invalid Resume Test Job",
            description="Temporary job for resume validation testing.",
            location="Bengaluru",
            salary="Test",
            experience="Test",
            employment_type="Full-time",
            status="ACTIVE",
        )

        db.add(test_job)
        db.commit()
        db.refresh(test_job)

        job_id = test_job.id

    finally:
        db.close()

    headers = get_candidate_headers()

    response = client.post(
        "/candidate/apply",
        headers=headers,
        json={
            "job_id": job_id,
            "resume_id": 999999999,
        },
    )

    assert response.status_code == 404

    db = SessionLocal()

    try:
        test_job = (
            db.query(Job)
            .filter(Job.id == job_id)
            .first()
        )

        if test_job:
            db.delete(test_job)

        db.commit()

    finally:
        db.close()


def test_candidate_career_fit_requires_authentication():
    response = client.get("/candidate/jobs/999999999/fit")

    assert response.status_code in {401, 403}


def test_candidate_career_fit_returns_404_for_nonexistent_job():
    headers = get_candidate_headers()

    response = client.get(
        "/candidate/jobs/999999999/fit",
        headers=headers,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Job not found"


def test_candidate_career_fit_requires_processed_resume():
    from app.database.models import (
        CandidateProfile,
        Company,
        EmployerUser,
        Resume,
    )

    db = SessionLocal()

    job_id = None
    candidate_id = None
    original_resume_text = []

    try:
        candidate_user = get_existing_candidate()

        assert candidate_user is not None

        candidate = (
            db.query(CandidateProfile)
            .filter(
                CandidateProfile.user_id == candidate_user.id
            )
            .first()
        )

        assert candidate is not None

        candidate_id = candidate.id

        resumes = (
            db.query(Resume)
            .filter(Resume.candidate_id == candidate_id)
            .all()
        )

        for resume in resumes:
            original_resume_text.append(
                (resume.id, resume.extracted_text)
            )
            resume.extracted_text = None

        employer_profile = (
            db.query(EmployerUser)
            .filter(EmployerUser.company_id.isnot(None))
            .first()
        )

        assert employer_profile is not None

        company = (
            db.query(Company)
            .filter(
                Company.id == employer_profile.company_id
            )
            .first()
        )

        assert company is not None

        test_job = Job(
            company_id=company.id,
            employer_id=employer_profile.id,
            title="Career Fit Resume Test Job",
            description="Temporary job for career fit testing.",
            location="Bengaluru",
            salary="Test",
            experience="1-3 years",
            employment_type="Full-time",
            status="ACTIVE",
        )

        db.add(test_job)
        db.commit()
        db.refresh(test_job)

        job_id = test_job.id

    finally:
        db.close()

    try:
        headers = get_candidate_headers()

        response = client.get(
            f"/candidate/jobs/{job_id}/fit",
            headers=headers,
        )

        assert response.status_code == 404
        assert response.json()["detail"] == (
            "No processed resume found. Upload a resume first."
        )

    finally:
        db = SessionLocal()

        try:
            for resume_id, extracted_text in original_resume_text:
                resume = (
                    db.query(Resume)
                    .filter(Resume.id == resume_id)
                    .first()
                )

                if resume:
                    resume.extracted_text = extracted_text

            if job_id is not None:
                test_job = (
                    db.query(Job)
                    .filter(Job.id == job_id)
                    .first()
                )

                if test_job:
                    db.delete(test_job)

            db.commit()

        finally:
            db.close()


def test_candidate_career_fit_returns_analysis():
    from app.database.models import (
        CandidateProfile,
        Company,
        EmployerUser,
        Skill,
    )

    db = SessionLocal()
    job_id = None

    try:
        candidate_user = get_existing_candidate()

        assert candidate_user is not None

        candidate = (
            db.query(CandidateProfile)
            .filter(
                CandidateProfile.user_id == candidate_user.id
            )
            .first()
        )

        assert candidate is not None

        employer_profile = (
            db.query(EmployerUser)
            .filter(EmployerUser.company_id.isnot(None))
            .first()
        )

        assert employer_profile is not None

        company = (
            db.query(Company)
            .filter(
                Company.id == employer_profile.company_id
            )
            .first()
        )

        assert company is not None

        test_job = Job(
            company_id=company.id,
            employer_id=employer_profile.id,
            title="Python Backend Developer Career Fit Test",
            description=(
                "Build backend applications using Python and FastAPI. "
                "Work with SQL databases and Git."
            ),
            location="Bengaluru",
            salary="Test",
            experience="1-3 years",
            employment_type="Full-time",
            status="ACTIVE",
        )

        python_skill = (
            db.query(Skill)
            .filter(Skill.name == "Python")
            .first()
        )

        fastapi_skill = (
            db.query(Skill)
            .filter(Skill.name == "FastAPI")
            .first()
        )

        sql_skill = (
            db.query(Skill)
            .filter(Skill.name == "SQL")
            .first()
        )

        skills = [
            skill
            for skill in (
                python_skill,
                fastapi_skill,
                sql_skill,
            )
            if skill is not None
        ]

        if skills:
            test_job.skills = skills

        db.add(test_job)
        db.commit()
        db.refresh(test_job)

        job_id = test_job.id

    finally:
        db.close()

    headers = get_candidate_headers()

    response = client.get(
        f"/candidate/jobs/{job_id}/fit",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["job_id"] == job_id
    assert data["job_title"] == (
        "Python Backend Developer Career Fit Test"
    )
    assert data["resume_id"] is not None

    assert "fit" in data
    assert isinstance(data["fit"], dict)

    fit = data["fit"]

    assert "score" in fit
    assert "readiness" in fit
    assert "matching_skills" in fit
    assert "missing_skills" in fit
    assert "recommendations" in fit

    assert isinstance(fit["score"], (int, float))
    assert isinstance(fit["matching_skills"], list)
    assert isinstance(fit["missing_skills"], list)
    assert isinstance(fit["recommendations"], list)

    db = SessionLocal()

    try:
        test_job = (
            db.query(Job)
            .filter(Job.id == job_id)
            .first()
        )

        if test_job:
            db.delete(test_job)

        db.commit()

    finally:
        db.close()
