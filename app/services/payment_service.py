import uuid

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.booking import Booking, BookingStatus
from app.models.payment import Payment, PaymentStatus
from app.models.user import User
from app.schemas.payment import PaymentCreate
from app.utils.exceptions import BadRequestError, ForbiddenError, NotFoundError


def _simulate_provider_outcome(booking: Booking, simulate_status: PaymentStatus | None) -> PaymentStatus:
    """
    Stand-in for a real payment gateway call.

    In production this would be an HTTP call to a provider (Stripe/Razorpay/
    etc). Here we simulate it deterministically so behaviour is testable:
    - a caller (e.g. a test) may force the outcome via `simulate_status`
    - otherwise we derive the outcome from the booking id so the same
      booking always produces the same simulated result, instead of being
      flaky/random in tests and demos.
    """
    if simulate_status is not None:
        return simulate_status
    return PaymentStatus.FAILED if booking.id % 10 == 0 else PaymentStatus.SUCCESS


def create_payment(db: Session, user: User, payload: PaymentCreate) -> Payment:
    booking = db.get(Booking, payload.booking_id)
    if booking is None:
        raise NotFoundError(f"Booking {payload.booking_id} not found")

    if booking.user_id != user.id and user.role.value != "ADMIN":
        raise ForbiddenError("You do not have access to this booking")

    if booking.status != BookingStatus.PENDING:
        # Covers: duplicate payment attempts, paying for an already
        # confirmed/failed/cancelled booking.
        raise BadRequestError(
            f"Booking {booking.id} is '{booking.status.value}' and is not payable "
            "(only PENDING bookings can be paid for)"
        )

    outcome = _simulate_provider_outcome(booking, payload.simulate_status)
    provider_payment_id = f"pay_{uuid.uuid4().hex[:16]}"

    # The amount is *always* read from the booking (server-side), never from
    # the request body - this is the same rule as at booking-creation time.
    payment = Payment(
        booking_id=booking.id,
        provider_payment_id=provider_payment_id,
        amount=booking.amount,
        status=outcome,
    )
    booking.status = BookingStatus.CONFIRMED if outcome == PaymentStatus.SUCCESS else BookingStatus.FAILED

    db.add(payment)
    try:
        db.commit()
    except IntegrityError as exc:  # pragma: no cover - astronomically unlikely uuid collision
        db.rollback()
        raise BadRequestError("Could not process payment, please retry") from exc

    db.refresh(payment)
    return payment


def get_payment_or_error(db: Session, payment_id: int, user: User) -> Payment:
    payment = db.get(Payment, payment_id)
    if payment is None:
        raise NotFoundError(f"Payment {payment_id} not found")
    if payment.booking.user_id != user.id and user.role.value != "ADMIN":
        raise ForbiddenError("You do not have access to this payment")
    return payment
