from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.schemas.payment import PaymentCreate, PaymentOut, WebhookPayload, WebhookResponse
from app.services import payment_service, webhook_service

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post(
    "",
    response_model=PaymentOut,
    status_code=status.HTTP_201_CREATED,
    summary="Simulate a payment attempt for a booking",
    responses={
        400: {"description": "Booking is not payable (not PENDING)"},
        403: {"description": "Not your booking"},
        404: {"description": "Booking not found"},
    },
)
def create_payment(
    payload: PaymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PaymentOut:
    return payment_service.create_payment(db, current_user, payload)


@router.post(
    "/webhook",
    response_model=WebhookResponse,
    summary="Receive a payment-status webhook from the (simulated) provider",
    description=(
        "Idempotent by `event_id`: redelivering the same event is always "
        "safe and never creates duplicate payments or bookings. "
        "This endpoint intentionally requires no authentication, mirroring "
        "how real payment providers call webhooks (they'd instead sign the "
        "payload, which is noted as a 'trade-off' in the README)."
    ),
    responses={404: {"description": "Unknown booking_id"}},
)
def payment_webhook(payload: WebhookPayload, db: Session = Depends(get_db)) -> WebhookResponse:
    return webhook_service.process_webhook(db, payload)


@router.get(
    "/{payment_id}",
    response_model=PaymentOut,
    summary="Get a single payment (owner or admin only)",
    responses={403: {"description": "Not your payment"}, 404: {"description": "Payment not found"}},
)
def get_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PaymentOut:
    return payment_service.get_payment_or_error(db, payment_id, current_user)
