"""PostgreSQL SecurityPort implementation."""

from pydbadminkit.adapters.postgresql.executor import PostgreSQLExecutor
from pydbadminkit.adapters.postgresql.mappers.access import map_direct_access
from pydbadminkit.adapters.postgresql.mappers.security import (
    map_role_info,
    map_role_membership,
)
from pydbadminkit.adapters.postgresql.queries.access import (
    LIST_DIRECT_RELATION_ACCESS,
    LIST_DIRECT_RELATION_ACCESS_QUERY_ID,
)
from pydbadminkit.adapters.postgresql.queries.security import (
    GET_ROLE,
    GET_ROLE_QUERY_ID,
    LIST_ROLE_MEMBERSHIPS,
    LIST_ROLE_MEMBERSHIPS_QUERY_ID,
    LIST_ROLES,
    LIST_ROLES_QUERY_ID,
)
from pydbadminkit.domain.security import DirectAccess, RoleDescription, RoleInfo, RoleMembership
from pydbadminkit.errors import ResourceNotFoundError


class PostgreSQLSecurityAdapter:
    """Read-only PostgreSQL role and membership inspection."""

    def __init__(self, executor: PostgreSQLExecutor) -> None:
        self._executor = executor

    def list_roles(
        self,
        *,
        include_system: bool = False,
        login_only: bool = False,
    ) -> tuple[RoleInfo, ...]:
        rows = self._executor.fetch_all(
            LIST_ROLES,
            (include_system, login_only),
            query_id=LIST_ROLES_QUERY_ID,
        )
        return tuple(map_role_info(row) for row in rows)

    def describe_role(self, name: str) -> RoleDescription:
        role_row = self._executor.fetch_one(
            GET_ROLE,
            (name,),
            query_id=GET_ROLE_QUERY_ID,
        )
        if role_row is None:
            raise ResourceNotFoundError(f"Role '{name}' was not found or is not visible.")

        memberships = self.list_role_memberships()
        return RoleDescription(
            role=map_role_info(role_row),
            member_of=tuple(membership for membership in memberships if membership.member == name),
            members=tuple(membership for membership in memberships if membership.role == name),
        )

    def list_role_memberships(self) -> tuple[RoleMembership, ...]:
        rows = self._executor.fetch_all(
            LIST_ROLE_MEMBERSHIPS,
            query_id=LIST_ROLE_MEMBERSHIPS_QUERY_ID,
        )
        return tuple(map_role_membership(row) for row in rows)

    def list_direct_access(
        self,
        role: str,
        *,
        schema: str | None = None,
        object_name: str | None = None,
        include_system: bool = False,
    ) -> tuple[DirectAccess, ...]:
        rows = self._executor.fetch_all(
            LIST_DIRECT_RELATION_ACCESS,
            (
                role,
                include_system,
                schema,
                schema,
                object_name,
                object_name,
            ),
            query_id=LIST_DIRECT_RELATION_ACCESS_QUERY_ID,
        )
        return tuple(map_direct_access(row) for row in rows)
