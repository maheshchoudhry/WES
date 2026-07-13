"""Repositories for the AI Work Management engine."""

import uuid

from sqlalchemy import func, or_, select

from app.models.work import (
    ActivityLog,
    Assignment,
    Comment,
    Milestone,
    Project,
    ProjectSprint,
    WorkDependency,
    WorkItem,
)
from app.repositories.base import BaseRepository


class ProjectRepository(BaseRepository[Project]):
    model = Project

    def list_all(self, *, offset: int = 0, limit: int = 50) -> list[Project]:
        return list(
            self.db.scalars(
                select(Project).order_by(Project.code).offset(offset).limit(limit)
            ).all()
        )

    def get_by_code(self, code: str) -> Project | None:
        return self.db.scalar(select(Project).where(Project.code == code))


class MilestoneRepository(BaseRepository[Milestone]):
    model = Milestone

    def list_by_project(self, project_id: uuid.UUID) -> list[Milestone]:
        return list(
            self.db.scalars(
                select(Milestone)
                .where(Milestone.project_id == project_id)
                .order_by(Milestone.due_date)
            ).all()
        )


class SprintRepository(BaseRepository[ProjectSprint]):
    model = ProjectSprint

    def list_by_project(self, project_id: uuid.UUID) -> list[ProjectSprint]:
        return list(
            self.db.scalars(
                select(ProjectSprint)
                .where(ProjectSprint.project_id == project_id)
                .order_by(ProjectSprint.sprint_number)
            ).all()
        )

    def list_all(self) -> list[ProjectSprint]:
        return list(self.db.scalars(select(ProjectSprint)).all())


class WorkItemRepository(BaseRepository[WorkItem]):
    model = WorkItem

    def get_by_code(self, code: str) -> WorkItem | None:
        return self.db.scalar(select(WorkItem).where(WorkItem.task_code == code))

    def _filtered(
        self,
        *,
        project_id=None,
        sprint_id=None,
        status=None,
        priority=None,
        assigned_ai_employee_id=None,
        search=None,
    ):
        stmt = select(WorkItem)
        if project_id is not None:
            stmt = stmt.where(WorkItem.project_id == project_id)
        if sprint_id is not None:
            stmt = stmt.where(WorkItem.sprint_id == sprint_id)
        if status is not None:
            stmt = stmt.where(WorkItem.status == status)
        if priority is not None:
            stmt = stmt.where(WorkItem.priority == priority)
        if assigned_ai_employee_id is not None:
            stmt = stmt.where(WorkItem.assigned_ai_employee_id == assigned_ai_employee_id)
        if search:
            like = f"%{search.lower()}%"
            stmt = stmt.where(
                or_(
                    func.lower(WorkItem.title).like(like),
                    func.lower(WorkItem.task_code).like(like),
                )
            )
        return stmt

    def list_filtered(self, *, offset: int = 0, limit: int = 50, **filters) -> list[WorkItem]:
        stmt = self._filtered(**filters).order_by(WorkItem.task_code).offset(offset).limit(limit)
        return list(self.db.scalars(stmt).all())

    def count_filtered(self, **filters) -> int:
        base = self._filtered(**filters).subquery()
        return int(self.db.scalar(select(func.count()).select_from(base)) or 0)

    def list_all(self) -> list[WorkItem]:
        return list(self.db.scalars(select(WorkItem)).all())


class AssignmentRepository(BaseRepository[Assignment]):
    model = Assignment

    def list_by_work_item(self, work_item_id: uuid.UUID) -> list[Assignment]:
        return list(
            self.db.scalars(
                select(Assignment)
                .where(Assignment.work_item_id == work_item_id)
                .order_by(Assignment.created_at)
            ).all()
        )


class DependencyRepository(BaseRepository[WorkDependency]):
    model = WorkDependency

    def list_by_work_item(self, work_item_id: uuid.UUID) -> list[WorkDependency]:
        return list(
            self.db.scalars(
                select(WorkDependency).where(WorkDependency.work_item_id == work_item_id)
            ).all()
        )


class CommentRepository(BaseRepository[Comment]):
    model = Comment

    def list_by_work_item(self, work_item_id: uuid.UUID) -> list[Comment]:
        return list(
            self.db.scalars(
                select(Comment)
                .where(Comment.work_item_id == work_item_id)
                .order_by(Comment.created_at)
            ).all()
        )


class ActivityRepository(BaseRepository[ActivityLog]):
    model = ActivityLog

    def list(
        self,
        *,
        project_id: uuid.UUID | None = None,
        work_item_id: uuid.UUID | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> list[ActivityLog]:
        stmt = select(ActivityLog)
        if project_id is not None:
            stmt = stmt.where(ActivityLog.project_id == project_id)
        if work_item_id is not None:
            stmt = stmt.where(ActivityLog.work_item_id == work_item_id)
        stmt = stmt.order_by(ActivityLog.created_at.desc()).offset(offset).limit(limit)
        return list(self.db.scalars(stmt).all())

    def count(self, *, project_id=None, work_item_id=None) -> int:
        stmt = select(func.count()).select_from(ActivityLog)
        if project_id is not None:
            stmt = stmt.where(ActivityLog.project_id == project_id)
        if work_item_id is not None:
            stmt = stmt.where(ActivityLog.work_item_id == work_item_id)
        return int(self.db.scalar(stmt) or 0)
