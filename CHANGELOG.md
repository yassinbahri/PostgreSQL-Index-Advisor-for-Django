# Changelog

## Unreleased

- Mapped PostgreSQL tables and columns to managed Django models and fields.
- Added reviewable `models.Index(fields=[...])` suggestions alongside SQL.
- Reported unmapped tables, ambiguous table ownership, and unmapped columns
  explicitly instead of guessing.
- Distinguished ordinary, relation, and generated Django fields in JSON
  recommendation evidence.
- Added read-only PostgreSQL table-size, estimated-row, scan, and write-activity
  evidence.
- Added an explainable 0-100 score with visible workload, table-impact,
  read-pressure, and write-penalty components.
- Suppressed tiny-table and strongly write-heavy candidates conservatively,
  while keeping recommendations when catalog statistics are unavailable.

## 0.2.1 - 2026-09-04

- Added CI-friendly non-zero exit mode for actionable recommendations.
- Added machine-readable JSON recommendation reports.

## 0.2.0 - 2026-08-19

- Replaced regex query extraction with PostgreSQL-aware SQL parsing.
- Updated collection for current `pg_stat_statements` timing columns.
- Added structured recommendations with workload evidence and query IDs.
- Suppressed candidates covered by valid existing index prefixes.
- Made the management command preview-only with text and JSON output.
- Safely quoted every identifier in generated SQL previews.
- Disabled the unsafe automatic index-application API from version 0.1.
- Added Django 5.2-6.1, Python 3.10-3.14, and PostgreSQL 14-17 testing.

## 0.1.0 - 2025-04-30

- Published the initial proof of concept.
