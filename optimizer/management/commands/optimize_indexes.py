from django.core.management.base import BaseCommand, CommandError

from optimizer.analyzer import extract_query_patterns, get_frequent_queries
from optimizer.applier import create_index
from optimizer.recommender import recommend_indexes


class Command(BaseCommand):
    help = "Analyze pg_stat_statements and create suggested indexes."

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            type=int,
            default=50,
            help="Number of statements to inspect (default: 50).",
        )

    def handle(self, *args, **kwargs):
        limit = kwargs.get("limit", 50)
        if limit <= 0:
            raise CommandError("--limit must be a positive integer.")

        self.stdout.write("Fetching slow queries...")
        queries = get_frequent_queries(limit=limit)

        self.stdout.write("Analyzing query patterns...")
        column_stats = extract_query_patterns(queries)

        self.stdout.write("Recommending indexes...")
        recommendations = recommend_indexes(column_stats)

        for recommendation in recommendations:
            table_name = recommendation.get("table")
            column_name = recommendation.get("column")
            if not table_name or not column_name:
                continue

            self.stdout.write(f"Creating index on {table_name}.{column_name}...")
            create_index(table_name, column_name)

        self.stdout.write(self.style.SUCCESS("Index optimization completed."))