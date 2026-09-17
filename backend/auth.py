"""
auth.py — Password hashing, JWT utilities, Pydantic schemas, and the
          reusable get_current_user() FastAPI dependency.
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from pydantic import BaseModel, EmailStr, field_validator
from sqlalchemy.orm import Session

from database import get_db
from models import User

# ============================================================
# CONFIGURATION  (loaded from environment / .env)
# ============================================================

JWT_SECRET_KEY: str = os.getenv(
    "JWT_SECRET_KEY",
    "change-this-to-a-strong-random-secret-before-production",
)
JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
    os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "10080")  # default 7 days
)

# ============================================================
# PASSWORD HASHING  (using bcrypt directly — avoids passlib 1.7.4 compat issues)
# ============================================================

import bcrypt as _bcrypt_lib


def hash_password(plain: str) -> str:
    """Return a bcrypt hash of *plain* (work factor 12)."""
    return _bcrypt_lib.hashpw(
        plain.encode("utf-8"),
        _bcrypt_lib.gensalt(rounds=12),
    ).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Return True if *plain* matches the stored *hashed* value."""
    return _bcrypt_lib.checkpw(
        plain.encode("utf-8"),
        hashed.encode("utf-8"),
    )


# ============================================================
# JWT
# ============================================================

def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Encode *data* as a signed JWT with an expiry claim."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    """
    Decode and verify *token*.

    Raises ``JWTError`` (from python-jose) when the token is invalid or
    expired — callers should convert this to an HTTP 401.
    """
    return jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])


# ============================================================
# PYDANTIC SCHEMAS
# ============================================================

class UserCreate(BaseModel):
    """Payload accepted by POST /auth/signup."""

    name: str
    email: EmailStr
    password: str

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Name must not be empty.")
        if len(v) > 120:
            raise ValueError("Name must be 120 characters or fewer.")
        return v

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long.")
        return v


class UserLogin(BaseModel):
    """Payload accepted by POST /auth/login."""

    email: EmailStr
    password: str


class UserOut(BaseModel):
    """Safe user representation returned from API endpoints (no password)."""

    id: int
    name: str
    email: str

    model_config = {"from_attributes": True}


class Token(BaseModel):
    """Response returned by POST /auth/login."""

    access_token: str
    token_type: str = "bearer"


# ============================================================
# AUTH DEPENDENCY
# ============================================================

_bearer_scheme = HTTPBearer(auto_error=False)

_CREDENTIALS_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials. Please log in again.",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    FastAPI dependency.

    Reads the Bearer token from the Authorization header, validates the JWT,
    looks up the corresponding user, and returns the User ORM object.

    Raises HTTP 401 for any invalid / missing / expired token.
    """
    if credentials is None or not credentials.credentials:
        raise _CREDENTIALS_EXCEPTION

    token = credentials.credentials

    try:
        payload = decode_access_token(token)
        user_id: Optional[int] = payload.get("sub")
        if user_id is None:
            raise _CREDENTIALS_EXCEPTION
    except JWTError:
        raise _CREDENTIALS_EXCEPTION

    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise _CREDENTIALS_EXCEPTION

    return user
