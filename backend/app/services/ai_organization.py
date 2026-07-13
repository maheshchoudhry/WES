"""AI Organization service — CRUD, validation, and business rules for AI employees.

Reuses the repository layer; enforces the Sprint 06 business rules (unique codes,
required role/department, manager optional only for the CEO, soft delete only).
"""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.domain.ai_enums import AIEmployeeStatus
from app.models.ai import AIKPI, AICapability, AIEmployee, AIResponsibility
from app.repositories.ai import (
    AICapabilityRepository,
    AIDepartmentRepository,
    AIEmployeeRepository,
    AIRoleRepository,
)
from app.schemas.ai import (
    AICapabilityRef,
    AIEmployeeCreate,
    AIEmployeeRead,
    AIEmployeeUpdate,
    AIKPIRead,
)


class AIOrganizationService:
    def __init__(self, db: Session):
        self.db = db
        self.employees = AIEmployeeRepository(db)
        self.departments = AIDepartmentRepository(db)
        self.roles = AIRoleRepository(db)
        self.capabilities = AICapabilityRepository(db)

    # -- serialization -----------------------------------------------------

    @staticmethod
    def serialize(emp: AIEmployee) -> AIEmployeeRead:
        role_level = emp.role.level.value if hasattr(emp.role.level, "value") else emp.role.level
        return AIEmployeeRead(
            id=emp.id,
            employee_code=emp.employee_code,
            name=emp.name,
            department_id=emp.department_id,
            department_name=emp.department.name if emp.department else None,
            role_id=emp.role_id,
            role_title=emp.role.title if emp.role else None,
            role_level=str(role_level) if emp.role else None,
            manager_id=emp.manager_id,
            manager_name=emp.manager.name if emp.manager else None,
            authority=emp.authority,
            decision_scope=emp.decision_scope,
            status=emp.status,
            version=emp.version,
            responsibilities=[r.description for r in emp.responsibilities],
            capabilities=[AICapabilityRef(code=c.code, name=c.name) for c in emp.capabilities],
            kpis=[AIKPIRead(name=k.name, target=k.target, unit=k.unit) for k in emp.kpis],
            created_at=emp.created_at,
            updated_at=emp.updated_at,
        )

    # -- reads -------------------------------------------------------------

    def get(self, employee_id: uuid.UUID) -> AIEmployeeRead:
        emp = self.employees.get(employee_id)
        if emp is None:
            raise NotFoundError(f"AI employee {employee_id} not found")
        return self.serialize(emp)

    def list(
        self,
        *,
        department_id: uuid.UUID | None = None,
        role_id: uuid.UUID | None = None,
        status: str | None = None,
        search: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[AIEmployeeRead], int]:
        items = self.employees.list_filtered(
            department_id=department_id,
            role_id=role_id,
            status=status,
            search=search,
            offset=offset,
            limit=limit,
        )
        total = self.employees.count_filtered(
            department_id=department_id, role_id=role_id, status=status, search=search
        )
        return [self.serialize(e) for e in items], total

    # -- helpers -----------------------------------------------------------

    def _resolve_capabilities(self, codes: list[str]) -> list[AICapability]:
        codes = [c.strip().lower() for c in codes if c and c.strip()]
        existing = {c.code: c for c in self.capabilities.get_by_codes(codes)}
        result: list[AICapability] = []
        for code in dict.fromkeys(codes):  # de-dupe, preserve order
            cap = existing.get(code)
            if cap is None:
                cap = AICapability(code=code, name=code.replace("_", " ").title())
                self.db.add(cap)
                self.db.flush()
                existing[code] = cap
            result.append(cap)
        return result

    def _validate_manager(self, role, manager_id: uuid.UUID | None, self_id: uuid.UUID | None):
        if manager_id is None:
            if not role.is_executive_head:
                raise ValidationError("A reporting manager is required (only the CEO may omit it)")
            return
        if self_id is not None and manager_id == self_id:
            raise ValidationError("An AI employee cannot report to itself")
        if self.employees.get(manager_id) is None:
            raise ValidationError(f"Manager {manager_id} does not exist")

    def _apply_children(self, emp: AIEmployee, payload) -> None:
        if getattr(payload, "responsibilities", None) is not None:
            emp.responsibilities = [
                AIResponsibility(description=d.strip(), position=i)
                for i, d in enumerate(payload.responsibilities)
                if d and d.strip()
            ]
        if getattr(payload, "capabilities", None) is not None:
            emp.capabilities = self._resolve_capabilities(payload.capabilities)
        if getattr(payload, "kpis", None) is not None:
            emp.kpis = [
                AIKPI(name=k.name.strip(), target=k.target, unit=k.unit) for k in payload.kpis
            ]

    # -- writes ------------------------------------------------------------

    def create(self, payload: AIEmployeeCreate) -> AIEmployeeRead:
        if self.employees.get_by_code(payload.employee_code):
            raise ConflictError(f"AI employee code '{payload.employee_code}' already exists")
        role = self.roles.get(payload.role_id)
        if role is None:
            raise ValidationError(f"AI role {payload.role_id} does not exist")
        if self.departments.get(payload.department_id) is None:
            raise ValidationError(f"AI department {payload.department_id} does not exist")
        self._validate_manager(role, payload.manager_id, None)

        emp = AIEmployee(
            employee_code=payload.employee_code,
            name=payload.name,
            department_id=payload.department_id,
            role_id=payload.role_id,
            manager_id=payload.manager_id,
            authority=payload.authority,
            decision_scope=payload.decision_scope,
            status=payload.status,
            version=1,
        )
        self.db.add(emp)
        self.db.flush()
        self._apply_children(emp, payload)
        self.db.flush()
        return self.get(emp.id)

    def update(self, employee_id: uuid.UUID, payload: AIEmployeeUpdate) -> AIEmployeeRead:
        emp = self.employees.get(employee_id)
        if emp is None:
            raise NotFoundError(f"AI employee {employee_id} not found")

        data = payload.model_dump(exclude_unset=True)

        if "role_id" in data and data["role_id"] is not None:
            if self.roles.get(data["role_id"]) is None:
                raise ValidationError(f"AI role {data['role_id']} does not exist")
            emp.role_id = data["role_id"]
        if "department_id" in data and data["department_id"] is not None:
            if self.departments.get(data["department_id"]) is None:
                raise ValidationError(f"AI department {data['department_id']} does not exist")
            emp.department_id = data["department_id"]
        if "manager_id" in data:
            role = self.roles.get(emp.role_id)
            self._validate_manager(role, data["manager_id"], emp.id)
            emp.manager_id = data["manager_id"]

        for field in ("name", "authority", "decision_scope", "status"):
            if field in data and data[field] is not None:
                setattr(emp, field, data[field])

        self._apply_children(emp, payload)
        emp.version += 1
        self.db.flush()
        return self.get(emp.id)

    def delete(self, employee_id: uuid.UUID) -> None:
        """Soft delete: archive the employee and promote its direct reports."""
        emp = self.employees.get(employee_id)
        if emp is None:
            raise NotFoundError(f"AI employee {employee_id} not found")
        # Promote direct reports to the deleted employee's manager (keep the chain).
        reports = self.employees.list_filtered(limit=10_000)
        for r in reports:
            if r.manager_id == emp.id:
                r.manager_id = emp.manager_id
        emp.is_deleted = True
        emp.status = AIEmployeeStatus.ARCHIVED
        emp.version += 1
        self.db.flush()
