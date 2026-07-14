"""Shared API dependencies (pagination, service providers, auth/RBAC)."""

import uuid
from dataclasses import dataclass

from fastapi import Depends, Query, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import ForbiddenError
from app.domain.roles import Permission, Role, role_has_permission
from app.services.auth import AuthError, AuthService
from app.services.company import CompanyService
from app.services.department import DepartmentService
from app.services.employee import EmployeeService


@dataclass
class Pagination:
    offset: int
    limit: int


def pagination(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
) -> Pagination:
    return Pagination(offset=(page - 1) * page_size, limit=page_size)


def get_company_service(db: Session = Depends(get_db)) -> CompanyService:
    return CompanyService(db)


def get_department_service(db: Session = Depends(get_db)) -> DepartmentService:
    return DepartmentService(db)


def get_employee_service(db: Session = Depends(get_db)) -> EmployeeService:
    return EmployeeService(db)


def get_ai_org_service(db: Session = Depends(get_db)):
    from app.services.ai_organization import AIOrganizationService

    return AIOrganizationService(db)


def get_ai_reporting_service(db: Session = Depends(get_db)):
    from app.services.ai_reporting import AIReportingService

    return AIReportingService(db)


# --- Authentication / RBAC ------------------------------------------------


@dataclass
class CurrentUser:
    """The authenticated principal resolved from the access token."""

    id: uuid.UUID
    email: str
    role: Role
    full_name: str
    department_id: uuid.UUID | None


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    return AuthService(db)


def _bearer_token(request: Request) -> str:
    header = request.headers.get("Authorization", "")
    scheme, _, token = header.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise AuthError("Missing or invalid Authorization header")
    return token


def get_current_user(
    request: Request,
    auth: AuthService = Depends(get_auth_service),
) -> CurrentUser:
    """Resolve the current user from the Bearer access token (401 if invalid)."""
    employee = auth.user_from_access_token(_bearer_token(request))
    role = employee.role if isinstance(employee.role, Role) else Role(employee.role)
    return CurrentUser(
        id=employee.id,
        email=employee.email,
        role=role,
        full_name=employee.full_name,
        department_id=employee.department_id,
    )


def require_permission(permission: Permission):
    """Build a dependency that enforces ``permission`` for the current user.

    Reusable RBAC middleware: every protected endpoint declares the permission it
    needs. Missing auth -> 401 (from get_current_user); insufficient role -> 403.
    """

    def _guard(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if not role_has_permission(user.role, permission):
            raise ForbiddenError(f"Role '{user.role.value}' lacks permission '{permission.value}'")
        return user

    return _guard


# --- Work Management service providers (need CurrentUser above) ------------


def get_work_service(
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    from app.services.work import WorkService

    role = user.role.value if hasattr(user.role, "value") else user.role
    return WorkService(db, actor=f"{user.full_name} ({role})")


def get_work_analytics_service(db: Session = Depends(get_db)):
    from app.services.work_analytics import WorkAnalyticsService

    return WorkAnalyticsService(db)


def get_orchestration_service(
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    from app.services.orchestration import OrchestrationService

    role = user.role.value if hasattr(user.role, "value") else user.role
    return OrchestrationService(db, actor=f"{user.full_name} ({role})")


def get_execution_service(db: Session = Depends(get_db)):
    from app.services.execution import ExecutionService

    return ExecutionService(db)


def get_provider_service(
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    from app.services.providers_service import ProviderService

    return ProviderService(db, actor=_actor(user))


def get_budget_service(db: Session = Depends(get_db)):
    from app.services.budget_service import BudgetService

    return BudgetService(db)


def get_platform_dashboard(db: Session = Depends(get_db)):
    from app.services.provider_platform import PlatformDashboard

    return PlatformDashboard(db)


def get_metrics_service(
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    from app.services.provider_platform import MetricsService

    return MetricsService(db, actor=_actor(user))


def get_cost_engine(db: Session = Depends(get_db)):
    from app.services.provider_platform import CostEngine

    return CostEngine(db)


def get_health_monitor(
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    from app.services.provider_platform import HealthMonitor

    return HealthMonitor(db, actor=_actor(user))


# --- Knowledge Engine service providers (Sprint 10) -----------------------


def _actor(user: "CurrentUser") -> str:
    role = user.role.value if hasattr(user.role, "value") else user.role
    return f"{user.full_name} ({role})"


def get_knowledge_service(
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    from app.services.knowledge import KnowledgeService

    return KnowledgeService(db, actor=_actor(user))


def get_approval_service(
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    from app.services.knowledge_versions import ApprovalService

    return ApprovalService(db, actor=_actor(user))


def get_knowledge_graph_service(db: Session = Depends(get_db)):
    from app.services.knowledge_graph import RelationshipService

    return RelationshipService(db)


def get_reference_service(db: Session = Depends(get_db)):
    from app.services.knowledge_graph import ReferenceService

    return ReferenceService(db)


def get_version_service(db: Session = Depends(get_db)):
    from app.services.knowledge_versions import VersionService

    return VersionService(db)


def get_search_service(db: Session = Depends(get_db)):
    from app.services.knowledge_search import SearchService

    return SearchService(db)


def get_retrieval_service(db: Session = Depends(get_db)):
    from app.services.knowledge_search import RetrievalService

    return RetrievalService(db)


def get_bookmark_service(db: Session = Depends(get_db)):
    from app.services.knowledge_collections import BookmarkService

    return BookmarkService(db)


def get_collection_service(db: Session = Depends(get_db)):
    from app.services.knowledge_collections import CollectionService

    return CollectionService(db)


def get_knowledge_analytics_service(db: Session = Depends(get_db)):
    from app.services.knowledge_analytics import AnalyticsService

    return AnalyticsService(db)


def get_adr_service(db: Session = Depends(get_db)):
    from app.services.knowledge_analytics import ADRService

    return ADRService(db)


# --- Repository Intelligence service providers (Sprint 12) ----------------


def get_repository_service(db: Session = Depends(get_db)):
    from app.services.repository_service import RepositoryService

    return RepositoryService(db)


def get_indexer_service(db: Session = Depends(get_db)):
    from app.services.repository_service import IndexerService

    return IndexerService(db)


def get_symbol_service(db: Session = Depends(get_db)):
    from app.services.repo_analysis import SymbolService

    return SymbolService(db)


def get_dependency_service(db: Session = Depends(get_db)):
    from app.services.repo_analysis import DependencyService

    return DependencyService(db)


def get_repo_search_service(db: Session = Depends(get_db)):
    from app.services.repo_analysis import SearchService

    return SearchService(db)


def get_impact_service(db: Session = Depends(get_db)):
    from app.services.repo_analysis import ImpactAnalysisService

    return ImpactAnalysisService(db)


def get_architecture_service(db: Session = Depends(get_db)):
    from app.services.repo_analysis import ArchitectureService

    return ArchitectureService(db)


def get_documentation_service(db: Session = Depends(get_db)):
    from app.services.repo_analysis import DocumentationService

    return DocumentationService(db)


def get_repository_dashboard(db: Session = Depends(get_db)):
    from app.services.repo_analysis import RepositoryDashboard

    return RepositoryDashboard(db)


# --- Autonomous Development service providers (Sprint 13) ------------------


def get_development_service(
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    from app.services.development_service import DevelopmentService

    return DevelopmentService(db, actor=_actor(user))


def get_approval_dev_service(
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    from app.services.dev_review import ApprovalService

    return ApprovalService(db, actor=user.full_name)


# --- Quality Gate service providers (Sprint 14) ---------------------------


def get_quality_gate_service(
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    from app.services.quality_gate_service import QualityGateService

    return QualityGateService(db, actor=_actor(user))


# --- DevOps Platform service providers (Sprint 15) ------------------------


def get_pipeline_service(
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    from app.services.devops_pipeline import PipelineService

    return PipelineService(db, actor=_actor(user))


def get_deployment_service(
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    from app.services.devops_deploy import DeploymentService

    return DeploymentService(db, actor=_actor(user))


def get_rollback_service(
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    from app.services.devops_deploy import RollbackService

    return RollbackService(db, actor=user.full_name)


def get_environment_service(db: Session = Depends(get_db)):
    from app.services.devops_deploy import EnvironmentService

    return EnvironmentService(db)


def get_release_service(db: Session = Depends(get_db)):
    from app.services.devops_release import ReleaseService

    return ReleaseService(db)


def get_health_service(db: Session = Depends(get_db)):
    from app.services.devops_monitor import HealthService

    return HealthService(db)


def get_monitoring_service(db: Session = Depends(get_db)):
    from app.services.devops_monitor import MonitoringService

    return MonitoringService(db)


def get_incident_service(db: Session = Depends(get_db)):
    from app.services.devops_monitor import IncidentService

    return IncidentService(db)


def get_artifact_service(db: Session = Depends(get_db)):
    from app.services.devops_build import ArtifactService

    return ArtifactService(db)
