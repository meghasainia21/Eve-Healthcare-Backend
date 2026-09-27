from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.schemas.booking import BookingCreate, BookingOut, PaginatedBookings
from app.services import booking_service

router = APIRouter(prefix="/bookings", tags=["Bookings"])


@router.post(
    "",
    response_model=BookingOut,
    status_code=status.HTTP_201_CREATED,
    summary="Book a diagnostic test",
    responses={
        401: {"description": "Missing or invalid token"},
        400: {"description": "Centre does not offer this test / invalid appointment time"},
        404: {"description": "Centre or test not found"},
    },
)
def create_booking(
    payload: BookingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BookingOut:
    return booking_service.create_booking(db, current_user, payload)


@router.get(
    "",
    response_model=PaginatedBookings,
    summary="List the current user's bookings (paginated)",
)
def list_bookings(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PaginatedBookings:
    items, total = booking_service.list_bookings_for_user(db, current_user, skip=skip, limit=limit)
    return PaginatedBookings(total=total, skip=skip, limit=limit, items=items)


@router.get(
    "/{booking_id}",
    response_model=BookingOut,
    summary="Get a single booking (owner or admin only)",
    responses={403: {"description": "Not your booking"}, 404: {"description": "Booking not found"}},
)
def get_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BookingOut:
    return booking_service.get_owned_booking_or_error(db, booking_id, current_user)


@router.post(
    "/{booking_id}/cancel",
    response_model=BookingOut,
    summary="Cancel a booking (owner or admin only)",
    responses={
        403: {"description": "Not your booking"},
        404: {"description": "Booking not found"},
        400: {"description": "Booking cannot be cancelled in its current state"},
    },
)
def cancel_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BookingOut:
    return booking_service.cancel_booking(db, booking_id, current_user)
