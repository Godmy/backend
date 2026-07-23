"""
Generate an ER-diagram schema file from the backend SQLAlchemy models.

Reads Base.metadata (all models registered via import_all_models) and emits
the native ERD DSL consumed by stylist-svelte's erd widget
(src/lib/erd/component/organism/schema). That widget's parser
(schemaTextToDocument) understands this grammar:

    table <name> {
      <column> <type> [pk] [unique] [required] [-> <target_table>.<target_col>]
    }

An inline `-> table.col` on a column both marks the reference and creates the
dependency edge, so no separate dependency lines are needed.

Type labels are simplified (int/varchar/bool/...) since the diagram shows a
label, not a precise DDL type. Output goes to backend/schema.erd.txt and stdout;
paste it into the widget or wire it into erd/data.

Usage:
    python scripts/gen_erd.py                 # write schema.erd.txt + print
    python scripts/gen_erd.py --stdout        # print only, don't write the file
    python scripts/gen_erd.py -o path/to.txt  # write to a custom path
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.platform.db.database import Base
from core.platform.db.init_db import import_all_models

# SQLAlchemy type class name -> short ERD label. Fallback: lowercased class name.
_TYPE_LABELS = {
    "Integer": "int",
    "BigInteger": "bigint",
    "SmallInteger": "smallint",
    "String": "varchar",
    "Unicode": "varchar",
    "VARCHAR": "varchar",
    "Text": "text",
    "UnicodeText": "text",
    "Boolean": "bool",
    "DateTime": "timestamp",
    "Date": "date",
    "Time": "time",
    "Float": "float",
    "Numeric": "decimal",
    "JSON": "json",
    "JSONB": "jsonb",
    "Vector": "vector",
    "Enum": "enum",
    "UUID": "uuid",
    "LargeBinary": "bytea",
}


def type_label(column) -> str:
    name = column.type.__class__.__name__
    return _TYPE_LABELS.get(name, name.lower())


def column_line(column) -> str:
    tokens = [column.name, type_label(column)]

    if column.primary_key:
        tokens.append("pk")
    else:
        # `pk` already implies unique + not-null; only annotate non-PK columns.
        if column.unique:
            tokens.append("unique")
        if not column.nullable:
            tokens.append("required")

    # Inline reference for the first foreign key; this is what draws the edge.
    for fk in column.foreign_keys:
        target = fk.column  # resolved target Column
        tokens.append(f"-> {target.table.name}.{target.name}")
        break

    return "  " + " ".join(tokens)


def generate() -> str:
    import_all_models()

    lines: list[str] = [
        "# Auto-generated from backend SQLAlchemy models by scripts/gen_erd.py.",
        "# Do not edit by hand -- regenerate after model changes.",
        "",
    ]

    for table in sorted(Base.metadata.tables.values(), key=lambda t: t.name):
        lines.append(f"table {table.name} {{")
        # PK first (ER convention); everything else keeps definition order.
        columns = sorted(table.columns, key=lambda c: 0 if c.primary_key else 1)
        for column in columns:
            lines.append(column_line(column))
        lines.append("}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--stdout", action="store_true", help="Print only, don't write a file.")
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        help="Output path (default: backend/schema.erd.txt).",
    )
    args = parser.parse_args(argv)

    schema_text = generate()

    if not args.stdout:
        backend_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        output = args.output or os.path.join(backend_root, "schema.erd.txt")
        with open(output, "w", encoding="utf-8") as handle:
            handle.write(schema_text)
        print(f"# wrote {output}", file=sys.stderr)

    print(schema_text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
