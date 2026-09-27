import pytest
from sqlalchemy.exc import IntegrityError

from app.models.booking import Booking
from app.models.center_test_offering import CenterTestOffering
from app.models.diagnostic_center import DiagnosticCenter
from app.models.diagnostic_test import DiagnosticTest
from app.models.payment import Payment, PaymentStatus, WebhookEvent
from app.models.user import User


def test_user_email_unique_constraint(db_session):
    db_session.add(User(name="A", email="dup@example.com", password_hash="x"))
    db_session.commit()

    db_session.add(User(name="B", email="dup@example.com", password_hash="y"))
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_center_test_offering_unique_constraint(db_session):
    center = DiagnosticCenter(name="C1", location="L1")
    test = DiagnosticTest(name="T1")
    db_session.add_all([center, test])
    db_session.flush()

    db_session.add(CenterTestOffering(center_id=center.id, test_id=test.id, price=100))
    db_session.commit()

    # Same (center, test) pair again must violate the unique constraint -
    # this is what stops a centre from having two conflicting prices for
    # the same test.
    db_session.add(CenterTestOffering(center_id=center.id, test_id=test.id, price=200))
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_webhook_event_id_unique_constraint(db_session):
    user = User(name="U", email="u1@example.com", password_hash="x")
    center = DiagnosticCenter(name="C1", location="L1")
    test = DiagnosticTest(name="T1")
    db_session.add_all([user, center, test])
    db_session.flush()

    booking = Booking(
        user_id=user.id,
        center_id=center.id,
        test_id=test.id,
        appointment_at="2099-01-01T00:00:00+00:00",
        amount=100,
    )
    db_session.add(booking)
    db_session.flush()

    db_session.add(
        WebhookEvent(
            event_id="evt_x",
            booking_id=booking.id,
            provider_payment_id="pay_x",
            status=PaymentStatus.SUCCESS,
        )
    )
    db_session.commit()

    # The row that actually enforces webhook idempotency at the DB level.
    db_session.add(
        WebhookEvent(
            event_id="evt_x",
            booking_id=booking.id,
            provider_payment_id="pay_y",
            status=PaymentStatus.SUCCESS,
        )
    )
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_payment_provider_id_unique_constraint(db_session):
    user = User(name="U", email="u2@example.com", password_hash="x")
    center = DiagnosticCenter(name="C1", location="L1")
    test = DiagnosticTest(name="T1")
    db_session.add_all([user, center, test])
    db_session.flush()

    booking = Booking(
        user_id=user.id,
        center_id=center.id,
        test_id=test.id,
        appointment_at="2099-01-01T00:00:00+00:00",
        amount=100,
    )
    db_session.add(booking)
    db_session.flush()

    db_session.add(
        Payment(booking_id=booking.id, provider_payment_id="pay_dup", amount=100, status=PaymentStatus.SUCCESS)
    )
    db_session.commit()

    db_session.add(
        Payment(booking_id=booking.id, provider_payment_id="pay_dup", amount=100, status=PaymentStatus.SUCCESS)
    )
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_booking_cascade_delete_with_user(db_session):
    """Deleting a user cascades to their bookings (ondelete=CASCADE)."""
    user = User(name="U", email="u3@example.com", password_hash="x")
    center = DiagnosticCenter(name="C1", location="L1")
    test = DiagnosticTest(name="T1")
    db_session.add_all([user, center, test])
    db_session.flush()

    booking = Booking(
        user_id=user.id,
        center_id=center.id,
        test_id=test.id,
        appointment_at="2099-01-01T00:00:00+00:00",
        amount=100,
    )
    db_session.add(booking)
    db_session.commit()
    booking_id = booking.id

    db_session.delete(user)
    db_session.commit()

    assert db_session.get(Booking, booking_id) is None


def test_booking_requires_valid_foreign_keys(db_session):
    """A booking pointing at a non-existent user must fail at the DB level."""
    center = DiagnosticCenter(name="C1", location="L1")
    test = DiagnosticTest(name="T1")
    db_session.add_all([center, test])
    db_session.flush()

    booking = Booking(
        user_id=999999,
        center_id=center.id,
        test_id=test.id,
        appointment_at="2099-01-01T00:00:00+00:00",
        amount=100,
    )
    db_session.add(booking)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()
