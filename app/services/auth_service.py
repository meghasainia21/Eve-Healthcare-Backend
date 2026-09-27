from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.schemas.auth import LoginRequest, SignupRequest
from app.utils.exceptions import ConflictError, UnauthorizedError


def signup(db: Session, payload: SignupRequest) -> User:
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing is not None:
        raise ConflictError("An account with this email already exists")

    user = User(
        name=payload.name,
        email=payload.email,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        # Second line of defense against a race between the check above and
        # the insert (two signups with the same email at the same instant).
        db.rollback()
        raise ConflictError("An account with this email already exists") from exc

    db.refresh(user)
    return user


def login(db: Session, payload: LoginRequest) -> tuple[User, str]:
    user = db.query(User).filter(User.email == payload.email).first()
    if user is None or not verify_password(payload.password, user.password_hash):
        # Deliberately identical message for "no such user" and "wrong
        # password" so we don't leak which emails are registered.
        raise UnauthorizedError("Invalid email or password")

    token = create_access_token(subject=str(user.id))
    return user, token
