"""PostgreSQL runtime inspection queries."""

LIST_SESSIONS_QUERY_ID = "PG_RUNTIME_LIST_SESSIONS"
LIST_QUERIES_QUERY_ID = "PG_RUNTIME_LIST_QUERIES"
LIST_TRANSACTIONS_QUERY_ID = "PG_RUNTIME_LIST_TRANSACTIONS"
LIST_WAITS_QUERY_ID = "PG_RUNTIME_LIST_WAITS"
LIST_LOCKS_QUERY_ID = "PG_RUNTIME_LIST_LOCKS"
LIST_BLOCKING_QUERY_ID = "PG_RUNTIME_LIST_BLOCKING"
CANCEL_QUERY_QUERY_ID = "PG_RUNTIME_CANCEL_QUERY"
TERMINATE_SESSION_QUERY_ID = "PG_RUNTIME_TERMINATE_SESSION"

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
WHERE (%s::name IS NULL OR datname = %s::name)
  AND (%s::name IS NULL OR usename = %s::name)
  AND (%s::text IS NULL OR state = %s::text)
  AND (%s::boolean OR pid <> pg_backend_pid())
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
  AND (%s::name IS NULL OR datname = %s::name)
  AND (%s::name IS NULL OR usename = %s::name)
  AND (%s::boolean OR pid <> pg_backend_pid())
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
  AND (%s::name IS NULL OR datname = %s::name)
  AND (%s::name IS NULL OR usename = %s::name)
  AND (%s::boolean OR pid <> pg_backend_pid())
ORDER BY xact_start, pid
"""

LIST_WAITS = """
SELECT
    pid,
    datname AS database_name,
    usename AS username,
    state,
    state_change,
    wait_event_type,
    wait_event,
    query
FROM pg_catalog.pg_stat_activity
WHERE wait_event IS NOT NULL
  AND (%s::name IS NULL OR datname = %s::name)
  AND (%s::name IS NULL OR usename = %s::name)
  AND (%s::text IS NULL OR wait_event_type = %s::text)
  AND (%s::boolean OR pid <> pg_backend_pid())
ORDER BY wait_event_type, wait_event, pid
"""

LIST_LOCKS = """
SELECT
    locks.pid,
    activity.datname AS database_name,
    activity.usename AS username,
    locks.locktype,
    locks.mode,
    locks.granted,
    locks.fastpath,
    namespace.nspname AS relation_schema,
    relation.relname AS relation_name,
    locks.transactionid::text AS transaction_id,
    locks.virtualxid::text AS virtual_transaction_id,
    locks.virtualtransaction,
    locks.page::bigint AS page,
    locks.tuple::bigint AS tuple_id
FROM pg_catalog.pg_locks AS locks
LEFT JOIN pg_catalog.pg_stat_activity AS activity
    ON activity.pid = locks.pid
LEFT JOIN pg_catalog.pg_class AS relation
    ON relation.oid = locks.relation
LEFT JOIN pg_catalog.pg_namespace AS namespace
    ON namespace.oid = relation.relnamespace
WHERE locks.pid IS NOT NULL
  AND (%s::name IS NULL OR activity.datname = %s::name)
  AND (%s::name IS NULL OR activity.usename = %s::name)
  AND (%s::boolean IS NULL OR locks.granted = %s::boolean)
  AND (%s::boolean OR locks.pid <> pg_backend_pid())
ORDER BY locks.granted, locks.pid, locks.locktype, locks.mode
"""

LIST_BLOCKING = """
WITH RECURSIVE blocking_chain AS (
    SELECT
        activity.pid AS root_pid,
        activity.pid AS blocked_pid,
        blocker.pid AS blocking_pid,
        1 AS depth,
        ARRAY[activity.pid, blocker.pid]::int[] AS path
    FROM pg_catalog.pg_stat_activity AS activity
    CROSS JOIN LATERAL
        unnest(pg_catalog.pg_blocking_pids(activity.pid)) AS blocker(pid)
    WHERE (%s::name IS NULL OR activity.datname = %s::name)
      AND (%s::name IS NULL OR activity.usename = %s::name)
      AND (%s::boolean OR activity.pid <> pg_backend_pid())

    UNION

    SELECT
        chain.root_pid,
        chain.blocking_pid AS blocked_pid,
        blocker.pid AS blocking_pid,
        chain.depth + 1,
        chain.path || blocker.pid
    FROM blocking_chain AS chain
    CROSS JOIN LATERAL
        unnest(pg_catalog.pg_blocking_pids(chain.blocking_pid)) AS blocker(pid)
    WHERE NOT blocker.pid = ANY(chain.path)
)
SELECT
    chain.root_pid,
    chain.blocked_pid,
    chain.blocking_pid,
    chain.depth,
    root.datname AS database_name,
    blocked.usename AS blocked_username,
    blocking.usename AS blocking_username,
    blocked.wait_event_type,
    blocked.wait_event,
    blocked.query AS blocked_query,
    blocking.query AS blocking_query
FROM blocking_chain AS chain
LEFT JOIN pg_catalog.pg_stat_activity AS root
    ON root.pid = chain.root_pid
LEFT JOIN pg_catalog.pg_stat_activity AS blocked
    ON blocked.pid = chain.blocked_pid
LEFT JOIN pg_catalog.pg_stat_activity AS blocking
    ON blocking.pid = chain.blocking_pid
ORDER BY chain.root_pid, chain.depth, chain.blocked_pid, chain.blocking_pid
"""


CANCEL_QUERY = """
WITH args AS (
    SELECT %s::integer AS target_pid
),
target AS (
    SELECT activity.pid, activity.backend_type, activity.state
    FROM pg_catalog.pg_stat_activity AS activity
    CROSS JOIN args
    WHERE activity.pid = args.target_pid
)
SELECT
    args.target_pid AS pid,
    EXISTS(SELECT 1 FROM target) AS target_exists,
    args.target_pid = pg_catalog.pg_backend_pid() AS self_target,
    COALESCE(
        (SELECT backend_type = 'client backend' FROM target),
        false
    ) AS client_backend,
    (SELECT backend_type FROM target) AS backend_type,
    COALESCE((SELECT state = 'active' FROM target), false) AS active_query,
    CASE
        WHEN args.target_pid = pg_catalog.pg_backend_pid() THEN false
        WHEN NOT EXISTS(SELECT 1 FROM target) THEN false
        WHEN NOT COALESCE(
            (SELECT backend_type = 'client backend' FROM target),
            false
        ) THEN false
        WHEN NOT COALESCE((SELECT state = 'active' FROM target), false) THEN false
        ELSE pg_catalog.pg_cancel_backend(args.target_pid)
    END AS changed
FROM args
"""

TERMINATE_SESSION = """
WITH args AS (
    SELECT %s::integer AS target_pid
),
target AS (
    SELECT activity.pid, activity.backend_type
    FROM pg_catalog.pg_stat_activity AS activity
    CROSS JOIN args
    WHERE activity.pid = args.target_pid
)
SELECT
    args.target_pid AS pid,
    EXISTS(SELECT 1 FROM target) AS target_exists,
    args.target_pid = pg_catalog.pg_backend_pid() AS self_target,
    COALESCE(
        (SELECT backend_type = 'client backend' FROM target),
        false
    ) AS client_backend,
    (SELECT backend_type FROM target) AS backend_type,
    NULL::boolean AS active_query,
    CASE
        WHEN args.target_pid = pg_catalog.pg_backend_pid() THEN false
        WHEN NOT EXISTS(SELECT 1 FROM target) THEN false
        WHEN NOT COALESCE(
            (SELECT backend_type = 'client backend' FROM target),
            false
        ) THEN false
        ELSE pg_catalog.pg_terminate_backend(args.target_pid)
    END AS changed
FROM args
"""
