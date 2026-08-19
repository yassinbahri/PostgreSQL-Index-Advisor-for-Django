import json

from django.core.management.base import BaseCommand, CommandError
from django.db import DEFAULT_DB_ALIAS, connections
from django.db.utils import ConnectionDoesNotExist

from optimizer.analyzer import (
    QueryCollectionError,
    extract_query_patterns,
    get_frequent_queries,
)
from optimizer.recommender import recommend_indexes
from optimizer.rendering import create_index_sql


class Command(BaseCommand):
    help = "Preview index recommendations from pg_stat_statements."

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            type=int,
            default=50,
            help="Number of statements to inspect (default: 50).",
        )
        parser.add_argument(
            "--database",
            default=DEFAULT_DB_ALIAS,
            help="Database alias from settings.DATABASES (default: default).",
        )
        parser.add_argument(
            "--min-calls",
            type=int,
            default=5,
            help="Ignore query patterns executed fewer than this many times.",
        )
        parser.add_argument(
            "--format",
            choices=("text", "json"),
            default="text",
            help="Output human-readable text or machine-readable JSON.",
        )

    def handle(self, *args, **kwargs):
        limit = kwargs.get("limit", 50)
        min_calls = kwargs.get("min_calls", 5)
        output_format = kwargs.get("format", "text")
        database = kwargs.get("database", DEFAULT_DB_ALIAS)
        if limit <= 0:
            raise CommandError("--limit must be a positive integer.")
        if min_calls <= 0:
            raise CommandError("--min-calls must be a positive integer.")

        try:
            database_connection = connections[database]
        except ConnectionDoesNotExist as exc:
            raise CommandError(f"Unknown database alias: {database}") from exc
        if database_connection.vendor != "postgresql":
            raise CommandError(
                f"Database alias '{database}' uses {database_connection.vendor}, but "
                "django-index-optimizer currently supports PostgreSQL only."
            )

        try:
            query_stats = get_frequent_queries(limit=limit, using=database)
        except QueryCollectionError as exc:
            raise CommandError(str(exc)) from exc
        patterns = extract_query_patterns(query_stats)
        recommendations = recommend_indexes(
            patterns, min_calls=min_calls, using=database
        )

        if output_format == "json":
            payload = []
            for recommendation in recommendations:
                item = recommendation.as_dict()
                item["create_sql"] = create_index_sql(
                    recommendation, database_connection.ops.quote_name
                )
                payload.append(item)
            self.stdout.write(
                json.dumps(payload, indent=2)
            )
            return

        if not recommendations:
            self.stdout.write(self.style.SUCCESS("No missing indexes detected."))
            return

        self.stdout.write(
            self.style.WARNING(
                f"{len(recommendations)} recommendation(s). Review before applying."
            )
        )
        for recommendation in recommendations:
            columns = ", ".join(recommendation.columns)
            self.stdout.write(
                f"\n{recommendation.schema}.{recommendation.table} ({columns})"
            )
            self.stdout.write(f"  Suggested name: {recommendation.index_name}")
            self.stdout.write(f"  Evidence: {recommendation.reason}")
            self.stdout.write(
                "  SQL preview: "
                + create_index_sql(
                    recommendation, database_connection.ops.quote_name
                )
            )
