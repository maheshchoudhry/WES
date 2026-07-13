"""Unit tests for the service layer (business rules and validation)."""

import uuid

import pytest

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.schemas.company import CompanyCreate, CompanyUpdate
from app.schemas.department import DepartmentCreate
from app.schemas.employee import EmployeeCreate
from app.services.company import CompanyService
from app.services.department import DepartmentService
from app.services.employee import EmployeeService


def _company(db):
    return CompanyService(db).create(
        CompanyCreate(name="WES", slug="wes", company_type="AI Company")
    )


# --- Company ---------------------------------------------------------------


def test_create_company_persists(db_session):
    company = _company(db_session)
    assert company.id is not None
    assert company.slug == "wes"


def test_duplicate_slug_conflicts(db_session):
    _company(db_session)
    with pytest.raises(ConflictError):
        CompanyService(db_session).create(
            CompanyCreate(name="Other", slug="wes", company_type="AI")
        )


def test_get_missing_company_raises_not_found(db_session):
    with pytest.raises(NotFoundError):
        CompanyService(db_session).get(uuid.uuid4())


def test_update_company(db_session):
    company = _company(db_session)
    updated = CompanyService(db_session).update(
        company.id, CompanyUpdate(company_type="Studio")
    )
    assert updated.company_type == "Studio"


def test_delete_company_with_departments_conflicts(db_session):
    company = _company(db_session)
    DepartmentService(db_session).create(
        DepartmentCreate(company_id=company.id, code="DEPT-01", name="Product")
    )
    with pytest.raises(ConflictError):
        CompanyService(db_session).delete(company.id)


# --- Department ------------------------------------------------------------


def test_department_requires_existing_company(db_session):
    with pytest.raises(ValidationError):
        DepartmentService(db_session).create(
            DepartmentCreate(company_id=uuid.uuid4(), code="DEPT-01", name="Product")
        )


def test_duplicate_department_code_conflicts(db_session):
    company = _company(db_session)
    svc = DepartmentService(db_session)
    svc.create(DepartmentCreate(company_id=company.id, code="DEPT-01", name="Product"))
    with pytest.raises(ConflictError):
        svc.create(DepartmentCreate(company_id=company.id, code="DEPT-01", name="Design"))


def test_department_code_uppercased(db_session):
    company = _company(db_session)
    dept = DepartmentService(db_session).create(
        DepartmentCreate(company_id=company.id, code="dept-02", name="Engineering")
    )
    assert dept.code == "DEPT-02"


# --- Employee --------------------------------------------------------------


def _employee_payload(company_id, **overrides):
    data = dict(
        company_id=company_id,
        employee_code="WES-EMP-006",
        full_name="Backend Engineer",
        email="be@wes.studio",
        position="Backend Engineer",
    )
    data.update(overrides)
    return EmployeeCreate(**data)


def test_register_employee(db_session):
    company = _company(db_session)
    emp = EmployeeService(db_session).register(_employee_payload(company.id))
    assert emp.employee_code == "WES-EMP-006"
    assert emp.department_id is None


def test_duplicate_employee_email_conflicts(db_session):
    company = _company(db_session)
    svc = EmployeeService(db_session)
    svc.register(_employee_payload(company.id))
    with pytest.raises(ConflictError):
        svc.register(_employee_payload(company.id, employee_code="WES-EMP-007"))


def test_assign_department_from_other_company_fails(db_session):
    company_a = _company(db_session)
    company_b = CompanyService(db_session).create(
        CompanyCreate(name="Other", slug="other", company_type="AI")
    )
    dept_b = DepartmentService(db_session).create(
        DepartmentCreate(company_id=company_b.id, code="DEPT-01", name="Product")
    )
    emp = EmployeeService(db_session).register(_employee_payload(company_a.id))
    with pytest.raises(ValidationError):
        EmployeeService(db_session).assign_department(emp.id, dept_b.id)


def test_employee_cannot_report_to_self(db_session):
    from app.schemas.employee import EmployeeUpdate

    company = _company(db_session)
    emp = EmployeeService(db_session).register(_employee_payload(company.id))
    with pytest.raises(ValidationError):
        EmployeeService(db_session).update(emp.id, EmployeeUpdate(reports_to_id=emp.id))
