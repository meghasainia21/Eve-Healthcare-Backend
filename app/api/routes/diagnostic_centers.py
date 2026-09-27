from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin
from app.db.database import get_db
from app.models.user import User
from app.schemas.diagnostic import (
    DiagnosticCenterCreate,
    DiagnosticCenterDetailOut,
    DiagnosticCenterOut,
    OfferingOut,
    PaginatedCenters,
)
from app.services import diagnostic_service

router = APIRouter(prefix="/diagnostic-centers", tags=["Diagnostic Centers"])


@router.get(
    "",
    response_model=PaginatedCenters,
    summary="List diagnostic centres (public, paginated)",
)
def list_centers(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> PaginatedCenters:
    items, total = diagnostic_service.list_centers(db, skip=skip, limit=limit)
    return PaginatedCenters(total=total, skip=skip, limit=limit, items=items)


@router.post(
    "",
    response_model=DiagnosticCenterDetailOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a diagnostic centre (admin only)",
    responses={403: {"description": "Admin privileges required"}},
)
def create_center(
    payload: DiagnosticCenterCreate,
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin),
) -> DiagnosticCenterDetailOut:
    center = diagnostic_service.create_center(db, payload)
    offerings = diagnostic_service.get_center_offerings(db, center.id)
    return _to_detail(center, offerings)


@router.get(
    "/{center_id}",
    response_model=DiagnosticCenterDetailOut,
    summary="Get a diagnostic centre with the tests it offers",
    responses={404: {"description": "Centre not found"}},
)
def get_center(center_id: int, db: Session = Depends(get_db)) -> DiagnosticCenterDetailOut:
    center = diagnostic_service.get_center_or_404(db, center_id)
    offerings = diagnostic_service.get_center_offerings(db, center_id)
    return _to_detail(center, offerings)


@router.get(
    "/{center_id}/tests",
    response_model=list[OfferingOut],
    summary="List the tests (and prices) offered by a centre",
    responses={404: {"description": "Centre not found"}},
)
def get_center_tests(center_id: int, db: Session = Depends(get_db)) -> list[OfferingOut]:
    offerings = diagnostic_service.get_center_offerings(db, center_id)
    return [
        OfferingOut(test_id=o.test_id, test_name=o.test.name, price=o.price) for o in offerings
    ]


def _to_detail(center, offerings) -> DiagnosticCenterDetailOut:
    return DiagnosticCenterDetailOut(
        id=center.id,
        name=center.name,
        location=center.location,
        created_at=center.created_at,
        tests=[OfferingOut(test_id=o.test_id, test_name=o.test.name, price=o.price) for o in offerings],
    )
