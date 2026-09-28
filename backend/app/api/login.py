from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.auth.security import verify_password, hash_password
from app.auth.token import create_access_token

router = APIRouter()

# Temporary recruiter credentials
USERNAME = "chaitu"

# Store hashed password instead of plain text
HASHED_PASSWORD = hash_password("chaitu29")


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/login")
def login(user: LoginRequest):

    if user.username != USERNAME:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )

    if not verify_password(
        user.password,
        HASHED_PASSWORD
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )

    access_token = create_access_token(
        {"sub": user.username}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }
