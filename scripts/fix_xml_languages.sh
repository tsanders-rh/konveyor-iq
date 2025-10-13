#!/bin/bash
# Fix language metadata for XML test cases

FILE="benchmarks/test_cases/generated/quarkus.yaml"

echo "Fixing XML language metadata in $FILE..."

# Create backup if not exists
if [ ! -f "$FILE.backup" ]; then
    cp "$FILE" "$FILE.backup"
    echo "Created backup: $FILE.backup"
fi

# For each XML rule, change language: java to language: xml in the next few lines
# We'll use a Python one-liner to do this safely

python3 - <<'PYTHON'
rule_ids = [
    "springboot-parent-pom-to-quarkus-00000",
    "javaee-pom-to-quarkus-00000",
    "javaee-pom-to-quarkus-00010",
    "javaee-pom-to-quarkus-00030",
    "javaee-pom-to-quarkus-00050",
]

file_path = "benchmarks/test_cases/generated/quarkus.yaml"

with open(file_path, 'r') as f:
    lines = f.readlines()

updated_count = 0
in_xml_rule = False
current_rule = None

for i, line in enumerate(lines):
    # Check if we're starting a new rule
    if line.strip().startswith("- rule_id:"):
        rule_id = line.split("rule_id:")[1].strip()
        in_xml_rule = rule_id in rule_ids
        current_rule = rule_id

    # If we're in an XML rule and find "language: java", change it
    if in_xml_rule and "language: java" in line:
        lines[i] = line.replace("language: java", "language: xml")
        updated_count += 1
        print(f"  ✓ Updated {current_rule}: java → xml")

# Write back
with open(file_path, 'w') as f:
    f.writelines(lines)

print(f"\nUpdated {updated_count} test case(s)")
PYTHON

echo "Done!"
