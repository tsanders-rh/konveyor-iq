# Automated Test Case Generation

This guide explains how to automatically generate test case templates from Konveyor rulesets.

## Overview

The test case generator (`scripts/generate_tests.py`) parses Konveyor ruleset YAML files and creates test case templates that you can fill in with code examples. This dramatically reduces the manual effort of creating test suites.

## Quick Start

### Generate from a Single Ruleset

```bash
python scripts/generate_tests.py \
    --ruleset https://github.com/konveyor/rulesets/blob/main/default/generated/quarkus/200-ee-to-quarkus.windup.yaml
```

This creates a file in `benchmarks/test_cases/generated/200-ee-to-quarkus.windup.yaml` with one test case template per rule.

### Generate from All Quarkus Rulesets

```bash
python scripts/generate_tests.py --all-quarkus
```

This scans all Quarkus rulesets and generates test suites for each one.

### Preview Before Generating

```bash
python scripts/generate_tests.py \
    --ruleset https://github.com/konveyor/rulesets/blob/main/default/generated/quarkus/200-ee-to-quarkus.windup.yaml \
    --preview
```

Shows what will be generated without writing files.

## Command-Line Options

| Option | Description |
|--------|-------------|
| `--ruleset URL` | Generate from a specific Konveyor ruleset URL |
| `--all-quarkus` | Generate from all Quarkus rulesets |
| `--output DIR` | Output directory (default: `benchmarks/test_cases/generated`) |
| `--preview` | Preview output without writing files |
| `--no-when` | Exclude `when` condition hints from code snippets |

## What Gets Generated

For each rule in the ruleset, the generator creates:

```yaml
rules:
  - rule_id: "ee-to-quarkus-00000"
    description: "@Stateless annotation must be replaced"
    severity: "low"
    category: "potential"
    source: "https://github.com/konveyor/rulesets/blob/main/..."
    migration_pattern: "@Stateless -> @ApplicationScoped"  # Extracted from message

    test_cases:
      - id: "tc001"
        language: "java"
        context: "TODO: Add context for ee-to-quarkus-00000"
        code_snippet: |
          // TODO: Add code example
          // Hint: This rule detects references to javax.ejb.Stateless, @Stateless annotation
          // Example pattern: ...
        expected_fix: "TODO: Add expected fix code here"
        # konveyor_guidance: "Stateless EJBs can be converted to a CDI bean..."
```

## Features

### 1. Automatic Metadata Extraction

The generator extracts:
- **Rule ID** - From `ruleID` field
- **Description** - From `description` field
- **Konveyor Message** - Added as comment for guidance
- **Category** - From `category` field (potential, mandatory, etc.)
- **Severity** - Mapped from `effort` score:
  - effort 1 → low
  - effort 2-3 → medium
  - effort 4-5 → high
  - effort 6+ → critical

### 2. Migration Pattern Detection

Automatically extracts migration patterns from rule messages:

```yaml
# Message: "replacing `@Stateless` annotation with `@ApplicationScoped`"
# Becomes:
migration_pattern: "@Stateless -> @ApplicationScoped"
```

### 3. Code Hints from 'When' Conditions

The generator analyzes the `when` condition to provide hints:

```yaml
code_snippet: |
  // TODO: Add code example
  // Hint: This rule detects @Stateless annotation, references to javax.ejb.Stateless
  // Example pattern: ...
```

### 4. Konveyor Guidance Included

The official Konveyor rule message is included as a comment:

```yaml
# konveyor_guidance: "Stateless EJBs can be converted to a CDI bean by replacing
#   the `@Stateless` annotation with a scope eg `@ApplicationScoped`"
```

This guidance will automatically be used in LLM prompts when you run evaluations!

## Workflow

### Step 1: Generate Templates

```bash
python scripts/generate_tests.py --all-quarkus
```

Output:
```
Fetching list of Quarkus rulesets...
Found 25 Quarkus rulesets

[1/25] Processing 200-ee-to-quarkus.windup.yaml
Fetching ruleset: https://github.com/konveyor/rulesets/blob/main/...
Found 3 rules

✓ Generated test cases: benchmarks/test_cases/generated/200-ee-to-quarkus.windup.yaml
  Rules: 3
  Test cases: 3 (1 per rule)

[2/25] Processing 201-persistence-to-quarkus.windup.yaml
...

✓ Generated 25 test suite files in benchmarks/test_cases/generated
```

### Step 2: Fill in TODOs

Edit the generated files to add actual code examples:

```yaml
# Before:
code_snippet: "TODO: Add code snippet that violates this rule"
expected_fix: "TODO: Add expected fix code here"

# After:
code_snippet: |
  import javax.ejb.Stateless;

  @Stateless
  public class UserService {
      public User findUser(Long id) {
          return database.find(id);
      }
  }

expected_fix: |
  import jakarta.enterprise.context.ApplicationScoped;

  @ApplicationScoped
  public class UserService {
      public User findUser(Long id) {
          return database.find(id);
      }
  }
```

### Step 3: Run Evaluation

```bash
python evaluate.py --benchmark benchmarks/test_cases/generated/200-ee-to-quarkus.windup.yaml
```

## Tips

### Finding Konveyor Ruleset URLs

Browse the official Konveyor rulesets repository:
https://github.com/konveyor/rulesets/tree/main/default/generated/quarkus

Click on any `.yaml` file and copy the URL.

### Organizing Generated Files

Create subdirectories for different migration types:

```bash
# EJB migrations
python scripts/generate_tests.py \
    --ruleset .../200-ee-to-quarkus.windup.yaml \
    --output benchmarks/test_cases/ejb_migration

# Persistence migrations
python scripts/generate_tests.py \
    --ruleset .../201-persistence-to-quarkus.windup.yaml \
    --output benchmarks/test_cases/persistence_migration
```

### Batch Processing with Shell Scripts

Create a script to generate multiple specific rulesets:

```bash
#!/bin/bash
# generate_my_rulesets.sh

RULESETS=(
    "200-ee-to-quarkus.windup.yaml"
    "201-persistence-to-quarkus.windup.yaml"
    "202-remote-ejb-to-quarkus.windup.yaml"
)

for ruleset in "${RULESETS[@]}"; do
    python scripts/generate_tests.py \
        --ruleset "https://github.com/konveyor/rulesets/blob/main/default/generated/quarkus/$ruleset"
done
```

### Customizing Generated Tests

After generation, you can:
1. Add multiple test cases per rule (copy/modify the template)
2. Add `expected_metrics` for stricter validation
3. Customize severity levels
4. Add more descriptive contexts

Example:
```yaml
rules:
  - rule_id: "ee-to-quarkus-00000"
    description: "@Stateless EJB to @ApplicationScoped CDI"
    test_cases:
      # Simple case (generated)
      - id: "tc001"
        context: "Simple stateless bean"
        code_snippet: |
          @Stateless
          public class SimpleService { }

      # Add more complex cases manually
      - id: "tc002"
        context: "Stateless bean with dependency injection"
        code_snippet: |
          @Stateless
          public class ComplexService {
              @EJB
              private OtherService other;
          }
```

## Advanced Usage

### Custom Output Structure

Generate into a custom directory structure:

```bash
mkdir -p benchmarks/test_cases/quarkus/ejb
mkdir -p benchmarks/test_cases/quarkus/persistence
mkdir -p benchmarks/test_cases/quarkus/jaxrs

python scripts/generate_tests.py \
    --ruleset .../200-ee-to-quarkus.windup.yaml \
    --output benchmarks/test_cases/quarkus/ejb

python scripts/generate_tests.py \
    --ruleset .../201-persistence-to-quarkus.windup.yaml \
    --output benchmarks/test_cases/quarkus/persistence
```

### Excluding When Condition Hints

If you prefer minimal templates:

```bash
python scripts/generate_tests.py \
    --ruleset URL \
    --no-when
```

Generates cleaner placeholders:
```yaml
code_snippet: "TODO: Add code snippet that violates this rule"
```

## Troubleshooting

### "Invalid GitHub URL"

Make sure you're using the full GitHub URL, not a local path:

✅ Correct:
```
https://github.com/konveyor/rulesets/blob/main/default/generated/quarkus/200-ee-to-quarkus.windup.yaml
```

❌ Incorrect:
```
/path/to/local/file.yaml
```

### "Error fetching ruleset: 404"

The ruleset file may have been moved or renamed. Check the latest structure at:
https://github.com/konveyor/rulesets/tree/main/default/generated/quarkus

### "Ruleset is not a list of rules"

Some Konveyor rulesets have nested structures. The generator expects a flat list of rules. If you encounter this, please open an issue.

## Next Steps

After generating test cases:

1. **Fill in code examples** - Replace TODO placeholders with real code
2. **Add expected fixes** - Provide the corrected code
3. **Review Konveyor guidance** - The message is included as a comment
4. **Run evaluation** - Test your LLMs against the generated suite
5. **Iterate** - Add more test cases, edge cases, variations

## Example: Complete Workflow

```bash
# 1. Generate from all Quarkus rulesets
python scripts/generate_tests.py --all-quarkus --output benchmarks/test_cases/generated

# 2. Review the generated files
ls -la benchmarks/test_cases/generated/

# 3. Edit one file (example)
vim benchmarks/test_cases/generated/200-ee-to-quarkus.windup.yaml
# ... fill in code examples and expected fixes ...

# 4. Run evaluation on the completed file
python evaluate.py --benchmark benchmarks/test_cases/generated/200-ee-to-quarkus.windup.yaml

# 5. Review results
open results/evaluation_report_*.html
```

## Contributing

Found a bug or have a feature request for the generator? Please open an issue at:
https://github.com/tsanders-rh/konveyor-iq/issues

Ideas for improvements:
- Generate multiple test cases per rule based on `when` conditions
- Extract code examples from Konveyor documentation
- Support for other language rulesets (Python, JavaScript)
- Integration with Konveyor analyzer output
