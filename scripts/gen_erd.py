"""
Write an ER-diagram schema snapshot file from the backend SQLAlchemy models.

Thin CLI wrapper around core.route.admin.erd_service.generate_erd_schema_text
(shared with the live `erdSchema` GraphQL field so both stay in sync). Output
goes to backend/schema.erd.txt and stdout; paste it into the erd widget or
wire it into erd/data for a static snapshot.

Usage:
    python scripts/gen_erd.py                 # write schema.erd.txt + print
    python scripts/gen_erd.py --stdout        # print only, don't write the file
    python scripts/gen_erd.py -o path/to.txt  # write to a custom path
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.route.admin.erd_service import generate_erd_schema_text


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

    schema_text = generate_erd_schema_text()

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
