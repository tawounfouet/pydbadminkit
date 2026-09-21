"""PostgreSQL table catalog queries."""

LIST_TABLES_QUERY_ID = "PG_LIST_TABLES"
GET_TABLE_QUERY_ID = "PG_GET_TABLE"
GET_TABLE_COLUMNS_QUERY_ID = "PG_GET_TABLE_COLUMNS"
GET_TABLE_CONSTRAINTS_QUERY_ID = "PG_GET_TABLE_CONSTRAINTS"

_SYSTEM_SCHEMA_PREDICATE = """
(
    n.nspname IN ('pg_catalog', 'information_schema', 'pg_toast')
    OR n.nspname ~ '^pg_temp_'
    OR n.nspname ~ '^pg_toast_temp_'
)
"""

_TABLE_SELECT = """
SELECT
    n.nspname AS schema_name,
    c.relname AS name,
    pg_get_userbyid(c.relowner) AS owner,
    c.relkind AS relkind,
    CASE
        WHEN c.reltuples < 0 THEN NULL
        ELSE c.reltuples::bigint
    END AS estimated_rows,
    pg_total_relation_size(c.oid) AS size_bytes
FROM pg_class AS c
JOIN pg_namespace AS n
    ON n.oid = c.relnamespace
"""

LIST_TABLES = (
    _TABLE_SELECT
    + f"""
WHERE c.relkind IN ('r', 'p', 'f')
  AND (%s::boolean OR NOT {_SYSTEM_SCHEMA_PREDICATE})
  AND (%s::text IS NULL OR n.nspname = %s)
ORDER BY n.nspname, c.relname
"""
)

GET_TABLE = (
    _TABLE_SELECT
    + """
WHERE c.relkind IN ('r', 'p', 'f')
  AND n.nspname = %s
  AND c.relname = %s
"""
)

GET_TABLE_COLUMNS = """
SELECT
    a.attname AS name,
    a.attnum AS position,
    format_type(a.atttypid, a.atttypmod) AS data_type,
    NOT a.attnotnull AS nullable,
    pg_get_expr(ad.adbin, ad.adrelid) AS default_expression,
    a.attidentity <> '' AS identity,
    a.attgenerated <> '' AS generated,
    col_description(c.oid, a.attnum) AS comment
FROM pg_class AS c
JOIN pg_namespace AS n
    ON n.oid = c.relnamespace
JOIN pg_attribute AS a
    ON a.attrelid = c.oid
LEFT JOIN pg_attrdef AS ad
    ON ad.adrelid = a.attrelid
   AND ad.adnum = a.attnum
WHERE n.nspname = %s
  AND c.relname = %s
  AND a.attnum > 0
  AND NOT a.attisdropped
ORDER BY a.attnum
"""

GET_TABLE_CONSTRAINTS = """
SELECT
    con.conname AS name,
    con.contype AS constraint_type,
    COALESCE(
        ARRAY(
            SELECT att.attname
            FROM unnest(con.conkey) WITH ORDINALITY AS key_col(attnum, ord)
            JOIN pg_attribute AS att
              ON att.attrelid = con.conrelid
             AND att.attnum = key_col.attnum
            ORDER BY key_col.ord
        ),
        ARRAY[]::text[]
    ) AS columns,
    pg_get_constraintdef(con.oid, true) AS definition
FROM pg_constraint AS con
JOIN pg_class AS c
    ON c.oid = con.conrelid
JOIN pg_namespace AS n
    ON n.oid = c.relnamespace
WHERE n.nspname = %s
  AND c.relname = %s
  AND con.contype IN ('p', 'f', 'u', 'c', 'x')
ORDER BY con.conname
"""
