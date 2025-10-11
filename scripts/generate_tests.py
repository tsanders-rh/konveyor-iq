#!/usr/bin/env python3
"""
Automated test case generator from Konveyor rulesets.

This script parses Konveyor YAML ruleset files and generates test case templates
that can be filled in with code examples. Supports label-based filtering to generate
migration-focused test suites.

Usage:
    # Generate from a single ruleset
    python scripts/generate_tests.py \
        --ruleset https://github.com/konveyor/rulesets/blob/main/default/generated/quarkus/200-ee-to-quarkus.windup.yaml

    # Generate from all Quarkus rulesets
    python scripts/generate_tests.py --all-quarkus

    # Generate from ALL Konveyor rulesets (all categories)
    python scripts/generate_tests.py --all-rulesets

    # Filter by migration path (Java EE → Quarkus)
    python scripts/generate_tests.py --all-rulesets --source java-ee --target quarkus
    # Output: java-ee-to-quarkus.yaml (39 aggregated rules)

    # Filter by target only (any source → Quarkus)
    python scripts/generate_tests.py --all-rulesets --target quarkus
    # Output: quarkus.yaml (aggregated rules from all sources)

    # Filter by source only (EAP7 → any target)
    python scripts/generate_tests.py --all-rulesets --source eap7
    # Output: eap7.yaml (aggregated rules for EAP7 migrations)

    # Preview without writing files
    python scripts/generate_tests.py --ruleset URL --preview

    # Auto-generate code examples using LLM
    python scripts/generate_tests.py --all-rulesets --source java-ee --target quarkus \
        --auto-generate --model gpt-4-turbo

Label-Based Filtering:
    Use --source and --target to filter rules by konveyor.io/source and
    konveyor.io/target labels. When filtering with --all-quarkus, all matching
    rules across all rulesets are aggregated into a single test suite file.

    Common migration paths:
        --source java-ee --target quarkus      # Java EE to Quarkus (39 rules)
        --source springboot --target quarkus   # Spring Boot to Quarkus (34 rules)
        --source jakarta-ee --target quarkus   # Jakarta EE to Quarkus
        --target quarkus                       # All migrations to Quarkus (73 rules)
"""
import argparse
import sys
import yaml
import requests
from pathlib import Path
from typing import List, Dict, Any, Optional
import re
import os

# Add parent directory to path to import models
sys.path.insert(0, str(Path(__file__).parent.parent))
from models import OpenAIModel, AnthropicModel


class TestCaseGenerator:
    """Generate test cases from Konveyor rulesets."""

    def __init__(self, output_dir: str = "benchmarks/test_cases/generated",
                 source_filter: Optional[str] = None,
                 target_filter: Optional[str] = None,
                 auto_generate: bool = False,
                 model_name: Optional[str] = None,
                 api_key: Optional[str] = None,
                 github_token: Optional[str] = None):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.source_filter = source_filter
        self.target_filter = target_filter
        self.auto_generate = auto_generate
        self.model = None

        # Setup GitHub token for higher API rate limits
        self.github_token = github_token or os.getenv("GITHUB_TOKEN")
        self.github_headers = {}
        if self.github_token:
            self.github_headers = {"Authorization": f"token {self.github_token}"}
            print("Using GitHub token for API requests (5,000 req/hour limit)")
        else:
            print("Warning: No GitHub token provided. Rate limited to 60 req/hour.")
            print("Set GITHUB_TOKEN env var or use --github-token for higher limits.")

        # Initialize model for auto-generation if requested
        if auto_generate:
            if not model_name:
                print("Warning: --auto-generate requires --model. Using gpt-4-turbo by default.")
                model_name = "gpt-4-turbo"

            self.model = self._initialize_model(model_name, api_key)
            if self.model:
                print(f"Auto-generation enabled with model: {model_name}")
            else:
                print("Warning: Failed to initialize model. Auto-generation disabled.")
                self.auto_generate = False

    def _initialize_model(self, model_name: str, api_key: Optional[str]):
        """Initialize LLM model for code generation."""
        try:
            # Determine provider from model name
            if "gpt" in model_name.lower() or "o1" in model_name.lower():
                provider = "openai"
            elif "claude" in model_name.lower():
                provider = "anthropic"
            else:
                print(f"Warning: Unknown model provider for '{model_name}'. Assuming OpenAI.")
                provider = "openai"

            # Get API key from argument or environment
            if not api_key:
                if provider == "openai":
                    api_key = os.getenv("OPENAI_API_KEY")
                elif provider == "anthropic":
                    api_key = os.getenv("ANTHROPIC_API_KEY")

            if not api_key:
                print(f"Error: No API key found for {provider}. Set OPENAI_API_KEY or ANTHROPIC_API_KEY environment variable.")
                return None

            # Initialize model
            config = {
                "api_key": api_key,
                "temperature": 0.3,  # Low temperature for more deterministic code generation
                "max_tokens": 2000
            }

            if provider == "openai":
                return OpenAIModel(model_name, config)
            elif provider == "anthropic":
                return AnthropicModel(model_name, config)

        except Exception as e:
            print(f"Error initializing model: {e}")
            return None

    def _generate_code_snippet(self, rule: Dict[str, Any], konveyor_message: str) -> str:
        """Generate violating code snippet using LLM."""
        if not self.auto_generate or not self.model:
            return self._create_code_snippet_placeholder(rule, include_when=True)

        rule_id = rule.get('ruleID', 'unknown')
        description = rule.get('description', 'No description')

        prompt = f"""Generate a Java code example that violates the following migration rule.

Rule ID: {rule_id}
Description: {description}
Konveyor Guidance: {konveyor_message}

Requirements:
- Generate ONLY the violating code (before migration)
- Include necessary imports
- Make it a complete, realistic code example
- Keep it concise (10-30 lines)
- Include the specific patterns mentioned in the rule

Respond with ONLY the Java code, no explanations."""

        try:
            print(f"    Generating code snippet for {rule_id}...", end=" ")
            result = self.model.generate(prompt)

            # Extract response text from dict
            if isinstance(result, dict):
                response_text = result.get("response", "")
            else:
                response_text = str(result)

            code = self._extract_code_from_response(response_text)
            print("✓")
            return code
        except Exception as e:
            print(f"✗ (Error: {e})")
            return self._create_code_snippet_placeholder(rule, include_when=True)

    def _generate_expected_fix(self, rule: Dict[str, Any], code_snippet: str, konveyor_message: str) -> str:
        """Generate expected fix using LLM."""
        if not self.auto_generate or not self.model:
            return "TODO: Add expected fix code here"

        if code_snippet.startswith("TODO"):
            return "TODO: Add expected fix code here"

        rule_id = rule.get('ruleID', 'unknown')
        description = rule.get('description', 'No description')

        prompt = f"""Fix the following Java code to resolve the migration violation.

Rule ID: {rule_id}
Description: {description}
Konveyor Guidance: {konveyor_message}

Original Code (violating):
```java
{code_snippet}
```

Requirements:
- Provide the COMPLETE fixed code
- Include all necessary imports
- Follow the migration guidance exactly
- Keep the same structure and logic, only fix the violation

Respond with ONLY the fixed Java code, no explanations."""

        try:
            print(f"    Generating expected fix for {rule_id}...", end=" ")
            result = self.model.generate(prompt)

            # Extract response text from dict
            if isinstance(result, dict):
                response_text = result.get("response", "")
            else:
                response_text = str(result)

            code = self._extract_code_from_response(response_text)
            print("✓")
            return code
        except Exception as e:
            print(f"✗ (Error: {e})")
            return "TODO: Add expected fix code here"

    def _extract_code_from_response(self, response: str) -> str:
        """Extract code block from LLM response."""
        # Try to find code between ```java and ```
        java_pattern = r'```java\s*(.*?)\s*```'
        match = re.search(java_pattern, response, re.DOTALL)
        if match:
            return match.group(1).strip()

        # Try to find code between ``` and ```
        code_pattern = r'```\s*(.*?)\s*```'
        match = re.search(code_pattern, response, re.DOTALL)
        if match:
            return match.group(1).strip()

        # No code blocks found, return as-is (might be plain code)
        return response.strip()

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
            response = requests.get(raw_url, headers=self.github_headers, timeout=10)
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

        # Check if any rules matched filters
        num_filtered_rules = len(test_suite['rules'])
        if (self.source_filter or self.target_filter) and num_filtered_rules == 0:
            filter_desc = []
            if self.source_filter:
                filter_desc.append(f"source={self.source_filter}")
            if self.target_filter:
                filter_desc.append(f"target={self.target_filter}")
            print(f"  No rules matched filters: {', '.join(filter_desc)}")
            return None

        # Convert to YAML
        yaml_content = yaml.dump(test_suite, sort_keys=False, default_flow_style=False, width=120)

        if preview:
            print("\n" + "=" * 80)
            print("Preview of generated test cases:")
            print("=" * 80)
            print(yaml_content)
            return None
        else:
            # Determine output filename
            if self.source_filter or self.target_filter:
                output_filename = f"{self._get_migration_path_name()}.yaml"
            else:
                output_filename = f"{ruleset_name}.yaml"

            # Write to file
            output_file = self.output_dir / output_filename
            output_file.write_text(yaml_content)
            print(f"\n✓ Generated test cases: {output_file}")
            if self.source_filter or self.target_filter:
                print(f"  Matched rules: {num_filtered_rules}/{len(ruleset_data)}")
            else:
                print(f"  Rules: {len(ruleset_data)}")
            print(f"  Test cases: {num_filtered_rules} (1 per rule)")
            return str(output_file)

    def generate_all_rulesets(self, preview: bool = False) -> List[str]:
        """
        Generate test cases from ALL Konveyor rulesets (all subdirectories).

        When source/target filters are specified, aggregates all matching rules
        across all rulesets into a single test suite file.

        Args:
            preview: If True, only preview first ruleset

        Returns:
            List of generated file paths
        """
        print("Fetching all Konveyor rulesets from default/generated...")

        # Get all YAML files from all subdirectories
        yaml_files = self._fetch_all_rulesets_recursive()

        if not yaml_files:
            print("No rulesets found")
            return []

        print(f"Found {len(yaml_files)} rulesets across all categories\n")

        # If filtering by source/target, aggregate all matching rules
        if self.source_filter or self.target_filter:
            return self._generate_aggregated_by_filters(yaml_files, preview, base_path="default/generated")

        # Otherwise, generate one file per ruleset
        generated_files = []

        for i, file_info in enumerate(yaml_files, 1):
            file_url = file_info['url']

            print(f"[{i}/{len(yaml_files)}] Processing {file_info['name']} ({file_info['category']})")

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

    def generate_all_quarkus_rulesets(self, preview: bool = False) -> List[str]:
        """
        Generate test cases from all Quarkus rulesets.

        When source/target filters are specified, aggregates all matching rules
        across all rulesets into a single test suite file.

        Args:
            preview: If True, only preview first ruleset

        Returns:
            List of generated file paths
        """
        print("Fetching list of Quarkus rulesets...")

        # Get list of ruleset files from GitHub
        api_url = "https://api.github.com/repos/konveyor/rulesets/contents/default/generated/quarkus"

        try:
            response = requests.get(api_url, headers=self.github_headers, timeout=10)
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

        # If filtering by source/target, aggregate all matching rules
        if self.source_filter or self.target_filter:
            return self._generate_aggregated_by_filters(yaml_files, preview)

        # Otherwise, generate one file per ruleset
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

    def _fetch_all_rulesets_recursive(self) -> List[Dict[str, Any]]:
        """
        Recursively fetch all YAML rulesets from all subdirectories in default/generated.

        Returns:
            List of dicts with 'name', 'url', and 'category' keys
        """
        base_url = "https://api.github.com/repos/konveyor/rulesets/contents/default/generated"
        all_yaml_files = []

        try:
            response = requests.get(base_url, headers=self.github_headers, timeout=10)
            response.raise_for_status()
            subdirs = response.json()
        except Exception as e:
            print(f"Error fetching subdirectories: {e}")
            return []

        # Iterate through each subdirectory
        for subdir in subdirs:
            if not isinstance(subdir, dict) or subdir.get('type') != 'dir':
                continue

            category = subdir['name']
            subdir_url = subdir['url']

            try:
                response = requests.get(subdir_url, headers=self.github_headers, timeout=10)
                response.raise_for_status()
                files = response.json()
            except Exception as e:
                print(f"Warning: Could not fetch {category}: {e}")
                continue

            # Filter for YAML files
            for file_info in files:
                if isinstance(file_info, dict) and file_info.get('name', '').endswith('.yaml'):
                    all_yaml_files.append({
                        'name': file_info['name'],
                        'url': f"https://github.com/konveyor/rulesets/blob/main/default/generated/{category}/{file_info['name']}",
                        'category': category
                    })

        return all_yaml_files

    def _generate_aggregated_by_filters(
        self,
        yaml_files: List[Dict[str, Any]],
        preview: bool,
        base_path: str = "default/generated/quarkus"
    ) -> List[str]:
        """
        Generate a single aggregated test suite from all matching rules across all rulesets.
        """
        all_matching_rules = []
        total_rules_scanned = 0

        for i, file_info in enumerate(yaml_files, 1):
            # Handle both old format (just dict from API) and new format (with url/category)
            if 'url' in file_info:
                file_url = file_info['url']
                file_name = file_info['name']
                category = file_info.get('category', '')
                display_name = f"{file_name} ({category})" if category else file_name
            else:
                file_url = f"https://github.com/konveyor/rulesets/blob/main/{base_path}/{file_info['name']}"
                display_name = file_info['name']

            print(f"[{i}/{len(yaml_files)}] Scanning {display_name}")

            # Fetch ruleset
            raw_url = self._convert_to_raw_url(file_url)
            if not raw_url:
                continue

            try:
                response = requests.get(raw_url, headers=self.github_headers, timeout=10)
                response.raise_for_status()
                ruleset_data = yaml.safe_load(response.text)
            except Exception as e:
                print(f"  Error fetching: {e}")
                continue

            if not isinstance(ruleset_data, list):
                continue

            total_rules_scanned += len(ruleset_data)

            # Filter rules
            for rule in ruleset_data:
                if isinstance(rule, dict) and self._matches_filters(rule):
                    # Add source URL to rule for reference
                    rule['_source_ruleset'] = file_url
                    all_matching_rules.append(rule)

            if all_matching_rules:
                print(f"  Found {len([r for r in all_matching_rules if r.get('_source_ruleset') == file_url])} matching rules")

        print(f"\nScanned {total_rules_scanned} total rules across {len(yaml_files)} rulesets")
        print(f"Found {len(all_matching_rules)} matching rules")

        if not all_matching_rules:
            print("\n⚠ No rules matched the specified filters")
            return []

        # Create aggregated test suite
        migration_path = self._get_migration_path_name()
        suite_name = f"{migration_path.title()} Migration"

        test_suite = {
            'name': suite_name,
            'description': f'Test cases for {migration_path} migration (aggregated from all Quarkus rulesets)',
            'version': '1.0.0',
            'metadata': {
                'source': 'Konveyor AI Migration Rules',
                'language': 'java',
                'generated_from': 'https://github.com/konveyor/rulesets/tree/main/default/generated/quarkus',
                'category': 'migration',
                'total_rulesets_scanned': len(yaml_files),
                'total_rules_scanned': total_rules_scanned
            },
            'rules': []
        }

        if self.source_filter:
            test_suite['metadata']['migration_source'] = self.source_filter
        if self.target_filter:
            test_suite['metadata']['migration_target'] = self.target_filter

        # Add migration-specific prompt
        prompt = self._generate_prompt_for_migration(self.source_filter, self.target_filter)
        if prompt:
            test_suite['prompt'] = prompt

        # Convert rules to test case format
        for rule in all_matching_rules:
            source_url = rule.pop('_source_ruleset', 'unknown')
            rule_entry = self._create_rule_entry(rule, source_url, include_when=True)
            if rule_entry:
                test_suite['rules'].append(rule_entry)

        # Convert to YAML
        yaml_content = yaml.dump(test_suite, sort_keys=False, default_flow_style=False, width=120)

        if preview:
            print("\n" + "=" * 80)
            print("Preview of aggregated test suite:")
            print("=" * 80)
            print(yaml_content[:2000])  # Show first 2000 chars
            print(f"\n... ({len(yaml_content)} total characters)")
            return []

        # Write to file
        output_filename = f"{migration_path}.yaml"
        output_file = self.output_dir / output_filename
        output_file.write_text(yaml_content)

        print(f"\n✓ Generated aggregated test suite: {output_file}")
        print(f"  Test cases: {len(test_suite['rules'])}")

        return [str(output_file)]

    def _create_test_suite(
        self,
        rules: List[Dict[str, Any]],
        ruleset_name: str,
        source_url: str,
        include_when: bool
    ) -> Dict[str, Any]:
        """Create test suite structure from rules."""

        # Filter rules by source/target labels if specified
        filtered_rules = []
        for rule in rules:
            if not isinstance(rule, dict):
                continue
            if self._matches_filters(rule):
                filtered_rules.append(rule)

        # Determine suite name and description based on filters
        if self.source_filter or self.target_filter:
            migration_path = self._get_migration_path_name()
            suite_name = f"{migration_path.title()} Migration"
            description = f'Test cases for {migration_path} migration'
        else:
            suite_name = self._format_suite_name(ruleset_name)
            description = f'Test cases generated from {ruleset_name}'

        # Extract category from first rule or use generic
        category = "migration"
        if filtered_rules and isinstance(filtered_rules[0], dict):
            category = filtered_rules[0].get('category', 'migration')

        test_suite = {
            'name': suite_name,
            'description': description,
            'version': '1.0.0',
            'metadata': {
                'source': 'Konveyor AI Migration Rules',
                'language': 'java',
                'generated_from': source_url,
                'category': category
            },
            'rules': []
        }

        # Add migration path to metadata if filtering
        if self.source_filter:
            test_suite['metadata']['migration_source'] = self.source_filter
        if self.target_filter:
            test_suite['metadata']['migration_target'] = self.target_filter

        for rule in filtered_rules:
            rule_entry = self._create_rule_entry(rule, source_url, include_when)
            if rule_entry:
                test_suite['rules'].append(rule_entry)

        return test_suite

    def _matches_filters(self, rule: Dict[str, Any]) -> bool:
        """Check if rule matches source/target filters based on labels."""
        if not self.source_filter and not self.target_filter:
            return True  # No filters, include all rules

        labels = rule.get('labels', [])
        if not labels:
            return False  # No labels, can't match filters

        # Extract source and target from labels
        rule_sources = []
        rule_targets = []

        for label in labels:
            if isinstance(label, str):
                if label.startswith('konveyor.io/source='):
                    rule_sources.append(label.split('=', 1)[1])
                elif label.startswith('konveyor.io/target='):
                    rule_targets.append(label.split('=', 1)[1])

        # Check filters
        source_match = True
        target_match = True

        if self.source_filter:
            source_match = self.source_filter in rule_sources

        if self.target_filter:
            target_match = self.target_filter in rule_targets

        return source_match and target_match

    def _get_migration_path_name(self) -> str:
        """Get migration path name for file naming."""
        parts = []
        if self.source_filter:
            parts.append(self.source_filter)
        if self.target_filter:
            parts.append(self.target_filter)
        return '-to-'.join(parts) if len(parts) == 2 else parts[0] if parts else 'filtered'

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

        # Generate or create placeholder for code snippet
        if self.auto_generate:
            code_snippet = self._generate_code_snippet(rule, message)
            expected_fix = self._generate_expected_fix(rule, code_snippet, message)
        else:
            code_snippet = self._create_code_snippet_placeholder(rule, include_when)
            expected_fix = 'TODO: Add expected fix code here'

        # Create test case template
        test_case = {
            'id': 'tc001',
            'language': 'java',
            'context': f'TODO: Add context for {rule_id}',
            'code_snippet': code_snippet,
            'expected_fix': expected_fix,
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

    def _generate_prompt_for_migration(self, source: Optional[str], target: Optional[str]) -> Optional[str]:
        """Generate migration-specific prompt template based on source/target."""

        # Prompt templates for different migration scenarios
        prompts = {
            # Quarkus migrations
            ('java-ee', 'quarkus'): """You are helping migrate Java EE code to Quarkus based on static analysis rules.

MIGRATION TARGET: Quarkus with Jakarta EE APIs
- Use Jakarta EE packages (jakarta.*) NOT Java EE (javax.*)
- Use CDI annotations: @ApplicationScoped, @Inject, @SessionScoped
- Use Jakarta Persistence and Jakarta Transactions
- DO NOT use Spring Framework (@Service, @Component, @Autowired, etc.)

Rule Violation:
{rule_description}

Konveyor Migration Guidance:
{konveyor_message}

Original Code:
```{language}
{code_snippet}
```

Context: {context}

Please provide:
1. The COMPLETE corrected code that resolves the violation (include ALL original code)
2. A brief explanation of the changes made

IMPORTANT:
- Provide the ENTIRE class with ALL fields and methods, not just the parts you changed
- Use Jakarta EE (jakarta.*) packages, not Spring Framework
- Follow Quarkus best practices

Format your response as:
FIXED CODE:
```{language}
[your complete fixed code here]
```

EXPLANATION:
[your explanation here]""",

            # EAP migrations
            ('eap7', 'eap8'): """You are helping migrate JBoss EAP 7 code to JBoss EAP 8 based on static analysis rules.

MIGRATION TARGET: JBoss EAP 8 with Jakarta EE 10
- Use Jakarta EE 10 packages (jakarta.*) instead of Java EE (javax.*)
- Follow EAP 8 configuration best practices
- Update deprecated APIs to their EAP 8 equivalents

Rule Violation:
{rule_description}

Konveyor Migration Guidance:
{konveyor_message}

Original Code:
```{language}
{code_snippet}
```

Context: {context}

Please provide:
1. The COMPLETE corrected code that resolves the violation
2. A brief explanation of the changes made

Format your response as:
FIXED CODE:
```{language}
[your complete fixed code here]
```

EXPLANATION:
[your explanation here]""",

            # Spring Boot migrations
            ('springboot', 'quarkus'): """You are helping migrate Spring Boot code to Quarkus based on static analysis rules.

MIGRATION TARGET: Quarkus
- Replace Spring annotations with Quarkus/Jakarta EE equivalents:
  - @Service, @Component → @ApplicationScoped
  - @Autowired → @Inject
  - @Repository → @ApplicationScoped with CDI
  - @RestController → @Path (JAX-RS)
- Use JAX-RS instead of Spring MVC
- Use CDI instead of Spring DI

Rule Violation:
{rule_description}

Konveyor Migration Guidance:
{konveyor_message}

Original Code:
```{language}
{code_snippet}
```

Context: {context}

Please provide:
1. The COMPLETE corrected code that resolves the violation
2. A brief explanation of the changes made

IMPORTANT:
- DO NOT use any Spring Framework annotations
- Use Quarkus and Jakarta EE APIs only

Format your response as:
FIXED CODE:
```{language}
[your complete fixed code here]
```

EXPLANATION:
[your explanation here]""",
        }

        # Generic template when no specific match
        generic_template = """You are helping with code migration based on static analysis rules.

Rule Violation:
{rule_description}

Konveyor Migration Guidance:
{konveyor_message}

Original Code:
```{language}
{code_snippet}
```

Context: {context}

Please provide:
1. The COMPLETE corrected code that resolves the violation
2. A brief explanation of the changes made

Format your response as:
FIXED CODE:
```{language}
[your complete fixed code here]
```

EXPLANATION:
[your explanation here]"""

        # Try to find exact match
        if source and target and (source, target) in prompts:
            return prompts[(source, target)]

        # Try target-only templates
        for (s, t), prompt in prompts.items():
            if target and t == target and not source:
                return prompt

        # Return generic template
        return generic_template

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

  # Generate from ALL Konveyor rulesets (all categories: quarkus, eap, spring-boot, etc.)
  python scripts/generate_tests.py --all-rulesets

  # Filter by migration path (source -> target)
  python scripts/generate_tests.py --all-rulesets --source eap7 --target quarkus

  # Filter by target only (any source -> Quarkus)
  python scripts/generate_tests.py --all-rulesets --target quarkus

  # Filter by source only (EAP7 -> any target)
  python scripts/generate_tests.py --all-rulesets --source eap7

  # Preview without writing files
  python scripts/generate_tests.py --ruleset URL --preview

  # Auto-generate code examples using LLM
  python scripts/generate_tests.py --all-rulesets --source java-ee --target quarkus \\
      --auto-generate --model gpt-4-turbo

  # Specify output directory
  python scripts/generate_tests.py --all-rulesets --output benchmarks/test_cases/auto_generated/
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
        '--all-rulesets',
        action='store_true',
        help='Generate from ALL Konveyor rulesets (all categories: quarkus, spring-boot, eap, etc.)'
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

    parser.add_argument(
        '--source',
        type=str,
        help='Filter rules by migration source (e.g., eap7, springboot, java-ee)'
    )

    parser.add_argument(
        '--target',
        type=str,
        help='Filter rules by migration target (e.g., quarkus, jakarta-ee)'
    )

    parser.add_argument(
        '--auto-generate',
        action='store_true',
        help='Automatically generate code_snippet and expected_fix using LLM (requires --model)'
    )

    parser.add_argument(
        '--model',
        type=str,
        help='LLM model to use for auto-generation (e.g., gpt-4-turbo, claude-3-5-sonnet)'
    )

    parser.add_argument(
        '--api-key',
        type=str,
        help='API key for LLM (optional, can use OPENAI_API_KEY or ANTHROPIC_API_KEY env vars)'
    )

    parser.add_argument(
        '--github-token',
        type=str,
        help='GitHub personal access token for higher API rate limits (optional, can use GITHUB_TOKEN env var)'
    )

    args = parser.parse_args()

    # Validate arguments
    options_count = sum([bool(args.ruleset), args.all_quarkus, args.all_rulesets])
    if options_count == 0:
        parser.error("Must specify one of: --ruleset, --all-quarkus, or --all-rulesets")
    if options_count > 1:
        parser.error("Cannot specify multiple generation modes (choose only one)")

    # Create generator
    generator = TestCaseGenerator(
        output_dir=args.output,
        source_filter=args.source,
        target_filter=args.target,
        auto_generate=args.auto_generate,
        model_name=args.model,
        api_key=args.api_key,
        github_token=args.github_token
    )

    # Generate test cases
    if args.all_rulesets:
        # Show filter info if applicable
        if args.source or args.target:
            filter_parts = []
            if args.source:
                filter_parts.append(f"source={args.source}")
            if args.target:
                filter_parts.append(f"target={args.target}")
            print(f"\nApplying filters: {', '.join(filter_parts)}")

        generated = generator.generate_all_rulesets(preview=args.preview)
        if not args.preview:
            if generated:
                print(f"\n✓ Successfully generated {len(generated)} test suite files!")
                if args.source or args.target:
                    print(f"  Filtered by: {', '.join(filter_parts)}")
                print(f"\nNext steps:")
                print(f"1. Review generated files in {args.output}/")
                print(f"2. Fill in TODO placeholders with actual code examples")
                print(f"3. Add expected_fix code for each test case")
                print(f"4. Run evaluation: python evaluate.py --benchmark {args.output}/")
            else:
                print(f"\n⚠ No test suites generated - no rules matched the filters")
    elif args.all_quarkus:
        # Show filter info if applicable
        if args.source or args.target:
            filter_parts = []
            if args.source:
                filter_parts.append(f"source={args.source}")
            if args.target:
                filter_parts.append(f"target={args.target}")
            print(f"\nApplying filters: {', '.join(filter_parts)}")

        generated = generator.generate_all_quarkus_rulesets(preview=args.preview)
        if not args.preview:
            if generated:
                print(f"\n✓ Successfully generated {len(generated)} test suite files!")
                if args.source or args.target:
                    print(f"  Filtered by: {', '.join(filter_parts)}")
                print(f"\nNext steps:")
                print(f"1. Review generated files in {args.output}/")
                print(f"2. Fill in TODO placeholders with actual code examples")
                print(f"3. Add expected_fix code for each test case")
                print(f"4. Run evaluation: python evaluate.py --benchmark {args.output}/")
            else:
                print(f"\n⚠ No test suites generated - no rules matched the filters")
    else:
        # Show filter info if applicable
        if args.source or args.target:
            filter_parts = []
            if args.source:
                filter_parts.append(f"source={args.source}")
            if args.target:
                filter_parts.append(f"target={args.target}")
            print(f"\nApplying filters: {', '.join(filter_parts)}")

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
        elif not args.preview and (args.source or args.target):
            print(f"\n⚠ No test suite generated - no rules matched the filters")


if __name__ == '__main__':
    main()
