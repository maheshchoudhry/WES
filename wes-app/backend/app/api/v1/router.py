"""Aggregate v1 API router."""
from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.routes import company, departments, employees, system

api_router = APIRouter()
api_router.include_router(company.router)
api_router.include_router(departments.router)
api_router.include_router(employees.router)
api_router.include_router(system.router)
