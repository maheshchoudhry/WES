"""Aggregate API v1 router."""

from fastapi import APIRouter

from app.api.v1 import (
    ai_employees,
    ai_org,
    ai_roles,
    assignments,
    auth,
    companies,
    dashboard,
    departments,
    employees,
    execution,
    health,
    libraries,
    projects,
    sprints,
    tasks,
    work_dashboard,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(dashboard.router)
api_router.include_router(companies.router)
api_router.include_router(departments.router)
api_router.include_router(employees.router)
api_router.include_router(ai_employees.router)
api_router.include_router(ai_roles.router)
api_router.include_router(ai_org.router)
api_router.include_router(projects.router)
api_router.include_router(sprints.router)
api_router.include_router(tasks.router)
api_router.include_router(assignments.router)
api_router.include_router(work_dashboard.router)
api_router.include_router(execution.router)
api_router.include_router(libraries.router)
