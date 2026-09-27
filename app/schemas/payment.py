from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.payment import PaymentStatus


class PaymentCreate(BaseModel):
    booking_id: int
    # Optional and only meant for tests/demos: forces the simulated outcome
    # instead of the deterministic default derived from the booking id.
    # A real integration would remove this field entirely.
    simulate_status: PaymentStatus | None = None


class PaymentOut(BaseModel):
    id: int
    booking_id: int
    provider_payment_id: str
    amount: Decimal
    status: PaymentStatus
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WebhookPayload(BaseModel):
    """
    Payload shape sent by the (simulated) payment provider.

    `event_id` is the provider's unique identifier for *this specific
    notification* - it is what makes the webhook idempotent, and is
    distinct from `provider_payment_id`, which identifies the underlying
    charge (a provider could in theory redeliver the same event_id, or
    send multiple events for one charge; we key idempotency off event_id
    since that's what "the same webhook delivered twice" means).
    """

    event_id: str = Field(min_length=1, max_length=128)
    provider_payment_id: str = Field(min_length=1, max_length=64)
    booking_id: int
    status: PaymentStatus


class WebhookResponse(BaseModel):
    received: bool
    duplicate: bool
    message: str
