"""Aggregate API v1 router."""

from fastapi import APIRouter

from app.api.v1 import auth, companies, dashboard, departments, employees, health

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(dashboard.router)
api_router.include_router(companies.router)
api_router.include_router(departments.router)
api_router.include_router(employees.router)
