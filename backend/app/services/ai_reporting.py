"""AI Reporting service — organization chart, department view, and org summary.

Derives the reporting structure from ai_employees.manager_id (no separate table);
provides read models for the AI workspaces and the Founder Dashboard.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.repositories.ai import AIDepartmentRepository, AIEmployeeRepository, AIRoleRepository


class AIReportingService:
    def __init__(self, db: Session):
        self.db = db
        self.employees = AIEmployeeRepository(db)
        self.departments = AIDepartmentRepository(db)
        self.roles = AIRoleRepository(db)

    def _node(self, emp) -> dict:
        return {
            "id": str(emp.id),
            "employee_code": emp.employee_code,
            "name": emp.name,
            "role_title": emp.role.title if emp.role else None,
            "department_name": emp.department.name if emp.department else None,
            "authority": emp.authority.value if hasattr(emp.authority, "value") else emp.authority,
            "status": emp.status.value if hasattr(emp.status, "value") else emp.status,
            "reports": [],
        }

    def org_chart(self) -> list[dict]:
        """Return the reporting hierarchy as a nested tree (roots = no manager)."""
        employees = self.employees.list_active()
        nodes = {emp.id: self._node(emp) for emp in employees}
        roots: list[dict] = []
        for emp in employees:
            node = nodes[emp.id]
            parent = nodes.get(emp.manager_id) if emp.manager_id else None
            if parent is not None:
                parent["reports"].append(node)
            else:
                roots.append(node)
        return roots

    def department_view(self) -> list[dict]:
        """Employees grouped by AI department, with counts."""
        employees = self.employees.list_active()
        by_dept: dict = {}
        for emp in employees:
            by_dept.setdefault(emp.department_id, []).append(emp)
        result = []
        for dept in self.departments.list_all():
            members = by_dept.get(dept.id, [])
            result.append(
                {
                    "id": str(dept.id),
                    "code": dept.code,
                    "name": dept.name,
                    "focus": dept.focus,
                    "employee_count": len(members),
                    "employees": [
                        {
                            "id": str(m.id),
                            "employee_code": m.employee_code,
                            "name": m.name,
                            "role_title": m.role.title if m.role else None,
                            "authority": (
                                m.authority.value if hasattr(m.authority, "value") else m.authority
                            ),
                            "status": m.status.value if hasattr(m.status, "value") else m.status,
                        }
                        for m in members
                    ],
                }
            )
        return result

    def summary(self) -> dict:
        """AI organization summary + a simple health signal for the dashboard."""
        employees = self.employees.list_active()
        total = len(employees)
        by_status: dict[str, int] = {}
        by_department: dict[str, int] = {}
        dept_names = {d.id: d.name for d in self.departments.list_all()}
        ceo_present = False
        orphans = 0
        for emp in employees:
            st = emp.status.value if hasattr(emp.status, "value") else emp.status
            by_status[st] = by_status.get(st, 0) + 1
            dname = dept_names.get(emp.department_id, "Unknown")
            by_department[dname] = by_department.get(dname, 0) + 1
            if emp.manager_id is None:
                if emp.role and emp.role.is_executive_head:
                    ceo_present = True
                else:
                    orphans += 1

        # Health: healthy when a CEO exists, no orphaned reports, all active.
        active = by_status.get("active", 0)
        if total == 0:
            health = "empty"
        elif ceo_present and orphans == 0 and active == total:
            health = "healthy"
        elif ceo_present and orphans == 0:
            health = "degraded"
        else:
            health = "at_risk"

        return {
            "total_employees": total,
            "department_count": len(self.departments.list_all()),
            "role_count": len(self.roles.list_all()),
            "by_status": by_status,
            "by_department": by_department,
            "ceo_present": ceo_present,
            "organization_health": health,
        }
