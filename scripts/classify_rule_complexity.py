#!/usr/bin/env python3
"""
Automatically classify migration complexity of rules based on pattern analysis.

This script analyzes rules and assigns migration_complexity levels:
- TRIVIAL: Mechanical changes (namespace, simple renames)
- LOW: Straightforward API equivalents
- MEDIUM: Requires context understanding
- HIGH: Architectural changes
- EXPERT: Likely needs human review

Usage:
    python scripts/classify_rule_complexity.py benchmarks/test_cases/generated/quarkus.yaml
    python scripts/classify_rule_complexity.py benchmarks/test_cases/generated/quarkus.yaml --dry-run
    python scripts/classify_rule_complexity.py benchmarks/test_cases/generated/quarkus.yaml --verbose
"""

import argparse
import sys
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
import yaml

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from benchmarks.schema import TestSuite, MigrationComplexity


class ComplexityClassifier:
    """Classify migration complexity based on pattern analysis."""

    # Keywords that indicate different complexity levels
    TRIVIAL_PATTERNS = [
        r'javax\.',  # Namespace changes
        r'import.*javax',
        r'package name',
        r'namespace',
    ]

    LOW_PATTERNS = [
        r'@Stateless',
        r'@Singleton',
        r'@ApplicationScoped',
        r'@Inject',
        r'@Autowired',
        r'simple.*replacement',
        r'replace.*annotation',
        r'CDI',
    ]

    MEDIUM_PATTERNS = [
        r'@MessageDriven',
        r'reactive',
        r'@ConfigProperty',
        r'configuration',
        r'@Transactional',
        r'messaging',
        r'JMS',
    ]

    HIGH_PATTERNS = [
        r'security',
        r'authentication',
        r'authorization',
        r'@EnableWebSecurity',
        r'SecurityConfig',
        r'WebSecurityConfigurerAdapter',
        r'complex.*migration',
        r'architectural',
    ]

    EXPERT_PATTERNS = [
        r'custom.*realm',
        r'SecurityDomain',
        r'performance.*critical',
        r'transaction.*boundary',
        r'distributed',
        r'cluster',
    ]

    def __init__(self, verbose: bool = False):
        self.verbose = verbose

    def _match_patterns(self, text: str, patterns: List[str]) -> int:
        """Count how many patterns match in the text."""
        count = 0
        text_lower = text.lower()
        for pattern in patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                count += 1
        return count

    def _analyze_imports(self, code: str) -> Dict[str, int]:
        """Analyze import complexity."""
        imports = re.findall(r'import\s+([\w.]+)', code)

        metrics = {
            'total_imports': len(imports),
            'javax_imports': sum(1 for i in imports if 'javax.' in i),
            'jakarta_imports': sum(1 for i in imports if 'jakarta.' in i),
            'spring_imports': sum(1 for i in imports if 'springframework' in i),
            'quarkus_imports': sum(1 for i in imports if 'quarkus' in i),
            'security_imports': sum(1 for i in imports if 'security' in i.lower()),
            'wildfly_imports': sum(1 for i in imports if 'wildfly' in i),
        }

        return metrics

    def _analyze_annotations(self, code: str) -> Dict[str, int]:
        """Analyze annotation complexity."""
        annotations = re.findall(r'@(\w+)', code)

        complex_annotations = [
            'EnableWebSecurity', 'MessageDriven', 'SecurityConfig',
            'ConfigurationProperties', 'Transactional'
        ]

        return {
            'total_annotations': len(annotations),
            'complex_annotations': sum(1 for a in annotations if a in complex_annotations),
        }

    def classify_rule(self, rule: Any) -> MigrationComplexity:
        """
        Classify a rule's migration complexity.

        Algorithm:
        1. Analyze rule description and test case code
        2. Count pattern matches for each complexity level
        3. Score based on weighted criteria
        4. Return highest matching complexity level
        """
        # Gather all text to analyze
        text_parts = [
            rule.description,
            rule.rule_id,
        ]

        # Add test case snippets and expected fixes
        for tc in rule.test_cases:
            if tc.code_snippet:
                text_parts.append(tc.code_snippet)
            if tc.expected_fix:
                text_parts.append(tc.expected_fix)
            if tc.context:
                text_parts.append(tc.context)

        combined_text = '\n'.join(text_parts)

        # Count pattern matches
        expert_score = self._match_patterns(combined_text, self.EXPERT_PATTERNS)
        high_score = self._match_patterns(combined_text, self.HIGH_PATTERNS)
        medium_score = self._match_patterns(combined_text, self.MEDIUM_PATTERNS)
        low_score = self._match_patterns(combined_text, self.LOW_PATTERNS)
        trivial_score = self._match_patterns(combined_text, self.TRIVIAL_PATTERNS)

        # Analyze code structure
        import_metrics = self._analyze_imports(combined_text)
        annotation_metrics = self._analyze_annotations(combined_text)

        # Decision logic
        if expert_score > 0:
            complexity = MigrationComplexity.EXPERT
        elif high_score > 0 or annotation_metrics['complex_annotations'] > 2:
            complexity = MigrationComplexity.HIGH
        elif medium_score > 1 or import_metrics['security_imports'] > 0:
            complexity = MigrationComplexity.MEDIUM
        elif low_score > 0 or annotation_metrics['total_annotations'] > 0:
            complexity = MigrationComplexity.LOW
        elif trivial_score > 0 and import_metrics['javax_imports'] > 0:
            complexity = MigrationComplexity.TRIVIAL
        else:
            # Default to LOW for unknown patterns
            complexity = MigrationComplexity.LOW

        if self.verbose:
            print(f"\n{rule.rule_id}:")
            print(f"  Scores: Expert={expert_score}, High={high_score}, Medium={medium_score}, Low={low_score}, Trivial={trivial_score}")
            print(f"  Imports: {import_metrics}")
            print(f"  Annotations: {annotation_metrics}")
            print(f"  → Classified as: {complexity.value}")

        return complexity

    def classify_file(
        self,
        file_path: Path,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """Classify all rules in a file and optionally update the file."""

        print(f"Classifying rules in: {file_path}")
        print(f"{'='*80}\n")

        # Load test suite
        with open(file_path, 'r') as f:
            data = yaml.safe_load(f)

        test_suite = TestSuite(**data)

        # Track statistics
        stats = {
            MigrationComplexity.TRIVIAL: 0,
            MigrationComplexity.LOW: 0,
            MigrationComplexity.MEDIUM: 0,
            MigrationComplexity.HIGH: 0,
            MigrationComplexity.EXPERT: 0,
        }

        changes = []

        # Classify each rule
        for rule in test_suite.rules:
            complexity = self.classify_rule(rule)
            stats[complexity] += 1

            # Track change if different from current
            if rule.migration_complexity != complexity:
                changes.append({
                    'rule_id': rule.rule_id,
                    'old': rule.migration_complexity.value if rule.migration_complexity else 'None',
                    'new': complexity.value
                })

                # Update in memory
                rule.migration_complexity = complexity

                print(f"✓ {rule.rule_id}: {complexity.value}")
            else:
                print(f"  {rule.rule_id}: {complexity.value} (unchanged)")

        # Print statistics
        print(f"\n{'='*80}")
        print("Classification Summary:")
        print(f"  TRIVIAL: {stats[MigrationComplexity.TRIVIAL]} rules (namespace changes, mechanical fixes)")
        print(f"  LOW:     {stats[MigrationComplexity.LOW]} rules (simple API equivalents)")
        print(f"  MEDIUM:  {stats[MigrationComplexity.MEDIUM]} rules (requires context understanding)")
        print(f"  HIGH:    {stats[MigrationComplexity.HIGH]} rules (architectural changes)")
        print(f"  EXPERT:  {stats[MigrationComplexity.EXPERT]} rules (likely needs human review)")
        print(f"\nTotal changes: {len(changes)}")

        if not dry_run and changes:
            # Update the YAML file
            print(f"\nUpdating {file_path}...")

            # Rebuild data dict with classifications
            for i, rule in enumerate(test_suite.rules):
                if rule.migration_complexity:
                    data['rules'][i]['migration_complexity'] = rule.migration_complexity.value

            # Write back
            with open(file_path, 'w') as f:
                yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

            print(f"✓ Updated {file_path}")
        elif dry_run:
            print("\n(Dry run - no changes written)")

        return {
            'stats': stats,
            'changes': changes
        }


def main():
    parser = argparse.ArgumentParser(
        description="Classify migration complexity of rules",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Classify and update file
  python scripts/classify_rule_complexity.py benchmarks/test_cases/generated/quarkus.yaml

  # Dry run (show classifications without updating)
  python scripts/classify_rule_complexity.py benchmarks/test_cases/generated/quarkus.yaml --dry-run

  # Verbose output with scoring details
  python scripts/classify_rule_complexity.py benchmarks/test_cases/generated/quarkus.yaml --verbose
        """
    )

    parser.add_argument(
        'file',
        type=Path,
        help='Path to test case YAML file'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show classifications without updating file'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show detailed scoring information'
    )

    args = parser.parse_args()

    if not args.file.exists():
        print(f"Error: File not found: {args.file}")
        sys.exit(1)

    classifier = ComplexityClassifier(verbose=args.verbose)
    classifier.classify_file(args.file, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
