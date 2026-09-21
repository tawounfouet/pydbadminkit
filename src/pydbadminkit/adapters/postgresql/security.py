"""PostgreSQL security inspection and mutation adapter."""

from psycopg import sql

from pydbadminkit.adapters.postgresql.executor import PostgreSQLExecutor
from pydbadminkit.adapters.postgresql.mappers.access import map_direct_access
from pydbadminkit.adapters.postgresql.mappers.effective_access import map_effective_access
from pydbadminkit.adapters.postgresql.mappers.ownership import map_ownership
from pydbadminkit.adapters.postgresql.mappers.security import (
    map_role_info,
    map_role_membership,
)
from pydbadminkit.adapters.postgresql.queries.access import (
    LIST_DIRECT_RELATION_ACCESS,
    LIST_DIRECT_RELATION_ACCESS_QUERY_ID,
)
from pydbadminkit.adapters.postgresql.queries.effective_access import (
    LIST_EFFECTIVE_RELATION_ACCESS,
    LIST_EFFECTIVE_RELATION_ACCESS_QUERY_ID,
)
from pydbadminkit.adapters.postgresql.queries.ownership import (
    LIST_OWNERSHIP,
    LIST_OWNERSHIP_QUERY_ID,
)
from pydbadminkit.adapters.postgresql.queries.security import (
    GET_ROLE,
    GET_ROLE_QUERY_ID,
    LIST_ROLE_MEMBERSHIPS,
    LIST_ROLE_MEMBERSHIPS_QUERY_ID,
    LIST_ROLES,
    LIST_ROLES_QUERY_ID,
)
from pydbadminkit.domain.common import DatabaseObjectType
from pydbadminkit.domain.security import (
    DirectAccess,
    EffectiveAccess,
    OwnershipInfo,
    RoleDescription,
    RoleInfo,
    RoleMembership,
)
from pydbadminkit.domain.security.mutations import (
    AlterRoleCommand,
    CreateRoleCommand,
    MembershipCommand,
    RelationAccessCommand,
)
from pydbadminkit.errors import ResourceNotFoundError


class PostgreSQLSecurityAdapter:
    """PostgreSQL security inspection and mutation adapter."""

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

    def list_effective_access(
        self,
        role: str,
        *,
        schema: str | None = None,
        object_name: str | None = None,
        include_system: bool = False,
    ) -> tuple[EffectiveAccess, ...]:
        rows = self._executor.fetch_all(
            LIST_EFFECTIVE_RELATION_ACCESS,
            (
                role,
                include_system,
                schema,
                schema,
                object_name,
                object_name,
            ),
            query_id=LIST_EFFECTIVE_RELATION_ACCESS_QUERY_ID,
        )
        return tuple(map_effective_access(row) for row in rows)

    def list_ownership(
        self,
        owner: str,
        *,
        object_type: DatabaseObjectType | None = None,
        schema: str | None = None,
        include_system: bool = False,
    ) -> tuple[OwnershipInfo, ...]:
        rows = self._executor.fetch_all(
            LIST_OWNERSHIP,
            (
                owner,
                owner,
                include_system,
                owner,
                include_system,
                schema,
                schema,
            ),
            query_id=LIST_OWNERSHIP_QUERY_ID,
        )
        ownership = tuple(map_ownership(row) for row in rows)
        if object_type is None:
            return ownership
        return tuple(item for item in ownership if item.object.object_type is object_type)


    def create_role(self, command: CreateRoleCommand) -> None:
        options = (
            sql.SQL("LOGIN" if command.can_login else "NOLOGIN"),
            sql.SQL("SUPERUSER" if command.is_superuser else "NOSUPERUSER"),
            sql.SQL("CREATEDB" if command.can_create_db else "NOCREATEDB"),
            sql.SQL("CREATEROLE" if command.can_create_role else "NOCREATEROLE"),
            sql.SQL("REPLICATION" if command.can_replicate else "NOREPLICATION"),
            sql.SQL("INHERIT" if command.inherit else "NOINHERIT"),
            sql.SQL("BYPASSRLS" if command.bypass_rls else "NOBYPASSRLS"),
            sql.SQL("CONNECTION LIMIT {}").format(sql.Literal(command.connection_limit)),
        )
        query = (
            sql.SQL("CREATE ROLE {} ").format(sql.Identifier(command.name))
            + sql.SQL(" ").join(options)
        )
        self._executor.execute(query, query_id="PG_CREATE_ROLE")

    def alter_role(self, command: AlterRoleCommand) -> None:
        options: list[sql.Composable] = []
        if command.can_login is not None:
            options.append(sql.SQL("LOGIN" if command.can_login else "NOLOGIN"))
        if command.is_superuser is not None:
            options.append(sql.SQL("SUPERUSER" if command.is_superuser else "NOSUPERUSER"))
        if command.can_create_db is not None:
            options.append(sql.SQL("CREATEDB" if command.can_create_db else "NOCREATEDB"))
        if command.can_create_role is not None:
            options.append(
                sql.SQL("CREATEROLE" if command.can_create_role else "NOCREATEROLE")
            )
        if command.can_replicate is not None:
            options.append(
                sql.SQL("REPLICATION" if command.can_replicate else "NOREPLICATION")
            )
        if command.inherit is not None:
            options.append(sql.SQL("INHERIT" if command.inherit else "NOINHERIT"))
        if command.bypass_rls is not None:
            options.append(sql.SQL("BYPASSRLS" if command.bypass_rls else "NOBYPASSRLS"))
        if command.connection_limit is not None:
            options.append(
                sql.SQL("CONNECTION LIMIT {}").format(sql.Literal(command.connection_limit))
            )

        query = (
            sql.SQL("ALTER ROLE {} ").format(sql.Identifier(command.name))
            + sql.SQL(" ").join(options)
        )
        self._executor.execute(query, query_id="PG_ALTER_ROLE")

    def drop_role(self, name: str) -> None:
        query = sql.SQL("DROP ROLE {}").format(sql.Identifier(name))
        self._executor.execute(query, query_id="PG_DROP_ROLE")

    def add_membership(self, command: MembershipCommand) -> None:
        query = sql.SQL("GRANT {} TO {}").format(
            sql.Identifier(command.role),
            sql.Identifier(command.member),
        )
        if command.admin_option:
            query += sql.SQL(" WITH ADMIN OPTION")
        self._executor.execute(query, query_id="PG_ADD_ROLE_MEMBERSHIP")

    def remove_membership(self, command: MembershipCommand) -> None:
        query = sql.SQL("REVOKE {} FROM {}").format(
            sql.Identifier(command.role),
            sql.Identifier(command.member),
        )
        self._executor.execute(query, query_id="PG_REMOVE_ROLE_MEMBERSHIP")

    def grant_access(self, command: RelationAccessCommand) -> None:
        relation = sql.Identifier(command.object.schema or "public", command.object.name)
        query = sql.SQL("GRANT {} ON TABLE {} TO {}").format(
            sql.SQL(command.access_type.value),
            relation,
            sql.Identifier(command.principal),
        )
        if command.grant_option:
            query += sql.SQL(" WITH GRANT OPTION")
        self._executor.execute(query, query_id="PG_GRANT_RELATION_ACCESS")

    def revoke_access(self, command: RelationAccessCommand) -> None:
        relation = sql.Identifier(command.object.schema or "public", command.object.name)
        query = sql.SQL("REVOKE {} ON TABLE {} FROM {}").format(
            sql.SQL(command.access_type.value),
            relation,
            sql.Identifier(command.principal),
        )
        self._executor.execute(query, query_id="PG_REVOKE_RELATION_ACCESS")
