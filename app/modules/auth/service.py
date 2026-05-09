from datetime import timedelta
from sqlalchemy.sql import func
from flask_jwt_extended import create_access_token, create_refresh_token

from ...models.user import User
from ...extensions import db
from ...errors import ApiError


VALID_ROLES = ["ADMIN", "RH", "MANAGER", "EMPLOYEE"]


# =========================
# LOGIN
# =========================
def login(email: str, password: str) -> dict:
    email = email.strip().lower()

    user = User.query.filter_by(email=email).first()

    if (
        not user
        or user.status != "ACTIVE"
        or not user.check_password(password)
    ):
        raise ApiError(
            "Invalid credentials",
            status=401,
            code="invalid_credentials"
        )

    access_token = create_access_token(
        identity=str(user.id),
        additional_claims={"role": user.role},
        expires_delta=timedelta(minutes=30),
    )

    refresh_token = create_refresh_token(
        identity=str(user.id),
        additional_claims={"role": user.role},
    )

    user.last_login = func.now()
    db.session.commit()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token
    }


# =========================
# REGISTER
# =========================
def register(email: str, password: str, role: str = "EMPLOYEE") -> dict:
    email = email.strip().lower()
    role = role.strip().upper()

    if not email or not password:
        raise ApiError(
            "Missing fields",
            status=400,
            code="missing_fields"
        )

    if len(password) < 8:
        raise ApiError(
            "Weak password",
            status=400,
            code="weak_password"
        )

    # bcrypt limitation (72 bytes)
    if len(password.encode("utf-8")) > 72:
        raise ApiError(
            "Password too long",
            status=400,
            code="password_too_long"
        )

    if User.query.filter_by(email=email).first():
        raise ApiError(
            "Email already exists",
            status=409,
            code="email_exists"
        )

    if role not in VALID_ROLES:
        raise ApiError(
            "Invalid role",
            status=400,
            code="invalid_role",
            extra={"allowed": VALID_ROLES}
        )

    user = User(
        email=email,
        role=role,
        status="ACTIVE"
    )

    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    return {
        "id": user.id,
        "email": user.email,
        "role": user.role
    }