from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.database.models import User
from app.auth.security import verify_password
from app.auth.token import create_access_token


router = APIRouter(
    tags=["Authentication"]
)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


@router.post("/login")
def login(
    data: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Authenticate a registered user using PostgreSQL.
    """

    user = db.query(User).filter(
        User.email == data.email
    ).first()

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    if not verify_password(
        data.password,
        user.password_hash
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    access_token = create_access_token(
        {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role
        }
    )

    return {
        "message": "Login successful",
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role
        }
    }
