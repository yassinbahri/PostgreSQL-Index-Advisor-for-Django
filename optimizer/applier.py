from django.db import connection

def create_index(table_name, column_name):
    index_name = f"auto_idx_{table_name}_{column_name}"
    with connection.cursor() as cursor:
        cursor.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_indexes 
                    WHERE tablename = %s AND indexname = %s
                ) THEN
                    EXECUTE format('CREATE INDEX CONCURRENTLY %I ON %I (%I)', %s, %s, %s);
                END IF;
            END
            $$;
        """, [table_name, index_name, index_name, table_name, column_name])
