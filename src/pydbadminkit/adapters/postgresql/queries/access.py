"""PostgreSQL explicit relation access queries."""

LIST_DIRECT_RELATION_ACCESS_QUERY_ID = "PG_LIST_DIRECT_RELATION_ACCESS"

LIST_DIRECT_RELATION_ACCESS = """
SELECT
    principal.rolname AS principal,
    issuer.rolname AS issuer,
    n.nspname AS schema_name,
    c.relname AS object_name,
    c.relkind AS relkind,
    acl.privilege_type AS access_type,
    acl.is_grantable AS delegable
FROM pg_class AS c
JOIN pg_namespace AS n
    ON n.oid = c.relnamespace
CROSS JOIN LATERAL aclexplode(c.relacl) AS acl
JOIN pg_roles AS principal
    ON principal.oid = acl.grantee
LEFT JOIN pg_roles AS issuer
    ON issuer.oid = acl.grantor
WHERE c.relkind IN ('r', 'p', 'v', 'm', 'f')
  AND principal.rolname = %s
  AND (%s::boolean OR n.nspname NOT LIKE 'pg_%')
  AND (%s::text IS NULL OR n.nspname = %s)
  AND (%s::text IS NULL OR c.relname = %s)
ORDER BY n.nspname, c.relname, acl.privilege_type
"""
