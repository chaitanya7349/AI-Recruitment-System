from fastapi.testclient import TestClient

from app.auth.token import create_access_token
from app.database.database import SessionLocal
from app.database.models import NotificationItem, User
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


def create_test_notification(user_id: int):
    db = SessionLocal()

    try:
        notification = NotificationItem(
            user_id=user_id,
            title="Automated Test Notification",
            message="Notification created for API testing.",
            notification_type="TEST",
            is_read=False,
        )

        db.add(notification)
        db.commit()
        db.refresh(notification)

        return notification.id

    finally:
        db.close()


def delete_test_notification(notification_id: int):
    db = SessionLocal()

    try:
        notification = (
            db.query(NotificationItem)
            .filter(NotificationItem.id == notification_id)
            .first()
        )

        if notification:
            db.delete(notification)
            db.commit()

    finally:
        db.close()


def test_notifications_require_authentication():
    response = client.get("/notifications/")

    assert response.status_code in {401, 403}


def test_candidate_can_get_notifications():
    headers = get_headers(
        "arjun.test@example.com",
        "JOB_SEEKER",
    )

    response = client.get(
        "/notifications/",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert "unread_count" in data
    assert "notifications" in data
    assert isinstance(data["notifications"], list)


def test_employer_can_get_notifications():
    headers = get_headers(
        "rahul.hr@techcorp.com",
        "EMPLOYER_USER",
    )

    response = client.get(
        "/notifications/",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert "unread_count" in data
    assert "notifications" in data


def test_user_can_mark_notification_as_read():
    user = get_user(
        "rahul.hr@techcorp.com",
        "EMPLOYER_USER",
    )

    assert user is not None

    notification_id = create_test_notification(user.id)

    try:
        headers = get_headers(
            "rahul.hr@techcorp.com",
            "EMPLOYER_USER",
        )

        response = client.patch(
            f"/notifications/{notification_id}/read",
            headers=headers,
        )

        assert response.status_code == 200
        assert response.json()["message"] == (
            "Notification marked as read."
        )

        db = SessionLocal()

        try:
            notification = (
                db.query(NotificationItem)
                .filter(
                    NotificationItem.id == notification_id
                )
                .first()
            )

            assert notification is not None
            assert notification.is_read is True

        finally:
            db.close()

    finally:
        delete_test_notification(notification_id)


def test_user_cannot_mark_another_users_notification_as_read():
    employer = get_user(
        "rahul.hr@techcorp.com",
        "EMPLOYER_USER",
    )

    candidate = get_user(
        "arjun.test@example.com",
        "JOB_SEEKER",
    )

    assert employer is not None
    assert candidate is not None

    notification_id = create_test_notification(
        employer.id
    )

    try:
        candidate_headers = get_headers(
            "arjun.test@example.com",
            "JOB_SEEKER",
        )

        response = client.patch(
            f"/notifications/{notification_id}/read",
            headers=candidate_headers,
        )

        assert response.status_code == 404

    finally:
        delete_test_notification(notification_id)


def test_mark_all_notifications_read():
    user = get_user(
        "rahul.hr@techcorp.com",
        "EMPLOYER_USER",
    )

    assert user is not None

    db = SessionLocal()

    notification_ids = []

    try:
        for index in range(2):
            notification = NotificationItem(
                user_id=user.id,
                title=f"Bulk Test Notification {index}",
                message="Notification created for bulk read testing.",
                notification_type="TEST",
                is_read=False,
            )

            db.add(notification)
            db.flush()

            notification_ids.append(notification.id)

        db.commit()

    finally:
        db.close()

    try:
        headers = get_headers(
            "rahul.hr@techcorp.com",
            "EMPLOYER_USER",
        )

        response = client.patch(
            "/notifications/read-all",
            headers=headers,
        )

        assert response.status_code == 200
        assert response.json()["message"] == (
            "All notifications marked as read."
        )

        db = SessionLocal()

        try:
            unread_count = (
                db.query(NotificationItem)
                .filter(
                    NotificationItem.user_id == user.id,
                    NotificationItem.id.in_(notification_ids),
                    NotificationItem.is_read == False,
                )
                .count()
            )

            assert unread_count == 0

        finally:
            db.close()

    finally:
        db = SessionLocal()

        try:
            for notification_id in notification_ids:
                notification = (
                    db.query(NotificationItem)
                    .filter(
                        NotificationItem.id == notification_id
                    )
                    .first()
                )

                if notification:
                    db.delete(notification)

            db.commit()

        finally:
            db.close()
