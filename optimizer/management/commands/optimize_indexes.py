from django.core.management.base import BaseCommand
from optimizer.analyzer import get_frequent_queries, extract_query_patterns
from optimizer.recommender import recommend_indexes
from optimizer.applier import create_index

class Command(BaseCommand):
  help = 'Analyze pg_stat_statements and create suggested indexes.'

  def handle(self, *args, **kwargs):
    self.stdout.write("Fetching slow queries...")
    queries = get_frequent_queries()

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
