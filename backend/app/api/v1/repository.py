"""Repository Intelligence endpoints (Sprint 12).

Register + scan repositories; browse files, modules, symbols, architecture,
dependency graphs; search; impact analysis; documentation links; and the
founder/AI dashboards. Reads: repo:read (all roles); writes (register/scan):
repo:write (Founder only)."""

import uuid

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from app.api.deps import (
    get_architecture_service,
    get_dependency_service,
    get_documentation_service,
    get_impact_service,
    get_indexer_service,
    get_repo_search_service,
    get_repository_dashboard,
    get_repository_service,
    get_symbol_service,
    require_permission,
)
from app.domain.roles import Permission

router = APIRouter(prefix="/repositories", tags=["repositories"])
_read = Depends(require_permission(Permission.REPO_READ))
_write = Depends(require_permission(Permission.REPO_WRITE))


class RegisterIn(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    root_path: str = Field(min_length=1)
    description: str | None = None


# --- repositories ---------------------------------------------------------


@router.get("", dependencies=[_read])
def list_repositories(service=Depends(get_repository_service)) -> dict:
    items = [service.serialize(r) for r in service.list_repositories()]
    return {"data": items, "meta": {"total": len(items)}}


@router.post("", dependencies=[_write])
def register(payload: RegisterIn, service=Depends(get_repository_service)) -> dict:
    repo = service.register(payload.name, payload.root_path, description=payload.description)
    return {"data": service.serialize(repo)}


@router.get("/{repository_id}", dependencies=[_read])
def get_repository(repository_id: uuid.UUID, service=Depends(get_repository_service)) -> dict:
    return {"data": service.serialize(service.get(repository_id))}


@router.post("/{repository_id}/scan", dependencies=[_write])
def scan(
    repository_id: uuid.UUID,
    indexer=Depends(get_indexer_service),
    service=Depends(get_repository_service),
) -> dict:
    scan = indexer.scan(repository_id)
    return {
        "data": {
            "scan_id": str(scan.id),
            "status": scan.status.value if hasattr(scan.status, "value") else scan.status,
            "file_count": scan.file_count,
            "symbol_count": scan.symbol_count,
            "module_count": scan.module_count,
            "duration_ms": scan.duration_ms,
            "summary": scan.summary,
            "repository": service.serialize(service.get(repository_id)),
        }
    }


@router.get("/{repository_id}/dashboard", dependencies=[_read])
def dashboard(repository_id: uuid.UUID, dash=Depends(get_repository_dashboard)) -> dict:
    return {"data": dash.founder(repository_id)}


# --- files / modules / symbols -------------------------------------------


@router.get("/{repository_id}/files", dependencies=[_read])
def list_files(
    repository_id: uuid.UUID,
    layer: str | None = Query(default=None),
    service=Depends(get_repository_service),
) -> dict:
    from sqlalchemy import select

    from app.models.repository import RepositoryFile

    stmt = select(RepositoryFile).where(RepositoryFile.repository_id == repository_id)
    if layer:
        stmt = stmt.where(RepositoryFile.layer == layer)
    stmt = stmt.order_by(RepositoryFile.path).limit(1000)
    files = service.db.scalars(stmt).all()
    items = [
        {
            "id": str(f.id),
            "path": f.path,
            "name": f.name,
            "language": f.language.value if hasattr(f.language, "value") else f.language,
            "layer": f.layer,
            "line_count": f.line_count,
            "symbol_count": f.symbol_count,
            "is_test": f.is_test,
            "is_config": f.is_config,
            "is_generated": f.is_generated,
        }
        for f in files
    ]
    return {"data": items, "meta": {"total": len(items)}}


@router.get("/{repository_id}/modules", dependencies=[_read])
def modules(repository_id: uuid.UUID, service=Depends(get_architecture_service)) -> dict:
    items = service.modules(repository_id)
    return {"data": items, "meta": {"total": len(items)}}


@router.get("/{repository_id}/architecture", dependencies=[_read])
def architecture(repository_id: uuid.UUID, service=Depends(get_architecture_service)) -> dict:
    items = service.layers(repository_id)
    return {"data": items, "meta": {"total": len(items)}}


@router.get("/{repository_id}/symbols", dependencies=[_read])
def symbols(
    repository_id: uuid.UUID,
    symbol_type: str | None = Query(default=None),
    service=Depends(get_symbol_service),
) -> dict:
    items = service.list_symbols(repository_id, symbol_type=symbol_type)
    return {"data": items, "meta": {"total": len(items)}}


@router.get("/{repository_id}/files/{file_id}/symbols", dependencies=[_read])
def file_symbols(
    repository_id: uuid.UUID, file_id: uuid.UUID, service=Depends(get_symbol_service)
) -> dict:
    items = service.for_file(file_id)
    return {"data": items, "meta": {"total": len(items)}}


@router.get("/{repository_id}/references", dependencies=[_read])
def references(
    repository_id: uuid.UUID,
    name: str = Query(min_length=1),
    service=Depends(get_symbol_service),
) -> dict:
    return {"data": service.references(repository_id, name)}


# --- graphs / search / impact / docs -------------------------------------


@router.get("/{repository_id}/import-graph", dependencies=[_read])
def import_graph(repository_id: uuid.UUID, service=Depends(get_dependency_service)) -> dict:
    return {"data": service.import_graph(repository_id)}


@router.get("/{repository_id}/module-graph", dependencies=[_read])
def module_graph(repository_id: uuid.UUID, service=Depends(get_dependency_service)) -> dict:
    return {"data": service.module_graph(repository_id)}


@router.get("/{repository_id}/dependencies", dependencies=[_read])
def external_dependencies(
    repository_id: uuid.UUID, service=Depends(get_dependency_service)
) -> dict:
    items = service.external_dependencies(repository_id)
    return {"data": items, "meta": {"total": len(items)}}


@router.get("/{repository_id}/search", dependencies=[_read])
def search(
    repository_id: uuid.UUID,
    q: str | None = Query(default=None),
    kind: str | None = Query(default=None),
    service=Depends(get_repo_search_service),
) -> dict:
    items = service.search(repository_id, q or "", kind=kind)
    return {"data": items, "meta": {"total": len(items)}}


@router.get("/{repository_id}/impact", dependencies=[_read])
def impact(
    repository_id: uuid.UUID,
    file_path: str = Query(min_length=1),
    service=Depends(get_impact_service),
) -> dict:
    return {"data": service.analyze(repository_id, file_path)}


@router.get("/{repository_id}/documentation", dependencies=[_read])
def documentation(repository_id: uuid.UUID, service=Depends(get_documentation_service)) -> dict:
    return {"data": service.links(repository_id)}


@router.get("/{repository_id}/ai-context", dependencies=[_read])
def ai_context(
    repository_id: uuid.UUID,
    keywords: str | None = Query(default=None),
    dash=Depends(get_repository_dashboard),
) -> dict:
    return {"data": dash.ai(keywords)}
