#!/usr/bin/env python3
"""
Extract imports from generated test cases and update stubs JAR.

This script analyzes test YAML files, extracts all imports used in code snippets
and expected fixes, and automatically generates missing stub files.

Usage:
    # Update stubs from a specific test file
    python scripts/update_stubs_from_tests.py benchmarks/test_cases/generated/quarkus.yaml

    # Update stubs from all generated tests
    python scripts/update_stubs_from_tests.py benchmarks/test_cases/generated/*.yaml

    # Preview what would be added without making changes
    python scripts/update_stubs_from_tests.py benchmarks/test_cases/generated/*.yaml --dry-run
"""
import argparse
import re
import yaml
from pathlib import Path
from typing import Set, Dict, List
import subprocess


class StubGenerator:
    """Generate stub files for missing Java imports."""

    # Known stub templates for different types
    ANNOTATION_TEMPLATE = """package {package};

import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

/**
 * Stub for {class_name} annotation.
 * Auto-generated for compilation testing.
 */
@Target({{ElementType.TYPE, ElementType.METHOD, ElementType.FIELD, ElementType.PARAMETER}})
@Retention(RetentionPolicy.RUNTIME)
public @interface {class_name} {{
}}
"""

    INTERFACE_TEMPLATE = """package {package};

/**
 * Stub for {class_name} interface.
 * Auto-generated for compilation testing.
 */
public interface {class_name} {{
}}
"""

    CLASS_TEMPLATE = """package {package};

/**
 * Stub for {class_name} class.
 * Auto-generated for compilation testing.
 */
public class {class_name} {{
}}
"""

    def __init__(self, stubs_dir: Path):
        """
        Initialize stub generator.

        Args:
            stubs_dir: Path to evaluators/stubs/src directory
        """
        self.stubs_dir = stubs_dir
        self.existing_stubs = self._scan_existing_stubs()

    def _scan_existing_stubs(self) -> Set[str]:
        """Scan existing stub files."""
        existing = set()
        if not self.stubs_dir.exists():
            return existing

        for java_file in self.stubs_dir.rglob("*.java"):
            # Convert path to fully qualified class name
            rel_path = java_file.relative_to(self.stubs_dir)
            fqcn = str(rel_path).replace('/', '.').replace('.java', '')
            existing.add(fqcn)

        return existing

    def extract_imports(self, code: str) -> Set[str]:
        """
        Extract import statements from Java code.

        Args:
            code: Java source code

        Returns:
            Set of fully qualified class names
        """
        imports = set()
        for match in re.finditer(r'import\s+(?:static\s+)?([a-zA-Z0-9_.]+);', code):
            import_path = match.group(1)
            # Skip wildcard imports
            if not import_path.endswith('*'):
                imports.add(import_path)

        return imports

    def generate_stub(self, fqcn: str, dry_run: bool = False) -> bool:
        """
        Generate a stub file for a fully qualified class name.

        Args:
            fqcn: Fully qualified class name (e.g., "org.eclipse.microprofile.config.Config")
            dry_run: If True, don't actually write files

        Returns:
            True if stub was generated (or would be in dry-run)
        """
        # Skip if already exists
        if fqcn in self.existing_stubs:
            return False

        # Skip standard Java classes
        if fqcn.startswith('java.') or fqcn.startswith('javax.'):
            # Only create stubs for javax.enterprise, javax.inject, etc.
            if not any(fqcn.startswith(p) for p in [
                'javax.enterprise', 'javax.inject', 'javax.persistence',
                'javax.transaction', 'javax.ejb', 'javax.jms'
            ]):
                return False

        # Parse package and class name
        parts = fqcn.split('.')
        class_name = parts[-1]
        package = '.'.join(parts[:-1])

        # Determine stub type based on naming conventions
        if class_name[0].isupper() and class_name[1].islower():
            # Likely an annotation or class
            # Check if it looks like an annotation (starts with uppercase, used with @)
            template = self.ANNOTATION_TEMPLATE if class_name in [
                'ConfigProperty', 'IfBuildProperty', 'PostConstruct', 'PreDestroy'
            ] else self.CLASS_TEMPLATE
        else:
            template = self.INTERFACE_TEMPLATE

        # Generate stub content
        stub_content = template.format(package=package, class_name=class_name)

        # Create file path
        package_path = self.stubs_dir / package.replace('.', '/')
        stub_file = package_path / f"{class_name}.java"

        if dry_run:
            print(f"  Would create: {stub_file.relative_to(self.stubs_dir.parent)}")
            return True

        # Create directory and write file
        package_path.mkdir(parents=True, exist_ok=True)
        stub_file.write_text(stub_content)
        print(f"  ✓ Created: {stub_file.relative_to(self.stubs_dir.parent)}")

        # Add to existing stubs
        self.existing_stubs.add(fqcn)
        return True


def extract_imports_from_test_suite(test_file: Path) -> Set[str]:
    """Extract all imports from a test suite YAML file."""
    with open(test_file, 'r') as f:
        test_suite = yaml.safe_load(f)

    if not test_suite or 'rules' not in test_suite:
        return set()

    all_imports = set()
    generator = StubGenerator(Path("evaluators/stubs/src"))

    for rule in test_suite['rules']:
        if 'test_cases' not in rule:
            continue

        for test_case in rule['test_cases']:
            # Extract from code_snippet
            if 'code_snippet' in test_case:
                all_imports.update(generator.extract_imports(test_case['code_snippet']))

            # Extract from expected_fix
            if 'expected_fix' in test_case:
                all_imports.update(generator.extract_imports(test_case['expected_fix']))

    return all_imports


def main():
    parser = argparse.ArgumentParser(
        description="Extract imports from test cases and generate missing stubs"
    )
    parser.add_argument(
        'test_files',
        nargs='+',
        type=Path,
        help="Test YAML files to analyze"
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help="Show what would be created without making changes"
    )
    parser.add_argument(
        '--rebuild',
        action='store_true',
        default=True,
        help="Rebuild stubs.jar after generating new stubs (default: True)"
    )

    args = parser.parse_args()

    # Initialize stub generator
    stubs_dir = Path("evaluators/stubs/src")
    if not stubs_dir.exists():
        print(f"Error: Stubs directory not found: {stubs_dir}")
        return 1

    generator = StubGenerator(stubs_dir)

    # Collect all imports from all test files
    print("Scanning test files for imports...")
    all_imports = set()
    for test_file in args.test_files:
        if not test_file.exists():
            print(f"  ⚠ Skipping: {test_file} (not found)")
            continue

        print(f"  • {test_file.name}")
        imports = extract_imports_from_test_suite(test_file)
        all_imports.update(imports)

    print(f"\nFound {len(all_imports)} unique imports")

    # Generate missing stubs
    print("\nGenerating missing stubs...")
    created_count = 0
    for fqcn in sorted(all_imports):
        if generator.generate_stub(fqcn, dry_run=args.dry_run):
            created_count += 1

    if created_count == 0:
        print("  ✓ All stubs already exist!")
    else:
        print(f"\nCreated {created_count} new stub files")

        # Rebuild stubs JAR
        if args.rebuild and not args.dry_run:
            print("\nRebuilding stubs.jar...")
            result = subprocess.run(
                ['bash', 'build.sh'],
                cwd='evaluators/stubs',
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                print("  ✓ Stubs JAR rebuilt successfully")
            else:
                print(f"  ✗ Failed to rebuild stubs JAR:")
                print(result.stderr)
                return 1

    return 0


if __name__ == '__main__':
    exit(main())
