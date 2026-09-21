"""PostgreSQL server queries."""

SERVER_INFO_QUERY_ID = "PG_SERVER_INFO"

SERVER_INFO = """
SELECT
    current_setting('server_version_num')::int AS server_version_num,
    current_database() AS current_database,
    current_user AS current_user
"""
