from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.booking import Booking, BookingStatus
from app.models.diagnostic_center import DiagnosticCenter
from app.models.diagnostic_test import DiagnosticTest
from app.models.user import User
from app.schemas.booking import BookingCreate
from app.services.diagnostic_service import get_offering_or_400
from app.utils.exceptions import BadRequestError, ForbiddenError, NotFoundError


def _validate_appointment_time(appointment_at: datetime) -> None:
    now = datetime.now(timezone.utc)
    # Normalize naive datetimes (e.g. if a client sends one without tz info)
    if appointment_at.tzinfo is None:
        appointment_at = appointment_at.replace(tzinfo=timezone.utc)
    if appointment_at <= now:
        raise BadRequestError("Appointment date/time must be in the future")


def create_booking(db: Session, user: User, payload: BookingCreate) -> Booking:
    center = db.get(DiagnosticCenter, payload.center_id)
    if center is None:
        raise NotFoundError(f"Diagnostic centre {payload.center_id} not found")

    test = db.get(DiagnosticTest, payload.test_id)
    if test is None:
        raise NotFoundError(f"Diagnostic test {payload.test_id} not found")

    # Confirms the centre actually offers this test, and gets the
    # authoritative, server-side price. The client can never set the price.
    offering = get_offering_or_400(db, payload.center_id, payload.test_id)

    _validate_appointment_time(payload.appointment_at)

    booking = Booking(
        user_id=user.id,
        center_id=payload.center_id,
        test_id=payload.test_id,
        appointment_at=payload.appointment_at,
        amount=offering.price,
        status=BookingStatus.PENDING,
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking


def list_bookings_for_user(
    db: Session, user: User, skip: int = 0, limit: int = 20
) -> tuple[list[Booking], int]:
    query = db.query(Booking).filter(Booking.user_id == user.id).order_by(Booking.id.desc())
    total = query.count()
    items = query.offset(skip).limit(limit).all()
    return items, total


def get_booking_or_404(db: Session, booking_id: int) -> Booking:
    booking = db.get(Booking, booking_id)
    if booking is None:
        raise NotFoundError(f"Booking {booking_id} not found")
    return booking


def get_owned_booking_or_error(db: Session, booking_id: int, user: User) -> Booking:
    """Fetch a booking and enforce that `user` owns it (or is an admin)."""
    booking = get_booking_or_404(db, booking_id)
    if booking.user_id != user.id and user.role.value != "ADMIN":
        raise ForbiddenError("You do not have access to this booking")
    return booking


def cancel_booking(db: Session, booking_id: int, user: User) -> Booking:
    booking = get_owned_booking_or_error(db, booking_id, user)

    if booking.status == BookingStatus.CONFIRMED:
        raise BadRequestError(
            "A confirmed (paid) booking cannot be cancelled directly; contact support for a refund"
        )
    if booking.status == BookingStatus.CANCELLED:
        raise BadRequestError("Booking is already cancelled")

    booking.status = BookingStatus.CANCELLED
    db.commit()
    db.refresh(booking)
    return booking
