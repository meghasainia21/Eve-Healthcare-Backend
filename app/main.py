import logging
import time
import uuid

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.routes import auth, bookings, diagnostic_centers, diagnostic_tests, payments
from app.core.config import settings
from app.core.logging import configure_logging
from app.utils.exceptions import AppError

configure_logging(settings.LOG_LEVEL)
logger = logging.getLogger("eve_healthcare")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=(
        "Backend service for diagnostic test bookings and simulated payments. "
        "Built for the EVE Healthcare SDE Intern assignment."
    ),
    version="1.0.0",
)


# ---------------------------------------------------------------------------
# Request logging middleware - gives every request a correlation id and logs
# method/path/status/duration as structured JSON. Useful for debugging
# webhook idempotency issues in particular (you can trace an event_id).
# ---------------------------------------------------------------------------
@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = str(uuid.uuid4())
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = round((time.perf_counter() - start) * 1000, 2)
    logger.info(
        "request_handled",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": duration_ms,
        },
    )
    response.headers["X-Request-ID"] = request_id
    return response


# ---------------------------------------------------------------------------
# Consistent JSON error responses.
# ---------------------------------------------------------------------------
@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"error": exc.message})


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"error": "Validation failed", "details": exc.errors()},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("unhandled_exception", extra={"path": request.url.path})
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "An unexpected error occurred"},
    )


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(auth.router)
app.include_router(diagnostic_centers.router)
app.include_router(diagnostic_tests.router)
app.include_router(bookings.router)
app.include_router(payments.router)


@app.get("/health", tags=["Health"], summary="Liveness/readiness probe")
def health_check() -> dict:
    return {"status": "ok"}


@app.get("/", tags=["Health"], summary="Root")
def root() -> dict:
    return {
        "service": settings.PROJECT_NAME,
        "docs": "/docs",
        "health": "/health",
    }
