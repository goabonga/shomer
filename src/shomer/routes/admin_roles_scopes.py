# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Admin roles and scopes management API endpoints.

CRUD for roles and scopes, role-scope assignment, user-role assignment.
Requires ``admin:rbac:read`` or ``admin:rbac:write`` scope.
"""

from __future__ import annotations

import uuid as _uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from shomer.deps import DbSession
from shomer.middleware.rbac import require_scope
from shomer.models.role import Role
from shomer.models.role_scope import RoleScope
from shomer.models.scope import Scope
from shomer.models.user import User
from shomer.models.user_role import UserRole

router = APIRouter(prefix="/admin", tags=["admin"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _parse_uuid(value: str, label: str = "ID") -> _uuid.UUID:
    """Parse a UUID string or raise 400."""
    try:
        return _uuid.UUID(value)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid {label}",
        )


# ---------------------------------------------------------------------------
# Scopes CRUD
# ---------------------------------------------------------------------------


class ScopeRequest(BaseModel):
    """Request body for scope creation/update.

    Attributes
    ----------
    name : str
        Unique scope name.
    description : str or None
        Human-readable description.
    """

    name: str
    description: str | None = None


@router.get(
    "/scopes",
    dependencies=[Depends(require_scope("admin:rbac:read"))],
)
async def list_scopes(db: DbSession) -> JSONResponse:
    """List all scopes.

    Parameters
    ----------
    db : DbSession
        Database session.

    Returns
    -------
    JSONResponse
        List of scopes.
    """
    result = await db.execute(select(Scope).order_by(Scope.name))
    scopes = list(result.scalars().all())
    return JSONResponse(
        content={
            "items": [
                {
                    "id": str(s.id),
                    "name": s.name,
                    "description": s.description,
                }
                for s in scopes
            ],
            "total": len(scopes),
        }
    )


@router.post(
    "/scopes",
    dependencies=[Depends(require_scope("admin:rbac:write"))],
    status_code=status.HTTP_201_CREATED,
)
async def create_scope(body: ScopeRequest, db: DbSession) -> JSONResponse:
    """Create a new scope.

    Parameters
    ----------
    body : ScopeRequest
        Scope data.
    db : DbSession
        Database session.

    Returns
    -------
    JSONResponse
        The created scope.

    Raises
    ------
    HTTPException
        409 if scope name already exists.
    """
    existing = await db.execute(select(Scope).where(Scope.name == body.name))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Scope already exists",
        )
    scope = Scope(name=body.name, description=body.description)
    db.add(scope)
    await db.flush()
    return JSONResponse(
        status_code=201,
        content={
            "id": str(scope.id),
            "name": scope.name,
            "description": scope.description,
            "message": "Scope created successfully",
        },
    )


@router.put(
    "/scopes/{scope_id}",
    dependencies=[Depends(require_scope("admin:rbac:write"))],
)
async def update_scope(
    scope_id: str, body: ScopeRequest, db: DbSession
) -> JSONResponse:
    """Update a scope.

    Parameters
    ----------
    scope_id : str
        UUID of the scope.
    body : ScopeRequest
        Updated scope data.
    db : DbSession
        Database session.

    Returns
    -------
    JSONResponse
        Updated scope.

    Raises
    ------
    HTTPException
        404 if not found.
    """
    sid = _parse_uuid(scope_id, "scope ID")
    result = await db.execute(select(Scope).where(Scope.id == sid))
    scope = result.scalar_one_or_none()
    if scope is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Scope not found"
        )
    scope.name = body.name
    if body.description is not None:
        scope.description = body.description
    await db.flush()
    return JSONResponse(
        content={
            "id": str(scope.id),
            "name": scope.name,
            "description": scope.description,
            "message": "Scope updated successfully",
        }
    )


@router.delete(
    "/scopes/{scope_id}",
    dependencies=[Depends(require_scope("admin:rbac:write"))],
)
async def delete_scope(scope_id: str, db: DbSession) -> JSONResponse:
    """Delete a scope.

    Parameters
    ----------
    scope_id : str
        UUID of the scope.
    db : DbSession
        Database session.

    Returns
    -------
    JSONResponse
        Confirmation message.

    Raises
    ------
    HTTPException
        404 if not found.
    """
    sid = _parse_uuid(scope_id, "scope ID")
    result = await db.execute(select(Scope).where(Scope.id == sid))
    scope = result.scalar_one_or_none()
    if scope is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Scope not found"
        )
    await db.delete(scope)
    await db.flush()
    return JSONResponse(
        content={"id": str(sid), "message": "Scope deleted successfully"}
    )


# ---------------------------------------------------------------------------
# Roles CRUD
# ---------------------------------------------------------------------------


class RoleRequest(BaseModel):
    """Request body for role creation/update.

    Attributes
    ----------
    name : str
        Unique role name.
    description : str or None
        Human-readable description.
    is_system : bool
        Whether this is a system role (default False).
    """

    name: str
    description: str | None = None
    is_system: bool = False


@router.get(
    "/roles",
    dependencies=[Depends(require_scope("admin:rbac:read"))],
)
async def list_roles(db: DbSession) -> JSONResponse:
    """List all roles with their scopes.

    Parameters
    ----------
    db : DbSession
        Database session.

    Returns
    -------
    JSONResponse
        List of roles with scope names.
    """
    result = await db.execute(
        select(Role).options(selectinload(Role.scopes)).order_by(Role.name)
    )
    roles = list(result.scalars().all())
    items: list[dict[str, Any]] = []
    for r in roles:
        items.append(
            {
                "id": str(r.id),
                "name": r.name,
                "description": r.description,
                "is_system": r.is_system,
                "scopes": [s.name for s in r.scopes],
            }
        )
    return JSONResponse(content={"items": items, "total": len(items)})


@router.post(
    "/roles",
    dependencies=[Depends(require_scope("admin:rbac:write"))],
    status_code=status.HTTP_201_CREATED,
)
async def create_role(body: RoleRequest, db: DbSession) -> JSONResponse:
    """Create a new role.

    Parameters
    ----------
    body : RoleRequest
        Role data.
    db : DbSession
        Database session.

    Returns
    -------
    JSONResponse
        The created role.

    Raises
    ------
    HTTPException
        409 if role name already exists.
    """
    existing = await db.execute(select(Role).where(Role.name == body.name))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Role already exists",
        )
    role = Role(name=body.name, description=body.description, is_system=body.is_system)
    db.add(role)
    await db.flush()
    return JSONResponse(
        status_code=201,
        content={
            "id": str(role.id),
            "name": role.name,
            "description": role.description,
            "is_system": role.is_system,
            "message": "Role created successfully",
        },
    )


@router.put(
    "/roles/{role_id}",
    dependencies=[Depends(require_scope("admin:rbac:write"))],
)
async def update_role(role_id: str, body: RoleRequest, db: DbSession) -> JSONResponse:
    """Update a role.

    Parameters
    ----------
    role_id : str
        UUID of the role.
    body : RoleRequest
        Updated role data.
    db : DbSession
        Database session.

    Returns
    -------
    JSONResponse
        Updated role.

    Raises
    ------
    HTTPException
        404 if not found.
    """
    rid = _parse_uuid(role_id, "role ID")
    result = await db.execute(select(Role).where(Role.id == rid))
    role = result.scalar_one_or_none()
    if role is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Role not found"
        )
    role.name = body.name
    if body.description is not None:
        role.description = body.description
    role.is_system = body.is_system
    await db.flush()
    return JSONResponse(
        content={
            "id": str(role.id),
            "name": role.name,
            "description": role.description,
            "is_system": role.is_system,
            "message": "Role updated successfully",
        }
    )


@router.delete(
    "/roles/{role_id}",
    dependencies=[Depends(require_scope("admin:rbac:write"))],
)
async def delete_role(role_id: str, db: DbSession) -> JSONResponse:
    """Delete a role.

    System roles cannot be deleted.

    Parameters
    ----------
    role_id : str
        UUID of the role.
    db : DbSession
        Database session.

    Returns
    -------
    JSONResponse
        Confirmation message.

    Raises
    ------
    HTTPException
        400 if system role, 404 if not found.
    """
    rid = _parse_uuid(role_id, "role ID")
    result = await db.execute(select(Role).where(Role.id == rid))
    role = result.scalar_one_or_none()
    if role is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Role not found"
        )
    if role.is_system:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete system role",
        )
    await db.delete(role)
    await db.flush()
    return JSONResponse(
        content={"id": str(rid), "message": "Role deleted successfully"}
    )


# ---------------------------------------------------------------------------
# Role ↔ Scope assignment
# ---------------------------------------------------------------------------


@router.post(
    "/roles/{role_id}/scopes/{scope_id}",
    dependencies=[Depends(require_scope("admin:rbac:write"))],
    status_code=status.HTTP_201_CREATED,
)
async def assign_scope_to_role(
    role_id: str, scope_id: str, db: DbSession
) -> JSONResponse:
    """Assign a scope to a role.

    Parameters
    ----------
    role_id : str
        UUID of the role.
    scope_id : str
        UUID of the scope.
    db : DbSession
        Database session.

    Returns
    -------
    JSONResponse
        Confirmation message.

    Raises
    ------
    HTTPException
        404 if role or scope not found, 409 if already assigned.
    """
    rid = _parse_uuid(role_id, "role ID")
    sid = _parse_uuid(scope_id, "scope ID")

    role_result = await db.execute(select(Role).where(Role.id == rid))
    if role_result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Role not found"
        )
    scope_result = await db.execute(select(Scope).where(Scope.id == sid))
    if scope_result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Scope not found"
        )

    existing = await db.execute(
        select(RoleScope).where(RoleScope.role_id == rid, RoleScope.scope_id == sid)
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Scope already assigned to role",
        )

    rs = RoleScope(role_id=rid, scope_id=sid)
    db.add(rs)
    await db.flush()
    return JSONResponse(
        status_code=201,
        content={"message": "Scope assigned to role"},
    )


@router.delete(
    "/roles/{role_id}/scopes/{scope_id}",
    dependencies=[Depends(require_scope("admin:rbac:write"))],
)
async def remove_scope_from_role(
    role_id: str, scope_id: str, db: DbSession
) -> JSONResponse:
    """Remove a scope from a role.

    Parameters
    ----------
    role_id : str
        UUID of the role.
    scope_id : str
        UUID of the scope.
    db : DbSession
        Database session.

    Returns
    -------
    JSONResponse
        Confirmation message.

    Raises
    ------
    HTTPException
        404 if assignment not found.
    """
    rid = _parse_uuid(role_id, "role ID")
    sid = _parse_uuid(scope_id, "scope ID")

    result = await db.execute(
        select(RoleScope).where(RoleScope.role_id == rid, RoleScope.scope_id == sid)
    )
    rs = result.scalar_one_or_none()
    if rs is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scope not assigned to role",
        )

    await db.delete(rs)
    await db.flush()
    return JSONResponse(content={"message": "Scope removed from role"})


# ---------------------------------------------------------------------------
# User ↔ Role assignment
# ---------------------------------------------------------------------------


@router.post(
    "/users/{user_id}/roles/{role_id}",
    dependencies=[Depends(require_scope("admin:rbac:write"))],
    status_code=status.HTTP_201_CREATED,
)
async def assign_role_to_user(
    user_id: str, role_id: str, db: DbSession
) -> JSONResponse:
    """Assign a role to a user (global).

    Parameters
    ----------
    user_id : str
        UUID of the user.
    role_id : str
        UUID of the role.
    db : DbSession
        Database session.

    Returns
    -------
    JSONResponse
        Confirmation message.

    Raises
    ------
    HTTPException
        404 if user or role not found, 409 if already assigned.
    """
    uid = _parse_uuid(user_id, "user ID")
    rid = _parse_uuid(role_id, "role ID")

    user_result = await db.execute(select(User).where(User.id == uid))
    if user_result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    role_result = await db.execute(select(Role).where(Role.id == rid))
    if role_result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Role not found"
        )

    existing = await db.execute(
        select(UserRole).where(
            UserRole.user_id == uid,
            UserRole.role_id == rid,
            UserRole.tenant_id.is_(None),
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Role already assigned to user",
        )

    ur = UserRole(user_id=uid, role_id=rid, tenant_id=None)
    db.add(ur)
    await db.flush()
    return JSONResponse(
        status_code=201,
        content={"message": "Role assigned to user"},
    )


@router.delete(
    "/users/{user_id}/roles/{role_id}",
    dependencies=[Depends(require_scope("admin:rbac:write"))],
)
async def remove_role_from_user(
    user_id: str, role_id: str, db: DbSession
) -> JSONResponse:
    """Remove a role from a user (global assignment).

    Parameters
    ----------
    user_id : str
        UUID of the user.
    role_id : str
        UUID of the role.
    db : DbSession
        Database session.

    Returns
    -------
    JSONResponse
        Confirmation message.

    Raises
    ------
    HTTPException
        404 if assignment not found.
    """
    uid = _parse_uuid(user_id, "user ID")
    rid = _parse_uuid(role_id, "role ID")

    result = await db.execute(
        select(UserRole).where(
            UserRole.user_id == uid,
            UserRole.role_id == rid,
            UserRole.tenant_id.is_(None),
        )
    )
    ur = result.scalar_one_or_none()
    if ur is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not assigned to user",
        )

    await db.delete(ur)
    await db.flush()
    return JSONResponse(content={"message": "Role removed from user"})
