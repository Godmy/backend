#!/usr/bin/env python3
"""
Script to fix database connection leaks in GraphQL schemas.
Replaces next(get_db()) with info.context["db"] pattern.
"""

import re
import sys
from pathlib import Path


def fix_file(filepath: Path) -> tuple[bool, int]:
    """
    Fix database connection leaks in a single file.

    Returns:
        (changed, num_replacements)
    """
    try:
        content = filepath.read_text(encoding='utf-8')
        original = content
        replacements = 0

        # Pattern 1: Find methods/functions that need info parameter
        # Look for strawberry field/mutation decorators followed by method definition
        method_pattern = r'(@strawberry\.(field|mutation)\s+def\s+\w+\([^)]*)'

        def add_info_param(match):
            params = match.group(1)
            # Check if info parameter already exists
            if 'info:' in params or 'info =' in params:
                return params
            # Add info parameter before closing paren
            if params.endswith('('):
                return params + 'info: strawberry.Info = None'
            else:
                return params + ', info: strawberry.Info = None'

        # First pass: add info parameter to methods
        content = re.sub(method_pattern, add_info_param, content)

        # Pattern 2: Replace get_db import and usage
        # Remove "from core.database import get_db" lines
        content = re.sub(r'\s*from core\.database import get_db\n', '', content)

        # Replace "db = next(get_db())" with "db = info.context["db"]"
        before_count = content.count('next(get_db())')
        content = re.sub(
            r'db = next\(get_db\(\)\)',
            'db = info.context["db"]',
            content
        )
        after_count = content.count('next(get_db())')
        replacements = before_count - after_count

        # Add comment for clarity
        if replacements > 0:
            content = re.sub(
                r'(db = info\.context\["db"\])',
                r'# Use DB session from context (no connection leak)\n        \1',
                content,
                count=replacements
            )

        # Check if anything changed
        if content != original:
            filepath.write_text(content, encoding='utf-8')
            return True, replacements
        return False, 0

    except Exception as e:
        print(f"Error processing {filepath}: {e}", file=sys.stderr)
        return False, 0


def main():
    """Fix all schema files."""
    backend_dir = Path(__file__).parent

    # Files to fix
    files_to_fix = [
        backend_dir / "auth" / "schemas" / "user.py",
        backend_dir / "auth" / "schemas" / "role.py",
        backend_dir / "auth" / "schemas" / "auth.py",
        backend_dir / "auth" / "schemas" / "admin.py",
        backend_dir / "core" / "schemas" / "soft_delete.py",
    ]

    total_changes = 0
    total_replacements = 0

    for filepath in files_to_fix:
        if not filepath.exists():
            print(f"⚠️  Skipping {filepath} (not found)")
            continue

        changed, replacements = fix_file(filepath)
        if changed:
            print(f"✅ Fixed {filepath.name}: {replacements} replacements")
            total_changes += 1
            total_replacements += replacements
        else:
            print(f"⏭️  Skipped {filepath.name} (no changes needed)")

    print(f"\n{'='*60}")
    print(f"Summary: Fixed {total_changes} files with {total_replacements} replacements")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
