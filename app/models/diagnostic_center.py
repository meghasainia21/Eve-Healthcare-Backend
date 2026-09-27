from datetime import datetime, timezone

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class DiagnosticCenter(Base):
    __tablename__ = "diagnostic_centers"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    location: Mapped[str] = mapped_column(String(255), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    offerings = relationship(
        "CenterTestOffering", back_populates="center", cascade="all, delete-orphan"
    )
    bookings = relationship("Booking", back_populates="center")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<DiagnosticCenter id={self.id} name={self.name!r}>"
