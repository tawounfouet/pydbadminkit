"""PostgreSQL view catalog queries."""

LIST_VIEWS_QUERY_ID = "PG_LIST_VIEWS"
GET_VIEW_QUERY_ID = "PG_GET_VIEW"
GET_VIEW_COLUMNS_QUERY_ID = "PG_GET_VIEW_COLUMNS"

_SYSTEM_SCHEMA_PREDICATE = """
(
    n.nspname IN ('pg_catalog', 'information_schema', 'pg_toast')
    OR n.nspname ~ '^pg_temp_'
    OR n.nspname ~ '^pg_toast_temp_'
)
"""

_VIEW_SELECT = """
SELECT
    n.nspname AS schema_name,
    c.relname AS name,
    pg_get_userbyid(c.relowner) AS owner,
    c.relkind AS relkind
FROM pg_class AS c
JOIN pg_namespace AS n
    ON n.oid = c.relnamespace
"""

LIST_VIEWS = (
    _VIEW_SELECT
    + f"""
WHERE c.relkind IN ('v', 'm')
  AND (%s::boolean OR NOT {_SYSTEM_SCHEMA_PREDICATE})
  AND (%s::text IS NULL OR n.nspname = %s)
ORDER BY n.nspname, c.relname
"""
)

GET_VIEW = (
    _VIEW_SELECT
    + """
WHERE c.relkind IN ('v', 'm')
  AND n.nspname = %s
  AND c.relname = %s
"""
)

GET_VIEW_COLUMNS = """
SELECT
    a.attname AS name,
    a.attnum AS position,
    format_type(a.atttypid, a.atttypmod) AS data_type,
    NOT a.attnotnull AS nullable,
    NULL::text AS default_expression,
    false AS identity,
    a.attgenerated <> '' AS generated,
    col_description(c.oid, a.attnum) AS comment
FROM pg_class AS c
JOIN pg_namespace AS n
    ON n.oid = c.relnamespace
JOIN pg_attribute AS a
    ON a.attrelid = c.oid
WHERE n.nspname = %s
  AND c.relname = %s
  AND c.relkind IN ('v', 'm')
  AND a.attnum > 0
  AND NOT a.attisdropped
ORDER BY a.attnum
"""

GET_VIEW_DEFINITION = """
SELECT pg_get_viewdef(c.oid, true) AS definition
FROM pg_class AS c
JOIN pg_namespace AS n
    ON n.oid = c.relnamespace
WHERE n.nspname = %s
  AND c.relname = %s
  AND c.relkind IN ('v', 'm')
"""
GET_VIEW_DEFINITION_QUERY_ID = "PG_GET_VIEW_DEFINITION"
