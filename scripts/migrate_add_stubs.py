#!/usr/bin/env python3
"""
Migration script to add stub generation to existing auto-generated test cases.

This script analyzes existing test YAML files and adds the test_code field
with auto-generated stubs for any test cases that don't already have it.

Usage:
    python scripts/migrate_add_stubs.py benchmarks/test_cases/generated/quarkus.yaml
    python scripts/migrate_add_stubs.py benchmarks/test_cases/generated/*.yaml --dry-run
"""
import argparse
import sys
import yaml
from pathlib import Path
from typing import Dict, Any, List

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from generate_tests import TestCaseGenerator


def migrate_test_suite(file_path: Path, dry_run: bool = False) -> Dict[str, Any]:
    """
    Migrate a test suite YAML file to add stubs.

    Args:
        file_path: Path to the YAML file
        dry_run: If True, show changes without writing

    Returns:
        Migration statistics
    """
    print(f"\nProcessing: {file_path}")

    # Load existing test suite
    with open(file_path, 'r') as f:
        test_suite = yaml.safe_load(f)

    if not test_suite or 'rules' not in test_suite:
        print(f"  ⚠ Skipping - not a valid test suite format")
        return {'skipped': 1}

    # Initialize generator for stub generation
    generator = TestCaseGenerator()

    stats = {
        'total_rules': len(test_suite['rules']),
        'updated': 0,
        'already_has_stubs': 0,
        'no_code': 0
    }

    # Process each rule
    for rule in test_suite['rules']:
        if 'test_cases' not in rule:
            continue

        for test_case in rule['test_cases']:
            # Check if test_code already exists
            if 'test_code' in test_case and test_case['test_code']:
                stats['already_has_stubs'] += 1
                continue

            # Check if we have code to analyze
            code_snippet = test_case.get('code_snippet', '')
            expected_fix = test_case.get('expected_fix', '')

            if not code_snippet or code_snippet.startswith('TODO'):
                stats['no_code'] += 1
                continue

            # Generate stubs
            try:
                stubs = generator._generate_test_stubs(code_snippet, expected_fix)

                if stubs:
                    test_case['test_code'] = stubs
                    stats['updated'] += 1
                    print(f"  ✓ Added stubs for {rule['rule_id']}")
                else:
                    # No stubs needed (self-contained code)
                    stats['no_code'] += 1

            except Exception as e:
                print(f"  ✗ Error processing {rule['rule_id']}: {e}")

    # Write back to file
    if not dry_run and stats['updated'] > 0:
        with open(file_path, 'w') as f:
            yaml.dump(test_suite, f, sort_keys=False, default_flow_style=False, width=120)
        print(f"\n✓ Updated {file_path}")

    return stats


def main():
    parser = argparse.ArgumentParser(
        description='Migrate existing test cases to include auto-generated stubs'
    )
    parser.add_argument(
        'files',
        nargs='+',
        help='Test suite YAML file(s) to migrate'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be changed without writing files'
    )

    args = parser.parse_args()

    # Process each file
    total_stats = {
        'total_files': 0,
        'total_rules': 0,
        'updated': 0,
        'already_has_stubs': 0,
        'no_code': 0,
        'skipped': 0
    }

    for file_pattern in args.files:
        file_path = Path(file_pattern)

        if file_path.is_file():
            files = [file_path]
        else:
            files = list(file_path.parent.glob(file_path.name))

        for f in files:
            if not f.exists():
                print(f"Warning: {f} does not exist")
                continue

            stats = migrate_test_suite(f, dry_run=args.dry_run)

            total_stats['total_files'] += 1
            for key in stats:
                total_stats[key] = total_stats.get(key, 0) + stats[key]

    # Print summary
    print("\n" + "=" * 70)
    print("Migration Summary")
    print("=" * 70)
    print(f"Files processed:         {total_stats['total_files']}")
    print(f"Total rules:             {total_stats['total_rules']}")
    print(f"Test cases updated:      {total_stats['updated']}")
    print(f"Already had stubs:       {total_stats['already_has_stubs']}")
    print(f"No external deps:        {total_stats['no_code']}")
    print(f"Skipped (no code):       {total_stats.get('skipped', 0)}")

    if args.dry_run:
        print("\n⚠ DRY RUN - No files were modified")
        print("Remove --dry-run to apply changes")
    else:
        print(f"\n✓ Migration complete!")

    print("=" * 70)


if __name__ == '__main__':
    main()
