def create_index_sql(recommendation, quote_name):
    index_name = quote_name(recommendation.index_name)
    schema = quote_name(recommendation.schema)
    table = quote_name(recommendation.table)
    columns = ", ".join(quote_name(column) for column in recommendation.columns)
    return f"CREATE INDEX CONCURRENTLY {index_name} ON {schema}.{table} ({columns});"
