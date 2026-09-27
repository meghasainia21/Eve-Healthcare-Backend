"""
Populate the database with realistic demo data: a couple of diagnostic
centres, a handful of tests, centre-specific pricing, and demo users
(one admin, one regular user).

Usage:
    python -m scripts.seed_data

Safe to re-run: it skips creating rows that already exist (matched by
unique fields), so it won't create duplicates if you run it twice.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.security import hash_password
from app.db.base import Base
from app.db.database import SessionLocal, engine
from app.models.center_test_offering import CenterTestOffering
from app.models.diagnostic_center import DiagnosticCenter
from app.models.diagnostic_test import DiagnosticTest
from app.models.user import User, UserRole

DEMO_USERS = [
    {"name": "Admin User", "email": "admin@eve-healthcare.com", "password": "AdminPass123", "role": UserRole.ADMIN},
    {"name": "Asha Verma", "email": "asha@example.com", "password": "UserPass123", "role": UserRole.USER},
]

DEMO_TESTS = [
    {"name": "Complete Blood Count (CBC)", "description": "Measures red/white blood cells and platelets"},
    {"name": "Lipid Profile", "description": "Cholesterol and triglyceride levels"},
    {"name": "Thyroid Profile (T3, T4, TSH)", "description": "Thyroid hormone levels"},
    {"name": "HbA1c", "description": "3-month average blood sugar level"},
    {"name": "Liver Function Test (LFT)", "description": "Assesses liver enzymes and function"},
]

DEMO_CENTERS = [
    {
        "name": "MediCore Diagnostics - MG Road",
        "location": "MG Road, Bengaluru",
        "prices": {
            "Complete Blood Count (CBC)": 350,
            "Lipid Profile": 600,
            "Thyroid Profile (T3, T4, TSH)": 750,
            "HbA1c": 450,
        },
    },
    {
        "name": "HealthFirst Labs - Andheri",
        "location": "Andheri West, Mumbai",
        "prices": {
            "Complete Blood Count (CBC)": 300,
            "Lipid Profile": 550,
            "Liver Function Test (LFT)": 700,
            "HbA1c": 400,
        },
    },
    {
        "name": "CarePlus Diagnostic Centre - Connaught Place",
        "location": "Connaught Place, New Delhi",
        "prices": {
            "Thyroid Profile (T3, T4, TSH)": 800,
            "Liver Function Test (LFT)": 650,
            "Complete Blood Count (CBC)": 320,
        },
    },
]


def seed() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        print("Seeding users...")
        for u in DEMO_USERS:
            if db.query(User).filter(User.email == u["email"]).first():
                continue
            db.add(
                User(
                    name=u["name"],
                    email=u["email"],
                    password_hash=hash_password(u["password"]),
                    role=u["role"],
                )
            )
        db.commit()

        print("Seeding diagnostic tests...")
        test_by_name: dict[str, DiagnosticTest] = {}
        for t in DEMO_TESTS:
            existing = db.query(DiagnosticTest).filter(DiagnosticTest.name == t["name"]).first()
            if existing is None:
                existing = DiagnosticTest(name=t["name"], description=t["description"])
                db.add(existing)
                db.flush()
            test_by_name[t["name"]] = existing
        db.commit()

        print("Seeding diagnostic centres and pricing...")
        for c in DEMO_CENTERS:
            center = db.query(DiagnosticCenter).filter(DiagnosticCenter.name == c["name"]).first()
            if center is None:
                center = DiagnosticCenter(name=c["name"], location=c["location"])
                db.add(center)
                db.flush()

            for test_name, price in c["prices"].items():
                test = test_by_name[test_name]
                exists = (
                    db.query(CenterTestOffering)
                    .filter(
                        CenterTestOffering.center_id == center.id,
                        CenterTestOffering.test_id == test.id,
                    )
                    .first()
                )
                if exists is None:
                    db.add(CenterTestOffering(center_id=center.id, test_id=test.id, price=price))
        db.commit()

        print("\nSeed complete.")
        print("Demo credentials:")
        for u in DEMO_USERS:
            print(f"  - {u['role'].value:<6} email={u['email']:<28} password={u['password']}")

    finally:
        db.close()


if __name__ == "__main__":
    seed()
