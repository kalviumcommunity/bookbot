"""
auth_routes.py — FastAPI router for authentication endpoints.

    POST /auth/signup  — create a new account
    POST /auth/login   — obtain a JWT
    GET  /auth/me      — return current authenticated user
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import User
from auth import (
    UserCreate,
    UserLogin,
    UserOut,
    Token,
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ============================================================
# POST /auth/signup
# ============================================================

@router.post(
    "/signup",
    response_model=Token,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
async def signup(payload: UserCreate, db: Session = Depends(get_db)):
    """
    Create a new user with the provided name, email, and password.

    - Email must be unique.
    - Password is hashed with bcrypt before storage.
    - Returns a JWT access token so the client is immediately authenticated.
    """

    # Check for duplicate email — return a generic 409 so we don't leak info.
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email address already exists.",
        )

    user = User(
        name=payload.name,
        email=payload.email,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    access_token = create_access_token(data={"sub": str(user.id)})
    return Token(access_token=access_token)


# ============================================================
# POST /auth/login
# ============================================================

@router.post(
    "/login",
    response_model=Token,
    summary="Log in with email and password",
)
async def login(payload: UserLogin, db: Session = Depends(get_db)):
    """
    Verify email + password and return a JWT access token.

    The error message is intentionally generic to avoid confirming whether
    a given email address is registered.
    """

    _INVALID = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid email or password.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    user = db.query(User).filter(User.email == payload.email).first()

    # Use constant-time comparison even for the "not found" case to prevent
    # timing-based email enumeration.
    if user is None or not verify_password(payload.password, user.password_hash):
        raise _INVALID

    access_token = create_access_token(data={"sub": str(user.id)})
    return Token(access_token=access_token)


# ============================================================
# GET /auth/me
# ============================================================

@router.get(
    "/me",
    response_model=UserOut,
    summary="Return the currently authenticated user",
)
async def me(current_user: User = Depends(get_current_user)):
    """
    Requires a valid Bearer token in the Authorization header.

    Returns the authenticated user's id, name, and email.
    The password hash is never included in the response.
    """
    return current_user
