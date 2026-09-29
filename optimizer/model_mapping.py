from dataclasses import dataclass

from django.apps import apps


@dataclass(frozen=True)
class DjangoFieldReference:
    name: str
    column: str
    kind: str


@dataclass(frozen=True)
class DjangoModelReference:
    label: str
    schema: str
    table: str
    fields: tuple[DjangoFieldReference, ...]


@dataclass(frozen=True)
class DjangoModelMatch:
    status: str
    model: DjangoModelReference | None = None
    fields: tuple[DjangoFieldReference, ...] = ()


def build_model_map(models=None, *, default_schema="public"):
    """Map PostgreSQL table identities to concrete Django models."""
    models = apps.get_models() if models is None else models
    mapping = {}
    for model in models:
        options = model._meta
        if options.proxy or not options.managed:
            continue
        schema, table = split_db_table(options.db_table, default_schema=default_schema)
        fields = tuple(
            DjangoFieldReference(
                name=field.name,
                column=field.column,
                kind=_field_kind(field),
            )
            for field in options.concrete_fields
            if field.column is not None
        )
        reference = DjangoModelReference(
            label=options.label,
            schema=schema,
            table=table,
            fields=fields,
        )
        mapping.setdefault((schema, table), []).append(reference)
    return {key: tuple(value) for key, value in mapping.items()}


def match_model(model_map, schema, table, columns):
    """Resolve table and column identities without guessing ambiguous matches."""
    candidates = model_map.get((schema, table), ())
    if not candidates:
        return DjangoModelMatch(status="unmapped_table")
    if len(candidates) != 1:
        return DjangoModelMatch(status="ambiguous_table")

    model = candidates[0]
    fields_by_column = {field.column: field for field in model.fields}
    try:
        fields = tuple(fields_by_column[column] for column in columns)
    except KeyError:
        return DjangoModelMatch(status="unmapped_column", model=model)
    return DjangoModelMatch(status="matched", model=model, fields=fields)


def split_db_table(db_table, *, default_schema="public"):
    """Split Django's common schema-qualified ``db_table`` representations."""
    value = db_table.strip()
    if value.startswith('"') and value.endswith('"') and '"."' in value:
        schema, table = value[1:-1].split('"."', 1)
        return schema.replace('""', '"'), table.replace('""', '"')
    if "." in value and '"' not in value:
        return tuple(value.split(".", 1))
    return default_schema, value.strip('"').replace('""', '"')


def _field_kind(field):
    if getattr(field, "generated", False):
        return "generated"
    if field.is_relation:
        return "relation"
    return "field"
