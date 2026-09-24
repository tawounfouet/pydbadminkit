"""PostgreSQL monitoring queries."""

GET_CONNECTION_STATISTICS_QUERY_ID = "PG_MONITORING_CONNECTION_STATISTICS"
LIST_DATABASE_SIZES_QUERY_ID = "PG_MONITORING_DATABASE_SIZES"
LIST_TABLE_STATISTICS_QUERY_ID = "PG_MONITORING_TABLE_STATISTICS"
LIST_INDEX_STATISTICS_QUERY_ID = "PG_MONITORING_INDEX_STATISTICS"

GET_CONNECTION_STATISTICS = """
SELECT
    COUNT(*) FILTER (WHERE backend_type = 'client backend')::bigint AS total,
    COUNT(*) FILTER (
        WHERE backend_type = 'client backend' AND state = 'active'
    )::bigint AS active,
    COUNT(*) FILTER (
        WHERE backend_type = 'client backend' AND state = 'idle'
    )::bigint AS idle,
    COUNT(*) FILTER (
        WHERE backend_type = 'client backend'
          AND state IN ('idle in transaction', 'idle in transaction (aborted)')
    )::bigint AS idle_in_transaction,
    current_setting('max_connections')::int AS max_connections
FROM pg_catalog.pg_stat_activity
"""

LIST_DATABASE_SIZES = """
SELECT
    datname AS database,
    pg_catalog.pg_database_size(datname) AS size_bytes
FROM pg_catalog.pg_database
WHERE datallowconn
  AND NOT datistemplate
ORDER BY datname
"""

LIST_TABLE_STATISTICS = """
SELECT
    stats.schemaname AS schema_name,
    stats.relname AS table_name,
    CASE
        WHEN relation.reltuples < 0 THEN NULL
        ELSE relation.reltuples::bigint
    END AS estimated_rows,
    stats.seq_scan AS sequential_scans,
    stats.idx_scan AS index_scans,
    stats.n_live_tup AS live_tuples,
    stats.n_dead_tup AS dead_tuples,
    stats.n_tup_ins AS inserted_rows,
    stats.n_tup_upd AS updated_rows,
    stats.n_tup_del AS deleted_rows,
    stats.last_vacuum,
    stats.last_autovacuum,
    stats.last_analyze,
    stats.last_autoanalyze
FROM pg_catalog.pg_stat_user_tables AS stats
JOIN pg_catalog.pg_class AS relation
    ON relation.oid = stats.relid
WHERE (%s::text IS NULL OR stats.schemaname = %s)
  AND (%s::text IS NULL OR stats.relname = %s)
ORDER BY stats.schemaname, stats.relname
"""

LIST_INDEX_STATISTICS = """
SELECT
    stats.schemaname AS schema_name,
    stats.relname AS table_name,
    stats.indexrelname AS index_name,
    stats.idx_scan AS scans,
    stats.idx_tup_read AS tuples_read,
    stats.idx_tup_fetch AS tuples_fetched,
    pg_catalog.pg_relation_size(stats.indexrelid) AS size_bytes
FROM pg_catalog.pg_stat_user_indexes AS stats
WHERE (%s::text IS NULL OR stats.schemaname = %s)
  AND (%s::text IS NULL OR stats.indexrelname = %s)
ORDER BY stats.schemaname, stats.indexrelname
"""
