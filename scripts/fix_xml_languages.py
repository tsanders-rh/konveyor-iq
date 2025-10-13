#!/usr/bin/env python3
"""
Fix language metadata for XML test cases that were incorrectly marked as Java.
"""
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import yaml

# Rule IDs with XML content that need language: xml
XML_RULE_IDS = [
    "springboot-parent-pom-to-quarkus-00000",
    "javaee-pom-to-quarkus-00000",
    "javaee-pom-to-quarkus-00010",
    "javaee-pom-to-quarkus-00030",
    "javaee-pom-to-quarkus-00050",
]

def fix_xml_languages(file_path: Path):
    """Update language field for XML test cases."""
    print(f"Processing: {file_path}")

    # Load YAML
    with open(file_path, 'r') as f:
        data = yaml.safe_load(f)

    updated_count = 0

    # Iterate through rules
    for rule in data.get('rules', []):
        if rule['rule_id'] in XML_RULE_IDS:
            for test_case in rule.get('test_cases', []):
                if test_case.get('language') == 'java':
                    test_case['language'] = 'xml'
                    updated_count += 1
                    print(f"  ✓ Updated {rule['rule_id']} - {test_case['id']}: java → xml")

    # Write updated YAML
    with open(file_path, 'w') as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

    print(f"\nUpdated {updated_count} test case(s)")
    print(f"Saved to: {file_path}")

if __name__ == "__main__":
    file_path = Path(__file__).parent.parent / "benchmarks" / "test_cases" / "generated" / "quarkus.yaml"
    fix_xml_languages(file_path)
