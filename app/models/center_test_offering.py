from sqlalchemy import ForeignKey, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class CenterTestOffering(Base):
    """
    The authoritative link between a centre and a test, carrying the price
    that centre charges for that test.

    This is the single source of truth for booking amounts: a client can
    ask to book (center_id, test_id) but can never dictate the price -
    the server always looks it up here.
    """

    __tablename__ = "center_test_offerings"
    __table_args__ = (
        UniqueConstraint("center_id", "test_id", name="uq_center_test_offering"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    center_id: Mapped[int] = mapped_column(
        ForeignKey("diagnostic_centers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    test_id: Mapped[int] = mapped_column(
        ForeignKey("diagnostic_tests.id", ondelete="CASCADE"), nullable=False, index=True
    )
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)

    center = relationship("DiagnosticCenter", back_populates="offerings")
    test = relationship("DiagnosticTest", back_populates="offerings")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<CenterTestOffering center_id={self.center_id} test_id={self.test_id} price={self.price}>"
