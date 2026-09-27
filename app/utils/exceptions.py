"""
A small set of domain exceptions that map cleanly onto HTTP status codes.

Routes/services raise these instead of `HTTPException` directly in most
places, so business logic doesn't need to know about FastAPI, and the
mapping to status codes lives in one place (`app.main`'s exception
handlers).
"""


class AppError(Exception):
    status_code = 400

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class NotFoundError(AppError):
    status_code = 404


class ForbiddenError(AppError):
    status_code = 403


class UnauthorizedError(AppError):
    status_code = 401


class ConflictError(AppError):
    status_code = 409


class BadRequestError(AppError):
    """Invalid request / business-rule violation -> HTTP 400."""

    status_code = 400


class ValidationAppError(AppError):
    """Reserved for semantic validation errors we want to surface as 422."""

    status_code = 422
