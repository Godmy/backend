#!/usr/bin/env python3
"""
Fix triple single quotes (''') to triple double quotes (\"\"\") in Python files.
"""
import glob
import re

# Find all Python schema files
files = glob.glob("**/*schemas*.py", recursive=True)

for file_path in files:
    print(f"Processing: {file_path}")

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Replace description=''' with description=\"\"\"
        modified = re.sub(
            r'(description\s*=\s*)\'\'\'',
            r'\1"""',
            content
        )

        # Replace closing ''' with \"\"\" only after @strawberry decorators
        # Find patterns like @strawberry...description='''...'''
        modified = re.sub(
            r'(@strawberry\.(field|mutation|type)\([^)]*description\s*=\s*"""[^"]*?)\'\'\'',
            r'\1"""',
            modified,
            flags=re.DOTALL
        )

        if modified != content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(modified)
            print(f"  ✓ Updated")
        else:
            print(f"  - No changes")

    except Exception as e:
        print(f"  ✗ Error: {e}")

print("\nDone!")
