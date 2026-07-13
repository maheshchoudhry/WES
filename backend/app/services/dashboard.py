"""Dashboard aggregation service.

Composes read-only views for the Executive Dashboard from existing Company Engine
data. It reuses the repository layer (the same data access used by the Company,
Department, and Employee services) and introduces no new business logic or
persistence.
"""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.orm import Session

from app import __version__
from app.models.company import Company
from app.models.department import Department
from app.models.employee import Employee
from app.repositories.company import CompanyRepository
from app.repositories.department import DepartmentRepository
from app.repositories.employee import EmployeeRepository
from app.schemas.dashboard import (
    ActivityItem,
    CompanySummary,
    Counts,
    DashboardStats,
    DepartmentStat,
    EmployeeDirectoryItem,
    SystemHealth,
)

# A single company operating model today; fetch generously to aggregate in memory.
_MAX = 10_000


class DashboardService:
    def __init__(self, db: Session):
        self.db = db
        self.companies = CompanyRepository(db)
        self.departments = DepartmentRepository(db)
        self.employees = EmployeeRepository(db)

    # -- internal loaders --------------------------------------------------

    def _primary_company(self) -> Company | None:
        companies = self.companies.list(limit=1)
        return companies[0] if companies else None

    def _all_departments(self) -> list[Department]:
        return self.departments.list(limit=_MAX)

    def _all_employees(self) -> list[Employee]:
        return self.employees.list(limit=_MAX)

    # -- public read models ------------------------------------------------

    def company_summary(self) -> CompanySummary | None:
        company = self._primary_company()
        if company is None:
            return None
        return CompanySummary(
            id=company.id,
            name=company.name,
            slug=company.slug,
            company_type=company.company_type,
            purpose=company.purpose,
            status=str(
                company.status.value if hasattr(company.status, "value") else company.status
            ),
            department_count=self.departments.count_by_company(company.id),
            employee_count=len([e for e in self._all_employees() if e.company_id == company.id]),
        )

    def stats(self) -> DashboardStats:
        departments = self._all_departments()
        employees = self._all_employees()

        def _val(x) -> str:
            return str(x.value if hasattr(x, "value") else x)

        employees_by_status: dict[str, int] = {}
        employees_by_authority: dict[str, int] = {}
        for e in employees:
            employees_by_status[_val(e.status)] = employees_by_status.get(_val(e.status), 0) + 1
            employees_by_authority[_val(e.authority)] = (
                employees_by_authority.get(_val(e.authority), 0) + 1
            )

        departments_by_status: dict[str, int] = {}
        for d in departments:
            departments_by_status[_val(d.status)] = departments_by_status.get(_val(d.status), 0) + 1

        return DashboardStats(
            company=self.company_summary(),
            totals=Counts(
                departments=len(departments), employees=len(employees), active_projects=0
            ),
            employees_by_status=employees_by_status,
            employees_by_authority=employees_by_authority,
            departments_by_status=departments_by_status,
        )

    def department_stats(self) -> list[DepartmentStat]:
        employees = self._all_employees()
        counts: dict = {}
        for e in employees:
            if e.department_id is not None:
                counts[e.department_id] = counts.get(e.department_id, 0) + 1
        result = []
        for d in self._all_departments():
            result.append(
                DepartmentStat(
                    id=d.id,
                    code=d.code,
                    name=d.name,
                    focus=d.focus,
                    status=str(d.status.value if hasattr(d.status, "value") else d.status),
                    employee_count=counts.get(d.id, 0),
                )
            )
        result.sort(key=lambda x: x.code)
        return result

    def employee_directory(self) -> list[EmployeeDirectoryItem]:
        employees = self._all_employees()
        dept_names = {d.id: d.name for d in self._all_departments()}
        emp_names = {e.id: e.full_name for e in employees}

        def _val(x) -> str:
            return str(x.value if hasattr(x, "value") else x)

        items = [
            EmployeeDirectoryItem(
                id=e.id,
                employee_code=e.employee_code,
                full_name=e.full_name,
                position=e.position,
                authority=_val(e.authority),
                status=_val(e.status),
                department_id=e.department_id,
                department_name=dept_names.get(e.department_id) if e.department_id else None,
                reports_to_id=e.reports_to_id,
                manager_name=emp_names.get(e.reports_to_id) if e.reports_to_id else None,
            )
            for e in employees
        ]
        items.sort(key=lambda x: x.employee_code)
        return items

    def recent_activity(self, limit: int = 10) -> list[ActivityItem]:
        """Derive an activity feed from entity create/update timestamps."""
        events: list[ActivityItem] = []

        def _add(entity_type: str, entity_id, label: str, created, updated) -> None:
            action = "created" if created == updated else "updated"
            events.append(
                ActivityItem(
                    entity_type=entity_type,
                    action=action,
                    entity_id=entity_id,
                    label=label,
                    timestamp=updated,
                )
            )

        company = self._primary_company()
        if company is not None:
            _add("company", company.id, company.name, company.created_at, company.updated_at)
        for d in self._all_departments():
            _add("department", d.id, f"{d.code} — {d.name}", d.created_at, d.updated_at)
        for e in self._all_employees():
            _add("employee", e.id, f"{e.employee_code} — {e.full_name}", e.created_at, e.updated_at)

        events.sort(key=lambda x: x.timestamp, reverse=True)
        return events[:limit]

    def system_health(self) -> SystemHealth:
        database = "connected"
        try:
            self.db.execute(text("SELECT 1"))
        except Exception:  # pragma: no cover - defensive
            database = "disconnected"
        return SystemHealth(
            api="ok",
            database=database,
            version=__version__,
            companies=self.companies.count(),
            departments=self.departments.count(),
            employees=self.employees.count(),
        )
