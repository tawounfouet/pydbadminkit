"""PostgreSQL effective relation access query."""

LIST_EFFECTIVE_RELATION_ACCESS_QUERY_ID = "PG_LIST_EFFECTIVE_RELATION_ACCESS"

LIST_EFFECTIVE_RELATION_ACCESS = """
WITH principal AS (
    SELECT oid, rolname, rolsuper
    FROM pg_roles
    WHERE rolname = %s
),
access_types(access_type) AS (
    VALUES
        ('SELECT'),
        ('INSERT'),
        ('UPDATE'),
        ('DELETE'),
        ('TRUNCATE'),
        ('REFERENCES'),
        ('TRIGGER')
)
SELECT
    p.rolname AS principal,
    n.nspname AS schema_name,
    c.relname AS object_name,
    c.relkind AS relkind,
    access_types.access_type,
    EXISTS (
        SELECT 1
        FROM aclexplode(c.relacl) AS acl
        WHERE acl.grantee = p.oid
          AND acl.privilege_type = access_types.access_type
    ) AS source_direct,
    (
        EXISTS (
            SELECT 1
            FROM aclexplode(c.relacl) AS acl
            WHERE acl.grantee <> 0
              AND acl.grantee <> p.oid
              AND acl.privilege_type = access_types.access_type
              AND pg_has_role(p.oid, acl.grantee, 'USAGE')
        )
        OR (
            c.relowner <> p.oid
            AND pg_has_role(p.oid, c.relowner, 'USAGE')
        )
    ) AS source_inherited,
    EXISTS (
        SELECT 1
        FROM aclexplode(c.relacl) AS acl
        WHERE acl.grantee = 0
          AND acl.privilege_type = access_types.access_type
    ) AS source_public,
    c.relowner = p.oid AS source_owner,
    p.rolsuper AS source_superuser
FROM principal AS p
CROSS JOIN pg_class AS c
JOIN pg_namespace AS n
    ON n.oid = c.relnamespace
CROSS JOIN access_types
WHERE c.relkind IN ('r', 'p', 'v', 'm', 'f')
  AND has_table_privilege(p.oid, c.oid, access_types.access_type)
  AND (
      %s::boolean
      OR (
          n.nspname NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
          AND n.nspname NOT LIKE 'pg_temp_%%'
          AND n.nspname NOT LIKE 'pg_toast_temp_%%'
      )
  )
  AND (%s::text IS NULL OR n.nspname = %s)
  AND (%s::text IS NULL OR c.relname = %s)
ORDER BY n.nspname, c.relname, access_types.access_type
"""
