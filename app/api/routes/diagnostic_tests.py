from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin
from app.db.database import get_db
from app.models.user import User
from app.schemas.diagnostic import DiagnosticTestCreate, DiagnosticTestOut
from app.services import diagnostic_service

router = APIRouter(prefix="/diagnostic-tests", tags=["Diagnostic Tests"])


@router.get("", response_model=list[DiagnosticTestOut], summary="List all diagnostic tests")
def list_tests(db: Session = Depends(get_db)) -> list[DiagnosticTestOut]:
    return diagnostic_service.list_tests(db)


@router.post(
    "",
    response_model=DiagnosticTestOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a diagnostic test (admin only)",
    responses={403: {"description": "Admin privileges required"}, 409: {"description": "Test already exists"}},
)
def create_test(
    payload: DiagnosticTestCreate,
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin),
) -> DiagnosticTestOut:
    return diagnostic_service.create_test(db, payload)
