from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.models.center_test_offering import CenterTestOffering
from app.models.diagnostic_center import DiagnosticCenter
from app.models.diagnostic_test import DiagnosticTest
from app.schemas.diagnostic import DiagnosticCenterCreate, DiagnosticTestCreate
from app.utils.exceptions import BadRequestError, ConflictError, NotFoundError


def create_test(db: Session, payload: DiagnosticTestCreate) -> DiagnosticTest:
    existing = db.query(DiagnosticTest).filter(DiagnosticTest.name == payload.name).first()
    if existing is not None:
        raise ConflictError(f"A diagnostic test named '{payload.name}' already exists")

    test = DiagnosticTest(name=payload.name, description=payload.description)
    db.add(test)
    db.commit()
    db.refresh(test)
    return test


def list_tests(db: Session) -> list[DiagnosticTest]:
    return db.query(DiagnosticTest).order_by(DiagnosticTest.name).all()


def create_center(db: Session, payload: DiagnosticCenterCreate) -> DiagnosticCenter:
    center = DiagnosticCenter(name=payload.name, location=payload.location)
    db.add(center)
    db.flush()  # obtain center.id without committing yet

    for offering_in in payload.offerings:
        test = db.get(DiagnosticTest, offering_in.test_id)
        if test is None:
            raise NotFoundError(f"Diagnostic test {offering_in.test_id} does not exist")
        db.add(
            CenterTestOffering(
                center_id=center.id, test_id=offering_in.test_id, price=offering_in.price
            )
        )

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ConflictError("Duplicate test offering for this centre") from exc

    db.refresh(center)
    return center


def list_centers(db: Session, skip: int = 0, limit: int = 20) -> tuple[list[DiagnosticCenter], int]:
    query = db.query(DiagnosticCenter).order_by(DiagnosticCenter.id)
    total = query.count()
    items = query.offset(skip).limit(limit).all()
    return items, total


def get_center_or_404(db: Session, center_id: int) -> DiagnosticCenter:
    center = db.get(DiagnosticCenter, center_id)
    if center is None:
        raise NotFoundError(f"Diagnostic centre {center_id} not found")
    return center


def get_center_offerings(db: Session, center_id: int) -> list[CenterTestOffering]:
    get_center_or_404(db, center_id)
    return (
        db.query(CenterTestOffering)
        .options(joinedload(CenterTestOffering.test))
        .filter(CenterTestOffering.center_id == center_id)
        .all()
    )


def get_offering_or_400(db: Session, center_id: int, test_id: int) -> CenterTestOffering:
    """
    The authoritative price lookup used by booking creation. Raises if the
    centre does not offer this test at all - this is what stops a client
    from booking an arbitrary (center, test) combination.
    """
    offering = (
        db.query(CenterTestOffering)
        .filter(
            CenterTestOffering.center_id == center_id,
            CenterTestOffering.test_id == test_id,
        )
        .first()
    )
    if offering is None:
        raise BadRequestError(
            f"Centre {center_id} does not offer test {test_id}"
        )
    return offering
