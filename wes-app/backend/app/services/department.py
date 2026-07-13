"""Department business logic."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.department import Department
from app.repositories.department import DepartmentRepository
from app.schemas.department import DepartmentCreate, DepartmentUpdate
from app.services.exceptions import ConflictError, NotFoundError


class DepartmentService:
    def __init__(self, db: Session) -> None:
        self.repo = DepartmentRepository(db)

    def list(self, offset: int, limit: int) -> tuple[list[Department], int]:
        return self.repo.list(offset, limit), self.repo.count()

    def get(self, department_id: int) -> Department:
        obj = self.repo.get(department_id)
        if obj is None:
            raise NotFoundError("Department not found", {"id": department_id})
        return obj

    def create(self, data: DepartmentCreate) -> Department:
        if self.repo.get_by_code(data.code) is not None:
            raise ConflictError("Department code already exists", {"code": data.code})
        return self.repo.save(Department(**data.model_dump()))

    def update(self, department_id: int, data: DepartmentUpdate) -> Department:
        obj = self.get(department_id)
        payload = data.model_dump(exclude_unset=True)
        new_code = payload.get("code")
        if new_code and new_code != obj.code and self.repo.get_by_code(new_code):
            raise ConflictError("Department code already exists", {"code": new_code})
        for key, value in payload.items():
            setattr(obj, key, value)
        return self.repo.save(obj)

    def delete(self, department_id: int) -> None:
        self.repo.delete(self.get(department_id))
