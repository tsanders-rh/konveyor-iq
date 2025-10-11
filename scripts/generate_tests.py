#!/usr/bin/env python3
"""
Automated test case generator from Konveyor rulesets.

This script parses Konveyor YAML ruleset files and generates test case templates
that can be filled in with code examples.

Usage:
    # Generate from a single ruleset
    python scripts/generate_tests.py \
        --ruleset https://github.com/konveyor/rulesets/blob/main/default/generated/quarkus/200-ee-to-quarkus.windup.yaml \
        --output benchmarks/test_cases/generated/

    # Generate from all Quarkus rulesets
    python scripts/generate_tests.py --all-quarkus --output benchmarks/test_cases/generated/

    # Preview without writing files
    python scripts/generate_tests.py --ruleset URL --preview
"""
import argparse
import sys
import yaml
import requests
from pathlib import Path
from typing import List, Dict, Any, Optional
import re


class TestCaseGenerator:
    """Generate test cases from Konveyor rulesets."""

    def __init__(self, output_dir: str = "benchmarks/test_cases/generated"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_from_ruleset(
        self,
        ruleset_url: str,
        preview: bool = False,
        include_when: bool = True
    ) -> Optional[str]:
        """
        Generate test cases from a Konveyor ruleset.

        Args:
            ruleset_url: GitHub URL to the ruleset YAML file
            preview: If True, print to stdout instead of writing file
            include_when: Include 'when' condition as comments

        Returns:
            Path to generated file or None if preview mode
        """
        print(f"Fetching ruleset: {ruleset_url}")

        # Fetch ruleset
        raw_url = self._convert_to_raw_url(ruleset_url)
        if not raw_url:
            print(f"Error: Invalid GitHub URL: {ruleset_url}")
            return None

        try:
            response = requests.get(raw_url, timeout=10)
            response.raise_for_status()
            ruleset_data = yaml.safe_load(response.text)
        except Exception as e:
            print(f"Error fetching ruleset: {e}")
            return None

        if not isinstance(ruleset_data, list):
            print("Error: Ruleset is not a list of rules")
            return None

        print(f"Found {len(ruleset_data)} rules")

        # Extract ruleset name from URL
        ruleset_name = self._extract_ruleset_name(ruleset_url)

        # Generate test suite
        test_suite = self._create_test_suite(ruleset_data, ruleset_name, ruleset_url, include_when)

        # Convert to YAML
        yaml_content = yaml.dump(test_suite, sort_keys=False, default_flow_style=False, width=120)

        if preview:
            print("\n" + "=" * 80)
            print("Preview of generated test cases:")
            print("=" * 80)
            print(yaml_content)
            return None
        else:
            # Write to file
            output_file = self.output_dir / f"{ruleset_name}.yaml"
            output_file.write_text(yaml_content)
            print(f"\n✓ Generated test cases: {output_file}")
            print(f"  Rules: {len(ruleset_data)}")
            print(f"  Test cases: {len(ruleset_data)} (1 per rule)")
            return str(output_file)

    def generate_all_quarkus_rulesets(self, preview: bool = False) -> List[str]:
        """
        Generate test cases from all Quarkus rulesets.

        Args:
            preview: If True, only preview first ruleset

        Returns:
            List of generated file paths
        """
        print("Fetching list of Quarkus rulesets...")

        # Get list of ruleset files from GitHub
        api_url = "https://api.github.com/repos/konveyor/rulesets/contents/default/generated/quarkus"

        try:
            response = requests.get(api_url, timeout=10)
            response.raise_for_status()
            files = response.json()
        except Exception as e:
            print(f"Error fetching ruleset list: {e}")
            return []

        # Filter for YAML files
        yaml_files = [
            f for f in files
            if isinstance(f, dict) and f.get('name', '').endswith('.yaml')
        ]

        print(f"Found {len(yaml_files)} Quarkus rulesets\n")

        generated_files = []

        for i, file_info in enumerate(yaml_files, 1):
            file_url = f"https://github.com/konveyor/rulesets/blob/main/default/generated/quarkus/{file_info['name']}"

            print(f"[{i}/{len(yaml_files)}] Processing {file_info['name']}")

            if preview and i > 1:
                print("  Skipping (preview mode, showing first only)")
                continue

            result = self.generate_from_ruleset(file_url, preview=preview, include_when=True)
            if result:
                generated_files.append(result)

            print()

        if not preview:
            print(f"\n✓ Generated {len(generated_files)} test suite files in {self.output_dir}")

        return generated_files

    def _create_test_suite(
        self,
        rules: List[Dict[str, Any]],
        ruleset_name: str,
        source_url: str,
        include_when: bool
    ) -> Dict[str, Any]:
        """Create test suite structure from rules."""

        # Extract category from first rule or use generic
        category = "migration"
        if rules and isinstance(rules[0], dict):
            category = rules[0].get('category', 'migration')

        test_suite = {
            'name': self._format_suite_name(ruleset_name),
            'description': f'Test cases generated from {ruleset_name}',
            'version': '1.0.0',
            'metadata': {
                'source': 'Konveyor AI Migration Rules',
                'language': 'java',
                'generated_from': source_url,
                'category': category
            },
            'rules': []
        }

        for rule in rules:
            if not isinstance(rule, dict):
                continue

            rule_entry = self._create_rule_entry(rule, source_url, include_when)
            if rule_entry:
                test_suite['rules'].append(rule_entry)

        return test_suite

    def _create_rule_entry(
        self,
        rule: Dict[str, Any],
        source_url: str,
        include_when: bool
    ) -> Optional[Dict[str, Any]]:
        """Create a rule entry with test case template."""

        rule_id = rule.get('ruleID')
        if not rule_id:
            return None

        description = rule.get('description', 'No description available')
        message = rule.get('message', '')
        category = rule.get('category', 'migration')
        effort = rule.get('effort', 1)

        # Create rule entry
        rule_entry = {
            'rule_id': rule_id,
            'description': description,
            'severity': self._map_effort_to_severity(effort),
            'category': category,
            'source': source_url,
        }

        # Add migration pattern hint from message if available
        if message:
            migration_pattern = self._extract_migration_pattern(message)
            if migration_pattern:
                rule_entry['migration_pattern'] = migration_pattern

        # Create test case template
        test_case = {
            'id': 'tc001',
            'language': 'java',
            'context': f'TODO: Add context for {rule_id}',
            'code_snippet': self._create_code_snippet_placeholder(rule, include_when),
            'expected_fix': 'TODO: Add expected fix code here',
        }

        # Add comments with guidance
        if message:
            test_case['# konveyor_guidance'] = message

        rule_entry['test_cases'] = [test_case]

        return rule_entry

    def _create_code_snippet_placeholder(self, rule: Dict[str, Any], include_when: bool) -> str:
        """Create a code snippet placeholder with hints from the rule's 'when' condition."""

        if not include_when or 'when' not in rule:
            return "TODO: Add code snippet that violates this rule"

        when_condition = rule.get('when', {})

        # Try to extract hints from the 'when' condition
        hints = self._extract_code_hints_from_when(when_condition)

        if hints:
            return f"// TODO: Add code example\n// Hint: This rule detects {hints}\n// Example pattern: ...\n"
        else:
            return "TODO: Add code snippet that violates this rule"

    def _extract_code_hints_from_when(self, when_condition: Any) -> str:
        """Extract code pattern hints from the 'when' condition."""

        hints = []

        def extract_patterns(condition):
            """Recursively extract patterns from nested conditions."""
            if isinstance(condition, dict):
                # Look for 'java.referenced' patterns
                if 'java.referenced' in condition:
                    ref = condition['java.referenced']
                    if isinstance(ref, dict):
                        pattern = ref.get('pattern', '')
                        if pattern:
                            # Clean up regex patterns
                            clean_pattern = pattern.replace('.*', '').replace('\\', '')
                            hints.append(f"references to {clean_pattern}")

                # Look for annotation patterns
                if 'annotation' in condition:
                    annotation = condition.get('annotation', '')
                    if annotation:
                        hints.append(f"@{annotation} annotation")

                # Recurse into nested conditions
                for key in ['or', 'and', 'from']:
                    if key in condition:
                        items = condition[key]
                        if isinstance(items, list):
                            for item in items:
                                extract_patterns(item)
                        else:
                            extract_patterns(items)

        extract_patterns(when_condition)

        return ', '.join(hints) if hints else ''

    def _extract_migration_pattern(self, message: str) -> str:
        """Try to extract migration pattern from message (e.g., '@Stateless -> @ApplicationScoped')."""

        # Look for patterns like "replace X with Y" or "X -> Y"
        patterns = [
            r'replacing?\s+`([^`]+)`\s+(?:annotation\s+)?with\s+`([^`]+)`',
            r'`([^`]+)`\s+(?:should\s+)?be\s+replaced\s+(?:with|by)\s+`([^`]+)`',
            r'([A-Z@]\S+)\s*->\s*([A-Z@]\S+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                return f"{match.group(1)} -> {match.group(2)}"

        return None

    def _map_effort_to_severity(self, effort: int) -> str:
        """Map Konveyor effort score to severity level."""
        if effort <= 1:
            return "low"
        elif effort <= 3:
            return "medium"
        elif effort <= 5:
            return "high"
        else:
            return "critical"

    def _format_suite_name(self, ruleset_name: str) -> str:
        """Format ruleset name into readable suite name."""
        # Convert "200-ee-to-quarkus.windup" to "EE to Quarkus Migration"
        name = ruleset_name.replace('.windup', '').replace('-', ' ')
        # Remove leading numbers
        name = re.sub(r'^\d+\s+', '', name)
        # Title case
        return name.title()

    def _extract_ruleset_name(self, url: str) -> str:
        """Extract ruleset name from URL."""
        # Extract filename from URL
        filename = url.split('/')[-1]
        # Remove .yaml extension
        return filename.replace('.yaml', '')

    def _convert_to_raw_url(self, github_url: str) -> Optional[str]:
        """Convert GitHub blob URL to raw content URL."""
        if "raw.githubusercontent.com" in github_url:
            return github_url

        blob_pattern = r'https://github\.com/([^/]+)/([^/]+)/blob/(.+)'
        match = re.match(blob_pattern, github_url)

        if match:
            user, repo, path = match.groups()
            return f"https://raw.githubusercontent.com/{user}/{repo}/{path}"

        return None


def main():
    parser = argparse.ArgumentParser(
        description='Generate test cases from Konveyor rulesets',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate from a single ruleset
  python scripts/generate_tests.py \\
      --ruleset https://github.com/konveyor/rulesets/blob/main/default/generated/quarkus/200-ee-to-quarkus.windup.yaml

  # Generate from all Quarkus rulesets
  python scripts/generate_tests.py --all-quarkus

  # Preview without writing files
  python scripts/generate_tests.py --ruleset URL --preview

  # Specify output directory
  python scripts/generate_tests.py --all-quarkus --output benchmarks/test_cases/auto_generated/
        """
    )

    parser.add_argument(
        '--ruleset',
        type=str,
        help='URL to a specific Konveyor ruleset YAML file'
    )

    parser.add_argument(
        '--all-quarkus',
        action='store_true',
        help='Generate from all Quarkus rulesets'
    )

    parser.add_argument(
        '--output',
        type=str,
        default='benchmarks/test_cases/generated',
        help='Output directory for generated test cases (default: benchmarks/test_cases/generated)'
    )

    parser.add_argument(
        '--preview',
        action='store_true',
        help='Preview generated content without writing files'
    )

    parser.add_argument(
        '--no-when',
        action='store_true',
        help='Exclude when condition hints from code snippets'
    )

    args = parser.parse_args()

    # Validate arguments
    if not args.ruleset and not args.all_quarkus:
        parser.error("Must specify either --ruleset or --all-quarkus")

    if args.ruleset and args.all_quarkus:
        parser.error("Cannot specify both --ruleset and --all-quarkus")

    # Create generator
    generator = TestCaseGenerator(output_dir=args.output)

    # Generate test cases
    if args.all_quarkus:
        generated = generator.generate_all_quarkus_rulesets(preview=args.preview)
        if not args.preview:
            print(f"\n✓ Successfully generated {len(generated)} test suite files!")
            print(f"\nNext steps:")
            print(f"1. Review generated files in {args.output}/")
            print(f"2. Fill in TODO placeholders with actual code examples")
            print(f"3. Add expected_fix code for each test case")
            print(f"4. Run evaluation: python evaluate.py --benchmark {args.output}/")
    else:
        result = generator.generate_from_ruleset(
            args.ruleset,
            preview=args.preview,
            include_when=not args.no_when
        )
        if result:
            print(f"\n✓ Successfully generated test suite!")
            print(f"\nNext steps:")
            print(f"1. Review generated file: {result}")
            print(f"2. Fill in TODO placeholders with actual code examples")
            print(f"3. Add expected_fix code for each test case")


if __name__ == '__main__':
    main()
