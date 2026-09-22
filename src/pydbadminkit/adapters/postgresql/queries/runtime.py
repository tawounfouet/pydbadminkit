"""PostgreSQL runtime inspection queries."""

LIST_SESSIONS_QUERY_ID = "PG_RUNTIME_LIST_SESSIONS"
LIST_QUERIES_QUERY_ID = "PG_RUNTIME_LIST_QUERIES"
LIST_TRANSACTIONS_QUERY_ID = "PG_RUNTIME_LIST_TRANSACTIONS"

LIST_SESSIONS = """
SELECT
    pid,
    datname AS database_name,
    usename AS username,
    application_name,
    client_addr::text AS client_address,
    backend_type,
    state,
    backend_start,
    state_change,
    wait_event_type,
    wait_event
FROM pg_catalog.pg_stat_activity
WHERE (%s IS NULL OR datname = %s)
  AND (%s IS NULL OR usename = %s)
  AND (%s IS NULL OR state = %s)
  AND (%s OR pid <> pg_backend_pid())
ORDER BY pid
"""

LIST_QUERIES = """
SELECT
    pid,
    datname AS database_name,
    usename AS username,
    query_id,
    state,
    query,
    query_start,
    (EXTRACT(EPOCH FROM (clock_timestamp() - query_start)) * 1000.0)::double precision
        AS elapsed_ms,
    wait_event_type,
    wait_event
FROM pg_catalog.pg_stat_activity
WHERE state = 'active'
  AND query_start IS NOT NULL
  AND (%s IS NULL OR datname = %s)
  AND (%s IS NULL OR usename = %s)
  AND (%s OR pid <> pg_backend_pid())
ORDER BY query_start, pid
"""

LIST_TRANSACTIONS = """
SELECT
    pid,
    datname AS database_name,
    usename AS username,
    state,
    xact_start,
    (EXTRACT(EPOCH FROM (clock_timestamp() - xact_start)) * 1000.0)::double precision
        AS elapsed_ms,
    backend_xid::text AS backend_xid,
    backend_xmin::text AS backend_xmin,
    query
FROM pg_catalog.pg_stat_activity
WHERE xact_start IS NOT NULL
  AND (%s IS NULL OR datname = %s)
  AND (%s IS NULL OR usename = %s)
  AND (%s OR pid <> pg_backend_pid())
ORDER BY xact_start, pid
"""
