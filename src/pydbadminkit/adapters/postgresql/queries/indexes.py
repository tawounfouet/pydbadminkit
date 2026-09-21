"""PostgreSQL index catalog queries."""

LIST_INDEXES_QUERY_ID = "PG_LIST_INDEXES"
GET_INDEX_QUERY_ID = "PG_GET_INDEX"

_SYSTEM_SCHEMA_PREDICATE = """
(
    tns.nspname IN ('pg_catalog', 'information_schema', 'pg_toast')
    OR tns.nspname ~ '^pg_temp_'
    OR tns.nspname ~ '^pg_toast_temp_'
)
"""

_INDEX_SELECT = """
SELECT
    ins.nspname AS schema_name,
    ic.relname AS name,
    tns.nspname AS table_schema,
    tc.relname AS table_name,
    am.amname AS method,
    pg_get_userbyid(ic.relowner) AS owner,
    i.indisunique AS is_unique,
    i.indisprimary AS is_primary,
    i.indisvalid AS is_valid,
    i.indisready AS is_ready,
    pg_relation_size(ic.oid) AS size_bytes
FROM pg_index AS i
JOIN pg_class AS ic
    ON ic.oid = i.indexrelid
JOIN pg_namespace AS ins
    ON ins.oid = ic.relnamespace
JOIN pg_class AS tc
    ON tc.oid = i.indrelid
JOIN pg_namespace AS tns
    ON tns.oid = tc.relnamespace
JOIN pg_am AS am
    ON am.oid = ic.relam
"""

LIST_INDEXES = (
    _INDEX_SELECT
    + f"""
WHERE (%s::boolean OR NOT {_SYSTEM_SCHEMA_PREDICATE})
  AND (%s::text IS NULL OR tns.nspname = %s)
  AND (%s::text IS NULL OR tc.relname = %s)
ORDER BY ins.nspname, ic.relname
"""
)

GET_INDEX = (
    _INDEX_SELECT
    + """
WHERE ins.nspname = %s
  AND ic.relname = %s
"""
)

GET_INDEX_DETAIL = """
SELECT
    pg_get_indexdef(i.indexrelid) AS definition,
    pg_get_expr(i.indpred, i.indrelid, true) AS predicate
FROM pg_index AS i
JOIN pg_class AS ic
    ON ic.oid = i.indexrelid
JOIN pg_namespace AS ins
    ON ins.oid = ic.relnamespace
WHERE ins.nspname = %s
  AND ic.relname = %s
"""
GET_INDEX_DETAIL_QUERY_ID = "PG_GET_INDEX_DETAIL"
