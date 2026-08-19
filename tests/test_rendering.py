from optimizer.rendering import create_index_sql
from optimizer.types import IndexRecommendation


def test_create_index_sql_quotes_every_identifier():
    recommendation = IndexRecommendation(
        schema="tenant data",
        table="Order",
        columns=("customer id",),
        index_name="order_customer_idx",
        calls=10,
        total_exec_time=100,
        mean_exec_time=10,
        query_ids=(42,),
        reason="Repeated filter.",
    )

    sql = create_index_sql(recommendation, lambda value: f'"{value}"')

    assert sql == (
        'CREATE INDEX CONCURRENTLY "order_customer_idx" ON '
        '"tenant data"."Order" ("customer id");'
    )
