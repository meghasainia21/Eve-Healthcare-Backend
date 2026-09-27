from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import TokenError, decode_access_token
from app.db.database import get_db
from app.models.user import User, UserRole
from app.utils.exceptions import ForbiddenError, UnauthorizedError

# `auto_error=False` lets us raise our own consistent 401 (with our JSON
# error shape) instead of FastAPI's default "Not authenticated" body.
bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None or not credentials.credentials:
        raise UnauthorizedError("Missing authentication token")

    try:
        payload = decode_access_token(credentials.credentials)
    except TokenError as exc:
        raise UnauthorizedError(str(exc)) from exc

    user_id = payload.get("sub")
    if user_id is None:
        raise UnauthorizedError("Invalid token payload")

    user = db.get(User, int(user_id))
    if user is None:
        raise UnauthorizedError("User no longer exists")

    return user


def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.ADMIN:
        raise ForbiddenError("Admin privileges required for this action")
    return current_user
