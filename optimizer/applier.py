class IndexApplicationDisabled(RuntimeError):
    """Raised when code attempts to apply an index automatically."""


def create_index(table_name, column_name):
    """Reject the unsafe automatic-application API retained from version 0.1."""
    raise IndexApplicationDisabled(
        "Automatic index creation is disabled. Run `python manage.py "
        "optimize_indexes`, review the previewed SQL, and apply it through your "
        "normal migration or database-change process."
    )
