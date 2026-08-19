# Troubleshooting `pg_stat_statements`

PostgreSQL Index Advisor for Django reads query statistics from PostgreSQL's
[`pg_stat_statements`](https://www.postgresql.org/docs/current/pgstatstatements.html)
extension. The extension has two separate setup steps: the module must be loaded by
the server, and the extension must be created in each database where it is used.

## Enable the extension on the server

Add `pg_stat_statements` to `shared_preload_libraries` in `postgresql.conf`:

```conf
shared_preload_libraries = 'pg_stat_statements'
```

Restart PostgreSQL after changing this setting. A reload is not enough because the
library is loaded when the server starts. If other libraries are already listed,
keep them and separate the names with commas.

## Create the extension in the application database

Connect to the database used by Django, then run:

```sql
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
```

The extension is created per database. Creating it in a maintenance database does
not make the view available in the application database.

## Verify the setup

Run these queries while connected to the application database:

```sql
SELECT extname, extversion
FROM pg_extension
WHERE extname = 'pg_stat_statements';

SELECT COUNT(*)
FROM pg_stat_statements;
```

An empty view can be normal immediately after a restart or when no tracked queries
have run yet. Run a few application queries and check again.

## Common errors

- `permission denied`: ask a database administrator to enable the server setting
  and create the extension, or grant the minimum permissions required by your
  PostgreSQL deployment. Do not solve this by sharing database credentials.
- `relation "pg_stat_statements" does not exist`: check that PostgreSQL was
  restarted after updating `shared_preload_libraries`, and that `CREATE EXTENSION`
  was run in the same database used by Django.
- No rows returned: run representative queries first, then query the view again.
  A restart also resets the accumulated statistics unless they are preserved by
  the server configuration.

## Managed PostgreSQL services

On hosted services, `shared_preload_libraries` and extension availability may be
controlled by the provider. Follow the provider's PostgreSQL extension guidance
and confirm that `pg_stat_statements` is supported before changing the Django
configuration.

When sharing a query from the view in an issue, remove credentials, tokens,
customer data, hostnames, and other sensitive literals first. Prefer a minimized
or parameterized example over a production query dump.
