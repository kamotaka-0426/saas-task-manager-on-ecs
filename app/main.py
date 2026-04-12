import logging
import json
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.config import settings
from app.routers import auth, organizations, projects, issues, labels


class JsonFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps({
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
        })


handler = logging.StreamHandler()
handler.setFormatter(JsonFormatter())
logger = logging.getLogger("app")
logger.addHandler(handler)
logger.setLevel(logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


_DESCRIPTION = """
Multi-tenant SaaS task management API — a minimal Linear/Asana clone.

## Features

- **Organizations** — multi-tenant isolation; every resource is scoped to an org
- **Projects** — group issues by project within an org
- **Issues** — full CRUD with status/priority tracking
- **Comments** — threaded comments per issue
- **Activity logs** — automatic audit trail on every change
- **Labels** — org-scoped labels attached to issues (many-to-many)
- **Assignees** — assign multiple org members to an issue (many-to-many)
- **Full-text search** — `?q=` searches title + description (tsvector/GIN on PostgreSQL, LIKE on SQLite)
- **Filters & sort** — `?status=`, `?priority=`, `?assignee_id=`, `?label_id=`, `?sort=`
- **Cursor pagination** — stable keyset pagination via `next_cursor`

## RBAC

| Role   | Create/Update | Delete | Manage labels/assignees |
|--------|--------------|--------|------------------------|
| member | ✗            | ✗      | ✗                      |
| admin  | ✓            | ✗      | ✓                      |
| owner  | ✓            | ✓      | ✓                      |
"""

_TAGS = [
    {"name": "auth",          "description": "Register and obtain JWT access tokens"},
    {"name": "organizations", "description": "Org CRUD and member management"},
    {"name": "projects",      "description": "Project CRUD within an org"},
    {"name": "issues",        "description": "Issue tracking — filters, search, pagination"},
    {"name": "labels",        "description": "Org-scoped label management"},
    {"name": "system",        "description": "Health check"},
]

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=_DESCRIPTION,
    version="1.0.0",
    openapi_tags=_TAGS,
    lifespan=lifespan,
)


class OriginVerifyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path == "/health":
            return await call_next(request)
        if settings.ORIGIN_VERIFY_SECRET:
            if request.headers.get("X-Origin-Verify", "") != settings.ORIGIN_VERIFY_SECRET:
                raise HTTPException(status_code=403, detail="Direct access is not allowed")
        return await call_next(request)


app.add_middleware(OriginVerifyMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(organizations.router)
app.include_router(projects.router)
app.include_router(issues.router)
app.include_router(labels.router)


@app.get("/health", tags=["system"], summary="Health check")
async def health_check():
    """Returns `{"status": "ok"}` — used by load balancer and readiness probes."""
    return {"status": "ok", "project": settings.PROJECT_NAME}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
