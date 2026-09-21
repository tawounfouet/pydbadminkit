"""PostgreSQL ownership inspection query."""

LIST_OWNERSHIP_QUERY_ID = "PG_LIST_OWNERSHIP"

LIST_OWNERSHIP = """
SELECT
    owner.rolname AS owner,
    'database'::text AS object_type,
    NULL::text AS schema_name,
    d.datname AS object_name
FROM pg_database AS d
JOIN pg_roles AS owner
    ON owner.oid = d.datdba
WHERE owner.rolname = %s

UNION ALL

SELECT
    owner.rolname AS owner,
    'schema'::text AS object_type,
    NULL::text AS schema_name,
    n.nspname AS object_name
FROM pg_namespace AS n
JOIN pg_roles AS owner
    ON owner.oid = n.nspowner
WHERE owner.rolname = %s
  AND (
      %s::boolean
      OR (
          n.nspname NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
          AND n.nspname NOT LIKE 'pg_temp_%%'
          AND n.nspname NOT LIKE 'pg_toast_temp_%%'
      )
  )

UNION ALL

SELECT
    owner.rolname AS owner,
    CASE
        WHEN c.relkind IN ('v', 'm') THEN 'view'
        ELSE 'table'
    END AS object_type,
    n.nspname AS schema_name,
    c.relname AS object_name
FROM pg_class AS c
JOIN pg_namespace AS n
    ON n.oid = c.relnamespace
JOIN pg_roles AS owner
    ON owner.oid = c.relowner
WHERE owner.rolname = %s
  AND c.relkind IN ('r', 'p', 'v', 'm', 'f')
  AND (
      %s::boolean
      OR (
          n.nspname NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
          AND n.nspname NOT LIKE 'pg_temp_%%'
          AND n.nspname NOT LIKE 'pg_toast_temp_%%'
      )
  )
  AND (%s::text IS NULL OR n.nspname = %s)

ORDER BY object_type, schema_name NULLS FIRST, object_name
"""
