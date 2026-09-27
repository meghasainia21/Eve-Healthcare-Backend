from datetime import datetime, timezone

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class DiagnosticTest(Base):
    __tablename__ = "diagnostic_tests"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    offerings = relationship(
        "CenterTestOffering", back_populates="test", cascade="all, delete-orphan"
    )
    bookings = relationship("Booking", back_populates="test")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<DiagnosticTest id={self.id} name={self.name!r}>"
