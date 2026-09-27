"""
Single import point that pulls in every model so Alembic's autogenerate
(and `Base.metadata.create_all` in tests) can see the full schema.

Alembic's `env.py` imports `Base` from this module — nothing else.
"""

from app.db.database import Base  # noqa: F401

from app.models.user import User  # noqa: F401
from app.models.diagnostic_center import DiagnosticCenter  # noqa: F401
from app.models.diagnostic_test import DiagnosticTest  # noqa: F401
from app.models.center_test_offering import CenterTestOffering  # noqa: F401
from app.models.booking import Booking  # noqa: F401
from app.models.payment import Payment, WebhookEvent  # noqa: F401
