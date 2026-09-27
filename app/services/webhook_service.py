from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.booking import Booking, BookingStatus
from app.models.payment import Payment, PaymentStatus, WebhookEvent
from app.schemas.payment import WebhookPayload, WebhookResponse
from app.utils.exceptions import NotFoundError


def process_webhook(db: Session, payload: WebhookPayload) -> WebhookResponse:
    """
    Idempotent webhook handler.

    Idempotency strategy:
    1. `webhook_events.event_id` has a UNIQUE constraint at the database
       level. We first check for it, then attempt to insert a new row.
    2. The insert (via `flush`) is what actually enforces idempotency
       under concurrency: if two identical webhook requests arrive at the
       same time, both may pass the initial SELECT check, but only one
       INSERT can succeed - the loser gets an IntegrityError and safely
       reports "already processed" instead of double-applying the event.
    3. Only after the event row is durably recorded do we touch the
       booking/payment rows, and only if the booking is still PENDING -
       this stops an out-of-order or duplicate-in-spirit event from
       flipping a booking that has already been resolved.
    """
    existing_event = db.query(WebhookEvent).filter(WebhookEvent.event_id == payload.event_id).first()
    if existing_event is not None:
        return WebhookResponse(
            received=True, duplicate=True, message="Event already processed; no action taken"
        )

    booking = db.get(Booking, payload.booking_id)
    if booking is None:
        raise NotFoundError(f"Booking {payload.booking_id} not found")

    event = WebhookEvent(
        event_id=payload.event_id,
        booking_id=payload.booking_id,
        provider_payment_id=payload.provider_payment_id,
        status=payload.status,
    )
    db.add(event)
    try:
        # Flushing (rather than waiting for commit) forces the unique
        # constraint to be checked now, so we can catch a concurrent
        # duplicate before doing any further work in this transaction.
        db.flush()
    except IntegrityError:
        db.rollback()
        return WebhookResponse(
            received=True,
            duplicate=True,
            message="Event already processed concurrently; no action taken",
        )

    payment = (
        db.query(Payment)
        .filter(Payment.provider_payment_id == payload.provider_payment_id)
        .first()
    )
    if payment is None:
        payment = Payment(
            booking_id=booking.id,
            provider_payment_id=payload.provider_payment_id,
            amount=booking.amount,
            status=payload.status,
        )
        db.add(payment)
    else:
        payment.status = payload.status

    state_changed = False
    if booking.status == BookingStatus.PENDING:
        booking.status = (
            BookingStatus.CONFIRMED if payload.status == PaymentStatus.SUCCESS else BookingStatus.FAILED
        )
        state_changed = True

    db.commit()

    message = "Webhook processed successfully"
    if not state_changed:
        message += f" (booking was already '{booking.status.value}'; status left unchanged)"

    return WebhookResponse(received=True, duplicate=False, message=message)
