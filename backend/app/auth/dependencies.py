from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.auth.token import verify_access_token
from app.database.database import get_db
from app.database.models import User

security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
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
            detail="Invalid authentication token",
        )

    try:
        user_id = int(user_id)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=401,
            detail="Invalid user identity",
        )

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=401,
            detail="User account not found",
        )

    return user


def require_candidate(
    user: User = Depends(get_current_user),
) -> User:
    if user.role != "JOB_SEEKER":
        raise HTTPException(
            status_code=403,
            detail="Candidate access required",
        )

    return user


def require_employer(
    user: User = Depends(get_current_user),
) -> User:
    if user.role != "EMPLOYER_USER":
        raise HTTPException(
            status_code=403,
            detail="Employer access required",
        )

    return user


def require_admin(
    user: User = Depends(get_current_user),
) -> User:
    if user.role != "ADMIN":
        raise HTTPException(
            status_code=403,
            detail="Admin access required",
        )

    return user
