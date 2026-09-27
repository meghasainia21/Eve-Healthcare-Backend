from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.booking import BookingStatus


class BookingCreate(BaseModel):
    """
    Note there is no `amount` field here on purpose: the price is always
    derived server-side from the centre's offering for the requested test.
    """

    center_id: int
    test_id: int
    appointment_at: datetime


class BookingOut(BaseModel):
    id: int
    user_id: int
    center_id: int
    test_id: int
    appointment_at: datetime
    amount: Decimal
    status: BookingStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaginatedBookings(BaseModel):
    total: int
    skip: int
    limit: int
    items: list[BookingOut]
