import enum
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class PaymentStatus(str, enum.Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class Payment(Base):
    """
    One row per attempted payment for a booking. `provider_payment_id` is
    unique because it represents a single charge attempt from the
    (simulated) payment provider - re-processing the same provider id
    must never create a second row.
    """

    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    booking_id: Mapped[int] = mapped_column(
        ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False, index=True
    )
    provider_payment_id: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True
    )
    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus, name="payment_status"), nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    booking = relationship("Booking", back_populates="payments")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Payment id={self.id} booking_id={self.booking_id} status={self.status}>"


class WebhookEvent(Base):
    """
    Records every webhook event we have ever successfully processed,
    keyed by the provider's `event_id`.

    Idempotency strategy (explained in full in the README):
    1. On receipt, try to INSERT a row keyed by `event_id`.
    2. A unique constraint on `event_id` means a second delivery of the
       same event fails at the database level (IntegrityError), even
       under concurrent requests - this is the real source of truth,
       not an in-memory check, which would not be safe across multiple
       API workers/processes.
    3. Only after the insert succeeds do we apply the booking/payment
       side effects, inside the same transaction.
    """

    __tablename__ = "webhook_events"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    event_id: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    booking_id: Mapped[int] = mapped_column(ForeignKey("bookings.id"), nullable=False)
    provider_payment_id: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus, name="webhook_payment_status"), nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<WebhookEvent event_id={self.event_id} booking_id={self.booking_id}>"
