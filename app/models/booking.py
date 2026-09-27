import enum
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class BookingStatus(str, enum.Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    center_id: Mapped[int] = mapped_column(
        ForeignKey("diagnostic_centers.id"), nullable=False, index=True
    )
    test_id: Mapped[int] = mapped_column(
        ForeignKey("diagnostic_tests.id"), nullable=False, index=True
    )

    appointment_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    # Snapshot of the offering price at booking time - see CenterTestOffering.
    # This is authoritative and never trusts client input.
    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    status: Mapped[BookingStatus] = mapped_column(
        Enum(BookingStatus, name="booking_status"),
        default=BookingStatus.PENDING,
        nullable=False,
        index=True,
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

    user = relationship("User", back_populates="bookings")
    center = relationship("DiagnosticCenter", back_populates="bookings")
    test = relationship("DiagnosticTest", back_populates="bookings")
    payments = relationship("Payment", back_populates="booking", cascade="all, delete-orphan")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Booking id={self.id} user_id={self.user_id} status={self.status}>"
