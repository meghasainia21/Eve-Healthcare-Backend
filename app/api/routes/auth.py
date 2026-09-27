from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, SignupRequest, TokenResponse, UserOut
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/signup",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user account",
    responses={409: {"description": "Email already registered"}},
)
def signup(payload: SignupRequest, db: Session = Depends(get_db)) -> UserOut:
    user = auth_service.signup(db, payload)
    return user


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Log in and receive a JWT access token",
    responses={401: {"description": "Invalid email or password"}},
)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user, token = auth_service.login(db, payload)
    return TokenResponse(access_token=token, user=UserOut.model_validate(user))


@router.get(
    "/me",
    response_model=UserOut,
    summary="Get the currently authenticated user",
    responses={401: {"description": "Missing or invalid token"}},
)
def read_current_user(current_user: User = Depends(get_current_user)) -> UserOut:
    return current_user
