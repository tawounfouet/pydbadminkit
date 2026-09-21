"""PostgreSQL schema catalog queries."""

LIST_SCHEMAS_QUERY_ID = "PG_LIST_SCHEMAS"
GET_SCHEMA_QUERY_ID = "PG_GET_SCHEMA"

_SYSTEM_SCHEMA_PREDICATE = """
(
    n.nspname IN ('pg_catalog', 'information_schema', 'pg_toast')
    OR n.nspname LIKE 'pg_temp_%'
    OR n.nspname LIKE 'pg_toast_temp_%'
)
"""

LIST_SCHEMAS = f"""
SELECT
    n.nspname AS name,
    pg_get_userbyid(n.nspowner) AS owner,
    {_SYSTEM_SCHEMA_PREDICATE} AS is_system
FROM pg_namespace AS n
WHERE (%s::boolean OR NOT {_SYSTEM_SCHEMA_PREDICATE})
ORDER BY n.nspname
"""

GET_SCHEMA = f"""
SELECT
    n.nspname AS name,
    pg_get_userbyid(n.nspowner) AS owner,
    {_SYSTEM_SCHEMA_PREDICATE} AS is_system
FROM pg_namespace AS n
WHERE n.nspname = %s
"""
