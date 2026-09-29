from app.auth.security import hash_password, verify_password
from app.auth.token import create_access_token, verify_access_token


def test_password_hash_is_not_plain_text():
    password = "TestPassword@123"

    hashed = hash_password(password)

    assert hashed != password
    assert hashed.startswith("$2")


def test_correct_password_is_verified():
    password = "TestPassword@123"

    hashed = hash_password(password)

    assert verify_password(password, hashed) is True


def test_wrong_password_is_rejected():
    password = "TestPassword@123"

    hashed = hash_password(password)

    assert verify_password("WrongPassword@123", hashed) is False


def test_jwt_creation_and_verification():
    payload = {
        "sub": "123",
        "email": "test@example.com",
        "role": "JOB_SEEKER",
    }

    token = create_access_token(payload)

    decoded = verify_access_token(token)

    assert decoded is not None
    assert decoded["sub"] == "123"
    assert decoded["email"] == "test@example.com"
    assert decoded["role"] == "JOB_SEEKER"


def test_invalid_jwt_is_rejected():
    decoded = verify_access_token(
        "this-is-not-a-valid-jwt"
    )

    assert decoded is None
