#!/usr/bin/env python3
"""
Automatically fix compilation errors in expected_fix code using an LLM.

This script:
1. Validates all expected_fix code segments
2. For each compilation failure, uses an LLM to fix the error
3. Validates the fix compiles successfully
4. Updates the YAML file with the corrected code

Usage:
    python scripts/fix_expected_fixes.py --file benchmarks/test_cases/generated/quarkus.yaml
    python scripts/fix_expected_fixes.py --file benchmarks/test_cases/generated/quarkus.yaml --model gpt-4-turbo
    python scripts/fix_expected_fixes.py --file benchmarks/test_cases/generated/quarkus.yaml --dry-run
    python scripts/fix_expected_fixes.py --file benchmarks/test_cases/generated/quarkus.yaml --rule-id jms-to-reactive-quarkus-00010
"""

import argparse
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
import yaml

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from benchmarks.schema import TestSuite
from evaluators.functional import FunctionalCorrectnessEvaluator
from models import get_model


class ExpectedFixFixer:
    """Automatically fix compilation errors in expected_fix code."""

    def __init__(self, model_name: str = "gpt-4-turbo", dry_run: bool = False, verbose: bool = False):
        self.model = get_model(model_name, api_key=None, config={})
        self.dry_run = dry_run
        self.verbose = verbose
        self.evaluator = FunctionalCorrectnessEvaluator({"compile_check": True})

    def build_fix_prompt(
        self,
        original_code: str,
        expected_fix: str,
        compilation_error: str,
        context: str
    ) -> str:
        """Build prompt for LLM to fix compilation error."""
        return f"""You are fixing a compilation error in a code migration example.

CONTEXT:
{context}

ORIGINAL CODE (before migration):
```java
{original_code}
```

EXPECTED FIX (after migration - CURRENTLY HAS COMPILATION ERROR):
```java
{expected_fix}
```

COMPILATION ERROR:
```
{compilation_error}
```

Your task: Fix ONLY the compilation error in the EXPECTED FIX code while preserving the migration pattern.

IMPORTANT RULES:
1. Fix ONLY the compilation error - don't change the migration approach
2. If there's an ambiguous import (e.g., both javax.jms.Message and org.eclipse.microprofile.reactive.messaging.Message):
   - Remove the conflicting import OR use fully qualified names
   - Prefer simpler types (String) over complex types if semantically equivalent
3. If a class is undefined (e.g., Employee, User):
   - Keep the code as-is (stub classes will be added separately)
   - This is NOT a compilation error you should fix
4. Preserve all imports, annotations, and migration patterns from the original expected fix
5. Return ONLY the complete fixed Java code, no explanations

Format your response as:
FIXED CODE:
```java
[complete fixed code here]
```"""

    def extract_fixed_code(self, response: str) -> Optional[str]:
        """Extract fixed code from LLM response."""
        # Look for code block
        import re

        # Try FIXED CODE: format first
        match = re.search(r'FIXED CODE:\s*```(?:java)?\s*\n(.*?)\n```', response, re.DOTALL)
        if match:
            return match.group(1).strip()

        # Try any code block
        match = re.search(r'```(?:java)?\s*\n(.*?)\n```', response, re.DOTALL)
        if match:
            return match.group(1).strip()

        return None

    def fix_test_case(
        self,
        rule_id: str,
        test_case_id: str,
        original_code: str,
        expected_fix: str,
        compilation_error: str,
        context: str,
        max_attempts: int = 3
    ) -> Optional[str]:
        """Attempt to fix a failing test case."""

        print(f"\n{'─'*80}")
        print(f"Fixing: {rule_id} - {test_case_id}")
        print(f"{'─'*80}")

        current_fix = expected_fix

        for attempt in range(1, max_attempts + 1):
            print(f"\nAttempt {attempt}/{max_attempts}...")

            # Build prompt
            prompt = self.build_fix_prompt(
                original_code,
                current_fix,
                compilation_error,
                context
            )

            # Get fix from LLM
            print("  → Querying LLM for fix...")
            result = self.model.generate(prompt)

            if self.verbose:
                print(f"\nLLM Response:\n{result['response']}\n")

            # Extract fixed code
            fixed_code = self.extract_fixed_code(result['response'])

            if not fixed_code:
                print("  ✗ Failed to extract fixed code from LLM response")
                continue

            # Validate fix compiles
            print("  → Validating fix compiles...")
            compiles, error_msg = self.evaluator._compile_java(fixed_code)

            if compiles:
                print(f"  ✓ Fix compiles successfully!")
                return fixed_code
            else:
                print(f"  ✗ Fix still has compilation errors")
                if self.verbose:
                    print(f"\n{error_msg}\n")

                # Update for next attempt
                current_fix = fixed_code
                compilation_error = error_msg

        print(f"\n  ✗ Failed to fix after {max_attempts} attempts")
        return None

    def fix_yaml_file(
        self,
        file_path: Path,
        rule_id_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """Fix all compilation errors in a YAML file."""

        print(f"\n{'='*80}")
        print(f"Processing: {file_path}")
        print(f"{'='*80}")

        # Load original YAML (preserve formatting)
        with open(file_path, 'r') as f:
            original_yaml = f.read()

        # Load as dict for modification
        with open(file_path, 'r') as f:
            data = yaml.safe_load(f)

        test_suite = TestSuite(**data)

        fixes_applied = 0
        fixes_failed = 0
        total_failures = 0

        # Track modifications
        modifications = []

        # Iterate through all rules and test cases
        for rule in test_suite.rules:
            # Skip if filtering by rule_id
            if rule_id_filter and rule.rule_id != rule_id_filter:
                continue

            for test_case in rule.test_cases:
                if not test_case.expected_fix:
                    continue

                # Check if expected_fix compiles
                compiles, error_msg = self.evaluator._compile_java(test_case.expected_fix)

                if compiles:
                    if self.verbose:
                        print(f"✓ {rule.rule_id} - {test_case.id}: Already compiles")
                    continue

                total_failures += 1

                # Attempt to fix
                fixed_code = self.fix_test_case(
                    rule.rule_id,
                    test_case.id,
                    test_case.code_snippet,
                    test_case.expected_fix,
                    error_msg,
                    test_case.context
                )

                if fixed_code:
                    fixes_applied += 1
                    modifications.append({
                        "rule_id": rule.rule_id,
                        "test_case_id": test_case.id,
                        "old_code": test_case.expected_fix,
                        "new_code": fixed_code
                    })

                    # Update in-memory structure
                    test_case.expected_fix = fixed_code
                else:
                    fixes_failed += 1

        # Apply modifications to YAML file
        if modifications and not self.dry_run:
            print(f"\n{'='*80}")
            print(f"Applying {len(modifications)} fix(es) to {file_path}")
            print(f"{'='*80}\n")

            # Update YAML data structure
            for mod in modifications:
                # Find and update the test case in the data dict
                for rule_idx, rule in enumerate(data['rules']):
                    if rule['rule_id'] == mod['rule_id']:
                        for tc_idx, tc in enumerate(rule['test_cases']):
                            if tc['id'] == mod['test_case_id']:
                                data['rules'][rule_idx]['test_cases'][tc_idx]['expected_fix'] = mod['new_code']

            # Write updated YAML
            with open(file_path, 'w') as f:
                yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

            print(f"✓ Updated {file_path}")

        # Print summary
        print(f"\n{'='*80}")
        print("SUMMARY")
        print(f"{'='*80}")
        print(f"Total compilation failures: {total_failures}")
        print(f"Fixes applied: {fixes_applied}")
        print(f"Fixes failed: {fixes_failed}")

        if self.dry_run and modifications:
            print(f"\n⚠️  DRY RUN: {len(modifications)} fix(es) would have been applied")

        print(f"{'='*80}\n")

        return {
            "total_failures": total_failures,
            "fixes_applied": fixes_applied,
            "fixes_failed": fixes_failed,
            "modifications": modifications
        }


def main():
    parser = argparse.ArgumentParser(
        description="Automatically fix compilation errors in expected_fix code using an LLM"
    )
    parser.add_argument(
        "--file",
        type=Path,
        required=True,
        help="YAML file to process"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="gpt-4-turbo",
        help="Model to use for fixing (default: gpt-4-turbo)"
    )
    parser.add_argument(
        "--rule-id",
        type=str,
        help="Only fix test cases for this specific rule_id"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be fixed without modifying files"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed output including LLM responses"
    )

    args = parser.parse_args()

    if not args.file.exists():
        print(f"Error: File not found: {args.file}")
        return 1

    fixer = ExpectedFixFixer(
        model_name=args.model,
        dry_run=args.dry_run,
        verbose=args.verbose
    )

    result = fixer.fix_yaml_file(args.file, rule_id_filter=args.rule_id)

    # Return exit code based on results
    if result["fixes_failed"] > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
