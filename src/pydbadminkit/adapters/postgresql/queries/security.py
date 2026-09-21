"""PostgreSQL role and membership inspection queries."""

LIST_ROLES_QUERY_ID = "PG_LIST_ROLES"
GET_ROLE_QUERY_ID = "PG_GET_ROLE"
LIST_ROLE_MEMBERSHIPS_QUERY_ID = "PG_LIST_ROLE_MEMBERSHIPS"

_ROLE_SELECT = """
SELECT
    r.rolname AS name,
    r.rolcanlogin AS can_login,
    r.rolsuper AS is_superuser,
    r.rolcreatedb AS can_create_db,
    r.rolcreaterole AS can_create_role,
    r.rolreplication AS can_replicate,
    r.rolinherit AS inherit,
    r.rolconnlimit AS connection_limit,
    r.rolvaliduntil AS valid_until,
    r.rolbypassrls AS bypass_rls
FROM pg_roles AS r
"""

LIST_ROLES = (
    _ROLE_SELECT
    + """
WHERE (%s::boolean OR r.rolname !~ '^pg_')
  AND (%s::boolean = false OR r.rolcanlogin)
ORDER BY r.rolname
"""
)

GET_ROLE = (
    _ROLE_SELECT
    + """
WHERE r.rolname = %s
"""
)

LIST_ROLE_MEMBERSHIPS = """
SELECT
    role_role.rolname AS role_name,
    member_role.rolname AS member_name,
    grantor_role.rolname AS grantor_name,
    m.admin_option AS admin_option
FROM pg_auth_members AS m
JOIN pg_roles AS role_role
    ON role_role.oid = m.roleid
JOIN pg_roles AS member_role
    ON member_role.oid = m.member
LEFT JOIN pg_roles AS grantor_role
    ON grantor_role.oid = m.grantor
ORDER BY role_role.rolname, member_role.rolname
"""
