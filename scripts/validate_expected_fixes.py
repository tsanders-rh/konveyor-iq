#!/usr/bin/env python3
"""
Validate that expected_fix code in test cases compiles successfully.

This script verifies that all expected_fix code segments in test case YAML files
can be successfully compiled, helping catch issues where the "correct" answer
doesn't actually compile.

Usage:
    python scripts/validate_expected_fixes.py
    python scripts/validate_expected_fixes.py --file benchmarks/test_cases/generated/quarkus.yaml
    python scripts/validate_expected_fixes.py --verbose
"""

import argparse
import sys
from pathlib import Path
from typing import List, Dict, Any
import yaml

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from benchmarks.schema import TestSuite
from evaluators.functional import FunctionalCorrectnessEvaluator


class ExpectedFixValidator:
    """Validates that expected_fix code segments compile successfully."""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.evaluator = FunctionalCorrectnessEvaluator({"compile_check": True})
        self.results = []

    def validate_file(self, file_path: Path) -> Dict[str, Any]:
        """Validate all expected_fix code in a test suite file."""
        print(f"\n{'='*80}")
        print(f"Validating: {file_path}")
        print(f"{'='*80}\n")

        # Load test suite
        with open(file_path, 'r') as f:
            data = yaml.safe_load(f)

        test_suite = TestSuite(**data)

        total_tests = 0
        passed = 0
        failed = 0
        failures = []

        # Iterate through all rules and test cases
        for rule in test_suite.rules:
            for test_case in rule.test_cases:
                total_tests += 1

                if not test_case.expected_fix:
                    if self.verbose:
                        print(f"⊘ {rule.rule_id} - {test_case.id}: No expected_fix defined (skipped)")
                    continue

                # Compile expected_fix
                compiles, error_msg = self.evaluator._compile_java(test_case.expected_fix)

                if compiles:
                    passed += 1
                    if self.verbose:
                        print(f"✓ {rule.rule_id} - {test_case.id}: Compiles successfully")
                else:
                    failed += 1
                    print(f"✗ {rule.rule_id} - {test_case.id}: COMPILATION FAILED")

                    failure = {
                        "file": str(file_path),
                        "rule_id": rule.rule_id,
                        "test_case_id": test_case.id,
                        "context": test_case.context,
                        "error": error_msg,
                        "code": test_case.expected_fix
                    }
                    failures.append(failure)

                    if self.verbose:
                        print(f"  Error: {error_msg}")
                        print()

        # Print summary for this file
        print(f"\n{'-'*80}")
        print(f"Summary for {file_path.name}:")
        print(f"  Total: {total_tests}")
        print(f"  Passed: {passed} ({passed/total_tests*100:.1f}%)" if total_tests > 0 else "  Passed: 0")
        print(f"  Failed: {failed} ({failed/total_tests*100:.1f}%)" if total_tests > 0 else "  Failed: 0")
        print(f"{'-'*80}\n")

        return {
            "file": str(file_path),
            "total": total_tests,
            "passed": passed,
            "failed": failed,
            "failures": failures
        }

    def validate_all(self, test_dir: Path) -> List[Dict[str, Any]]:
        """Validate all YAML files in the test directory."""
        yaml_files = list(test_dir.glob("**/*.yaml"))

        if not yaml_files:
            print(f"No YAML files found in {test_dir}")
            return []

        results = []
        for yaml_file in sorted(yaml_files):
            try:
                result = self.validate_file(yaml_file)
                results.append(result)
            except Exception as e:
                print(f"ERROR processing {yaml_file}: {e}")
                if self.verbose:
                    import traceback
                    traceback.print_exc()

        return results

    def print_overall_summary(self, results: List[Dict[str, Any]]):
        """Print overall summary across all files."""
        if not results:
            return

        print(f"\n{'='*80}")
        print("OVERALL SUMMARY")
        print(f"{'='*80}\n")

        total_files = len(results)
        total_tests = sum(r["total"] for r in results)
        total_passed = sum(r["passed"] for r in results)
        total_failed = sum(r["failed"] for r in results)

        print(f"Files Validated: {total_files}")
        print(f"Total Test Cases: {total_tests}")
        print(f"Passed: {total_passed} ({total_passed/total_tests*100:.1f}%)" if total_tests > 0 else "Passed: 0")
        print(f"Failed: {total_failed} ({total_failed/total_tests*100:.1f}%)" if total_tests > 0 else "Failed: 0")

        # Print detailed failures
        all_failures = []
        for result in results:
            all_failures.extend(result["failures"])

        if all_failures:
            print(f"\n{'='*80}")
            print("DETAILED FAILURES")
            print(f"{'='*80}\n")

            for i, failure in enumerate(all_failures, 1):
                print(f"{i}. {failure['rule_id']} - {failure['test_case_id']}")
                print(f"   File: {failure['file']}")
                print(f"   Context: {failure['context']}")
                print(f"\n   Compilation Error:")
                print(f"   {'-'*76}")
                for line in failure['error'].split('\n'):
                    print(f"   {line}")
                print(f"   {'-'*76}")
                print(f"\n   Expected Fix Code:")
                print(f"   {'-'*76}")
                for line in failure['code'].split('\n'):
                    print(f"   {line}")
                print(f"   {'-'*76}\n")

        print(f"{'='*80}\n")

        # Return exit code
        return 0 if total_failed == 0 else 1


def main():
    parser = argparse.ArgumentParser(
        description="Validate that expected_fix code segments compile successfully"
    )
    parser.add_argument(
        "--file",
        type=Path,
        help="Specific YAML file to validate (default: all files in benchmarks/test_cases/)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed output for all test cases"
    )

    args = parser.parse_args()

    validator = ExpectedFixValidator(verbose=args.verbose)

    if args.file:
        # Validate single file
        if not args.file.exists():
            print(f"Error: File not found: {args.file}")
            return 1

        result = validator.validate_file(args.file)
        results = [result]
    else:
        # Validate all files in test_cases directory
        test_dir = Path(__file__).parent.parent / "benchmarks" / "test_cases"
        results = validator.validate_all(test_dir)

    # Print overall summary and return exit code
    return validator.print_overall_summary(results)


if __name__ == "__main__":
    sys.exit(main())
