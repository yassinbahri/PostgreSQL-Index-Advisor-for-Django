from types import SimpleNamespace

from optimizer.model_mapping import build_model_map, match_model, split_db_table


def field(name, column, *, relation=False, generated=False):
    return SimpleNamespace(
        name=name,
        column=column,
        is_relation=relation,
        generated=generated,
    )


def model(label, db_table, fields, *, managed=True, proxy=False):
    return SimpleNamespace(
        _meta=SimpleNamespace(
            label=label,
            db_table=db_table,
            concrete_fields=fields,
            managed=managed,
            proxy=proxy,
        )
    )


def test_maps_database_columns_to_django_fields():
    book = model(
        "library.Book",
        "library_book",
        [
            field("id", "id"),
            field("author", "author_id", relation=True),
            field("published", "published_at"),
        ],
    )

    match = match_model(
        build_model_map([book]),
        "public",
        "library_book",
        ("author_id", "published_at"),
    )

    assert match.status == "matched"
    assert match.model.label == "library.Book"
    assert [(item.name, item.column, item.kind) for item in match.fields] == [
        ("author", "author_id", "relation"),
        ("published", "published_at", "field"),
    ]


def test_maps_schema_qualified_db_table():
    event = model("events.Event", '"analytics"."event"', [field("id", "id")])

    match = match_model(
        build_model_map([event]),
        "analytics",
        "event",
        ("id",),
    )

    assert match.status == "matched"
    assert match.model.label == "events.Event"


def test_generated_fields_are_distinguished():
    report = model(
        "reports.Report",
        "report",
        [field("search_vector", "search_vector", generated=True)],
    )

    match = match_model(
        build_model_map([report]),
        "public",
        "report",
        ("search_vector",),
    )

    assert match.fields[0].kind == "generated"


def test_unmanaged_and_proxy_models_are_not_mapped():
    unmanaged = model("legacy.Record", "record", [], managed=False)
    proxy = model("library.BookProxy", "library_book", [], proxy=True)

    assert build_model_map([unmanaged, proxy]) == {}


def test_unmapped_and_ambiguous_tables_are_explicit():
    assert match_model({}, "public", "missing", ("id",)).status == "unmapped_table"

    duplicate = object()
    model_map = {("public", "duplicate"): (duplicate, duplicate)}
    assert (
        match_model(model_map, "public", "duplicate", ("id",)).status
        == "ambiguous_table"
    )


def test_unmapped_column_does_not_return_partial_field_match():
    book = model("library.Book", "library_book", [field("id", "id")])
    match = match_model(
        build_model_map([book]),
        "public",
        "library_book",
        ("missing_column",),
    )

    assert match.status == "unmapped_column"
    assert match.model.label == "library.Book"
    assert match.fields == ()


def test_split_db_table_supports_common_django_forms():
    assert split_db_table("library_book") == ("public", "library_book")
    assert split_db_table("analytics.event") == ("analytics", "event")
    assert split_db_table('"analytics"."event"') == ("analytics", "event")
