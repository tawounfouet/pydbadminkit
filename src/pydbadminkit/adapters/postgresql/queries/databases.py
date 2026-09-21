"""PostgreSQL database catalog queries."""

LIST_DATABASES_QUERY_ID = "PG_LIST_DATABASES"
GET_DATABASE_QUERY_ID = "PG_GET_DATABASE"

_DATABASE_SELECT = """
SELECT
    d.datname AS name,
    pg_get_userbyid(d.datdba) AS owner,
    pg_encoding_to_char(d.encoding) AS encoding,
    d.datcollate AS collation,
    d.datallowconn AS allow_connections,
    d.datconnlimit AS connection_limit,
    pg_database_size(d.oid) AS size_bytes
FROM pg_database AS d
"""

LIST_DATABASES = (
    _DATABASE_SELECT
    + """
WHERE NOT d.datistemplate
ORDER BY d.datname
"""
)

GET_DATABASE = (
    _DATABASE_SELECT
    + """
WHERE d.datname = %s
"""
)
