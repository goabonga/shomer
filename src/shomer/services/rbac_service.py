# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""RBAC permission evaluation service.

Resolves user roles, collects scopes, and evaluates permissions
with wildcard support and role expiration.
"""

from __future__ import annotations

import fnmatch
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shomer.models.role_scope import RoleScope
from shomer.models.scope import Scope
from shomer.models.user_role import UserRole


class RBACService:
    """Evaluate RBAC permissions for users.

    Resolves roles assigned to a user (optionally scoped to a tenant),
    collects all scopes from active (non-expired) roles, and checks
    permissions with wildcard matching.

    Attributes
    ----------
    session : AsyncSession
        Database session.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_user_roles(
        self,
        user_id: uuid.UUID,
        tenant_id: uuid.UUID | None = None,
    ) -> list[UserRole]:
        """Resolve all active role assignments for a user.

        Returns roles that are either global (``tenant_id IS NULL``) or
        scoped to the given tenant. Expired roles are excluded.

        Parameters
        ----------
        user_id : uuid.UUID
            The user's ID.
        tenant_id : uuid.UUID or None
            Optional tenant scope. If provided, includes both global
            and tenant-specific roles.

        Returns
        -------
        list[UserRole]
            Active role assignments.
        """
        now = datetime.now(timezone.utc)
        stmt = select(UserRole).where(
            UserRole.user_id == user_id,
        )
        result = await self.session.execute(stmt)
        all_roles = result.scalars().all()

        active: list[UserRole] = []
        for ur in all_roles:
            # Skip expired roles
            if ur.expires_at is not None and ur.expires_at < now:
                continue
            # Include global roles (tenant_id is None) and tenant-specific
            if ur.tenant_id is None or ur.tenant_id == tenant_id:
                active.append(ur)
        return active

    async def get_user_scopes(
        self,
        user_id: uuid.UUID,
        tenant_id: uuid.UUID | None = None,
    ) -> set[str]:
        """Collect all scope names from the user's active roles.

        Parameters
        ----------
        user_id : uuid.UUID
            The user's ID.
        tenant_id : uuid.UUID or None
            Optional tenant scope.

        Returns
        -------
        set[str]
            Set of scope names the user has.
        """
        user_roles = await self.get_user_roles(user_id, tenant_id)
        if not user_roles:
            return set()

        role_ids = [ur.role_id for ur in user_roles]

        # Get all scopes for these roles via RoleScope junction
        stmt = (
            select(Scope.name)
            .join(RoleScope, RoleScope.scope_id == Scope.id)
            .where(RoleScope.role_id.in_(role_ids))
        )
        result = await self.session.execute(stmt)
        return {row[0] for row in result.all()}

    async def has_permission(
        self,
        user_id: uuid.UUID,
        scope: str,
        tenant_id: uuid.UUID | None = None,
    ) -> bool:
        """Check if a user has a specific permission.

        Supports wildcard matching: a user scope of ``admin:*`` matches
        a required scope of ``admin:users:read``.

        Parameters
        ----------
        user_id : uuid.UUID
            The user's ID.
        scope : str
            The required scope (e.g. ``admin:users:read``).
        tenant_id : uuid.UUID or None
            Optional tenant scope.

        Returns
        -------
        bool
            ``True`` if the user has the required permission.
        """
        user_scopes = await self.get_user_scopes(user_id, tenant_id)
        return self._matches_any(scope, user_scopes)

    async def has_any_permission(
        self,
        user_id: uuid.UUID,
        scopes: list[str],
        tenant_id: uuid.UUID | None = None,
    ) -> bool:
        """Check if a user has at least one of the required permissions.

        Parameters
        ----------
        user_id : uuid.UUID
            The user's ID.
        scopes : list[str]
            Required scopes (at least one must match).
        tenant_id : uuid.UUID or None
            Optional tenant scope.

        Returns
        -------
        bool
            ``True`` if the user has at least one of the required scopes.
        """
        user_scopes = await self.get_user_scopes(user_id, tenant_id)
        return any(self._matches_any(s, user_scopes) for s in scopes)

    @staticmethod
    def _matches_any(required: str, available: set[str]) -> bool:
        """Check if a required scope matches any available scope.

        Uses ``fnmatch``-style wildcard matching where ``*`` matches
        any segment. For example, ``admin:*`` matches ``admin:users:read``.

        Parameters
        ----------
        required : str
            The scope to check.
        available : set[str]
            The user's available scopes (may contain wildcards).

        Returns
        -------
        bool
            ``True`` if any available scope matches the required one.
        """
        for scope in available:
            if scope == required:
                return True
            # Wildcard matching: "admin:*" matches "admin:users:read"
            if "*" in scope and fnmatch.fnmatch(required, scope):
                return True
        return False

    @staticmethod
    def scope_matches(pattern: str, scope: str) -> bool:
        """Check if a scope pattern matches a specific scope.

        Parameters
        ----------
        pattern : str
            Scope pattern (may contain ``*`` wildcards).
        scope : str
            The scope to check against.

        Returns
        -------
        bool
            ``True`` if the pattern matches the scope.
        """
        if pattern == scope:
            return True
        if "*" in pattern:
            return fnmatch.fnmatch(scope, pattern)
        return False
