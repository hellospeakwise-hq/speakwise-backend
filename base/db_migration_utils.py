"""Shared PostgreSQL helpers for UUID primary-key conversion migrations."""

FK_DISCOVERY_SQL = """
    SELECT
        tc.table_name,
        kcu.column_name,
        tc.constraint_name,
        pg_get_constraintdef(con.oid) AS constraint_def,
        (SELECT is_nullable FROM information_schema.columns c
         WHERE c.table_name = tc.table_name
           AND c.column_name = kcu.column_name
           AND c.table_schema = tc.table_schema) AS is_nullable
    FROM information_schema.table_constraints tc
    JOIN information_schema.key_column_usage kcu
      ON tc.constraint_name = kcu.constraint_name
      AND tc.table_schema = kcu.table_schema
    JOIN information_schema.constraint_column_usage ccu
      ON tc.constraint_name = ccu.constraint_name
      AND tc.table_schema = ccu.table_schema
    JOIN pg_constraint con
      ON con.conname = tc.constraint_name
    WHERE tc.constraint_type = 'FOREIGN KEY'
      AND ccu.table_name = ANY(%s);
"""


def discover_inbound_fk_constraints(cursor, target_pk_tables):
    """Return metadata for every FK constraint referencing the given tables."""
    cursor.execute(FK_DISCOVERY_SQL, [list(target_pk_tables)])
    return cursor.fetchall()


def drop_fk_constraints(cursor, fk_constraints):
    """Drop the discovered FK constraints and null out their columns."""
    for table_name, _column_name, constraint_name, _, _ in fk_constraints:
        cursor.execute(
            f'ALTER TABLE "{table_name}" DROP CONSTRAINT "{constraint_name}";'
        )


def convert_fk_columns_to_uuid(cursor, fk_constraints, already_handled):
    """Cast remaining FK columns to uuid, preserving their nullability flag."""
    converted = []
    for row in fk_constraints:
        table_name, column_name = row[0], row[1]
        is_nullable = row[4] == "YES"
        if (table_name, column_name) in already_handled:
            continue
        if not is_nullable:
            cursor.execute(
                f'ALTER TABLE "{table_name}" ALTER COLUMN "{column_name}" '
                f"DROP NOT NULL;"
            )
        cursor.execute(
            f'ALTER TABLE "{table_name}" ALTER COLUMN "{column_name}" '
            f"TYPE uuid USING (NULL);"
        )
        converted.append((table_name, column_name, is_nullable))
    return converted


def restore_fk_constraints(cursor, fk_constraints):
    """Recreate dropped FK constraints and their original NOT NULL state."""
    for (
        table_name,
        column_name,
        constraint_name,
        constraint_def,
        is_nullable,
    ) in fk_constraints:
        if is_nullable == "NO":
            cursor.execute(
                f'ALTER TABLE "{table_name}" ALTER COLUMN "{column_name}" '
                f"SET NOT NULL;"
            )
        cursor.execute(
            f'ALTER TABLE "{table_name}" '
            f'ADD CONSTRAINT "{constraint_name}" {constraint_def};'
        )


class FkConstraintSnapshot:
    """Captures inbound FK state across the phases of one migration run."""

    def __init__(self):
        """Initialize empty capture lists for constraint metadata."""
        self.captured = []
        self.converted_external_columns = []

    def drop(self, schema_editor, target_pk_tables, already_handled):
        """Discover, drop, and record FK constraints targeting the tables."""
        if schema_editor.connection.vendor != "postgresql":
            return
        cursor = schema_editor.connection.cursor()
        self.captured = discover_inbound_fk_constraints(cursor, target_pk_tables)
        drop_fk_constraints(cursor, self.captured)
        self.converted_external_columns = convert_fk_columns_to_uuid(
            cursor, self.captured, set(already_handled)
        )

    def convert_targets(self, schema_editor, statements):
        """Run the raw DDL converting each app's own columns to uuid."""
        if schema_editor.connection.vendor != "postgresql":
            return
        cursor = schema_editor.connection.cursor()
        for statement in statements:
            cursor.execute(statement)

    def restore(self, schema_editor):
        """Re-add every FK constraint removed during drop()."""
        if schema_editor.connection.vendor != "postgresql":
            return
        restore_fk_constraints(schema_editor.connection.cursor(), self.captured)
