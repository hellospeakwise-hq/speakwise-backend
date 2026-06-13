"""Utilities for writing database-backend-agnostic migrations."""


def is_postgres(schema_editor):
    """Return True if the database backend is PostgreSQL."""
    return schema_editor.connection.vendor == "postgresql"


def run_if_postgres(sql, reverse_sql=None):
    """Return a RunSQL operation that only executes on PostgreSQL.

    Usage::

        from base.migration_utils import run_if_postgres

        operations = [
            run_if_postgres(
                sql='CREATE EXTENSION IF NOT EXISTS "pgcrypto";',
            ),
        ]
    """
    from django.db import migrations

    def forward(apps, schema_editor):
        if is_postgres(schema_editor):
            schema_editor.execute(sql)

    def backward(apps, schema_editor):
        if reverse_sql and is_postgres(schema_editor):
            schema_editor.execute(reverse_sql)

    return migrations.RunPython(forward, backward)


def execute_sql_list_if_postgres(sql_list):
    """Return a RunPython that executes a list of SQL statements only on PostgreSQL.

    The SQL statements are executed in order. No-op on non-PostgreSQL backends.

    Usage::

        from base.migration_utils import execute_sql_list_if_postgres

        operations = [
            execute_sql_list_if_postgres([
                "ALTER TABLE foo ALTER COLUMN id TYPE uuid USING (gen_random_uuid());",
            ]),
        ]
    """
    from django.db import migrations

    def forward(apps, schema_editor):
        if is_postgres(schema_editor):
            for statement in sql_list:
                schema_editor.execute(statement)

    return migrations.RunPython(forward, migrations.RunPython.noop)
