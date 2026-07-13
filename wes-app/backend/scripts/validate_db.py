"""CI smoke check: create/read/delete a Company against the configured database.

Validates real persistence (used in CI against PostgreSQL).
"""
from __future__ import annotations

from app.db.session import SessionLocal
from app.models import Company


def main() -> None:
    db = SessionLocal()
    try:
        company = Company(name="CI Smoke Co")
        db.add(company)
        db.commit()
        db.refresh(company)
        assert company.id is not None

        fetched = db.get(Company, company.id)
        assert fetched is not None
        assert fetched.name == "CI Smoke Co"

        db.delete(fetched)
        db.commit()
        assert db.get(Company, company.id) is None
        print(f"DB validation OK (create/read/delete) against {db.bind.url}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
