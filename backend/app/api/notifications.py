from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.auth.token import verify_access_token
from app.database.database import get_db
from app.database.models import User, NotificationItem


router = APIRouter(
    prefix="/notifications",
    tags=["Notifications"],
)

security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    payload = verify_access_token(credentials.credentials)

    if not payload:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
        )

    user_id = payload.get("sub")

    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Invalid token",
        )

    user = (
        db.query(User)
        .filter(User.id == int(user_id))
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=401,
            detail="User not found",
        )

    return user


@router.get("/")
def get_notifications(
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    notifications = (
        db.query(NotificationItem)
        .filter(NotificationItem.user_id == user.id)
        .order_by(NotificationItem.created_at.desc())
        .limit(50)
        .all()
    )

    unread_count = (
        db.query(NotificationItem)
        .filter(
            NotificationItem.user_id == user.id,
            NotificationItem.is_read == False,
        )
        .count()
    )

    return {
        "unread_count": unread_count,
        "notifications": [
            {
                "id": notification.id,
                "application_id": notification.application_id,
                "title": notification.title,
                "message": notification.message,
                "notification_type": notification.notification_type,
                "is_read": notification.is_read,
                "created_at": notification.created_at,
            }
            for notification in notifications
        ],
    }


@router.patch("/{notification_id}/read")
def mark_notification_read(
    notification_id: int,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    notification = (
        db.query(NotificationItem)
        .filter(
            NotificationItem.id == notification_id,
            NotificationItem.user_id == user.id,
        )
        .first()
    )

    if not notification:
        raise HTTPException(
            status_code=404,
            detail="Notification not found",
        )

    notification.is_read = True

    db.commit()

    return {
        "message": "Notification marked as read."
    }


@router.patch("/read-all")
def mark_all_notifications_read(
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    (
        db.query(NotificationItem)
        .filter(
            NotificationItem.user_id == user.id,
            NotificationItem.is_read == False,
        )
        .update(
            {
                NotificationItem.is_read: True
            },
            synchronize_session=False,
        )
    )

    db.commit()

    return {
        "message": "All notifications marked as read."
    }
