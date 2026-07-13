"""Dashboard read-model schemas.

These are aggregation/read views composed from the Company Engine data. They add
no new persistence — they reshape existing Company/Department/Employee data for
the Executive Dashboard.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel


class CompanySummary(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    company_type: str
    purpose: str | None
    status: str
    department_count: int
    employee_count: int


class Counts(BaseModel):
    departments: int
    employees: int
    active_projects: int = 0


class DashboardStats(BaseModel):
    company: CompanySummary | None
    totals: Counts
    employees_by_status: dict[str, int]
    employees_by_authority: dict[str, int]
    departments_by_status: dict[str, int]


class DepartmentStat(BaseModel):
    id: uuid.UUID
    code: str
    name: str
    focus: str | None
    status: str
    employee_count: int


class EmployeeDirectoryItem(BaseModel):
    id: uuid.UUID
    employee_code: str
    full_name: str
    position: str
    authority: str
    status: str
    department_id: uuid.UUID | None
    department_name: str | None
    reports_to_id: uuid.UUID | None
    manager_name: str | None


class ActivityItem(BaseModel):
    entity_type: str  # company | department | employee
    action: str  # created | updated
    entity_id: uuid.UUID
    label: str
    timestamp: datetime


class SystemHealth(BaseModel):
    api: str
    database: str
    version: str
    companies: int
    departments: int
    employees: int
