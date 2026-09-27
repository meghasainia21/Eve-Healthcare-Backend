from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


# ---------- Diagnostic Test ----------


class DiagnosticTestCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None


class DiagnosticTestOut(BaseModel):
    id: int
    name: str
    description: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------- Centre <-> Test offering (pricing) ----------


class OfferingCreate(BaseModel):
    test_id: int
    price: Decimal = Field(gt=0, decimal_places=2)


class OfferingOut(BaseModel):
    test_id: int
    test_name: str
    price: Decimal

    model_config = ConfigDict(from_attributes=True)


# ---------- Diagnostic Centre ----------


class DiagnosticCenterCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    location: str = Field(min_length=1, max_length=255)
    offerings: list[OfferingCreate] = Field(default_factory=list)


class DiagnosticCenterOut(BaseModel):
    id: int
    name: str
    location: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DiagnosticCenterDetailOut(DiagnosticCenterOut):
    tests: list[OfferingOut] = Field(default_factory=list)


class PaginatedCenters(BaseModel):
    total: int
    skip: int
    limit: int
    items: list[DiagnosticCenterOut]
