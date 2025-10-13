# Setup Guide

## Installation

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

This installs all required dependencies including:
- `pyyaml` - YAML file processing
- `pydantic` - Schema validation and type checking
- `openai`, `anthropic`, `google-generativeai` - LLM providers
- `pylint`, `radon`, `bandit` - Code analysis tools
- `plotly`, `pandas` - Reporting and data visualization

### 2. Set API Keys

Set environment variables for the LLM providers you plan to use:

```bash
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
export GOOGLE_API_KEY="..."
```

Or create a `.env` file:

```bash
cat > .env << EOF
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=...
EOF
```

### 3. Verify Installation

```bash
# Check Python version (3.10+ recommended)
python3 --version

# Verify dependencies
pip list | grep -E "(pyyaml|pydantic|openai|anthropic)"

# Test schema import
python3 -c "from benchmarks.schema import TestSuite, MigrationComplexity; print('✓ Schema imports work')"
```

## Quick Start

### Generate Test Cases

```bash
# Generate tests from Konveyor rulesets
python3 scripts/generate_tests.py \
    --ruleset-path ~/Workspace/rulesets/default/generated/quarkus \
    --output benchmarks/test_cases/generated/my_tests.yaml \
    --target quarkus
```

### Classify Migration Complexity

```bash
# Classify rules by migration difficulty
python3 scripts/classify_rule_complexity.py \
    benchmarks/test_cases/generated/my_tests.yaml
```

### Fix Compilation Errors

```bash
# Fix trivial cases (namespace changes)
python3 scripts/fix_expected_fixes.py \
    --file benchmarks/test_cases/generated/my_tests.yaml \
    --complexity trivial,low
```

### Validate Test Cases

```bash
# Validate expected_fix code compiles
python3 scripts/validate_expected_fixes.py \
    benchmarks/test_cases/generated/my_tests.yaml
```

### Run Evaluation

```bash
# Evaluate AI models
python3 evaluate.py \
    --test-file benchmarks/test_cases/generated/my_tests.yaml \
    --models gpt-4-turbo claude-3-7-sonnet-latest
```

## Directory Structure

```
konveyor-iq/
├── benchmarks/
│   ├── schema.py              # Pydantic schemas (TestSuite, Rule, MigrationComplexity)
│   └── test_cases/
│       └── generated/         # Auto-generated test cases
├── config/
│   └── migration_guidance.yaml # Migration-specific prompts
├── scripts/
│   ├── generate_tests.py      # Generate test cases from rulesets
│   ├── classify_rule_complexity.py  # Classify migration difficulty
│   ├── fix_expected_fixes.py  # Auto-fix compilation errors
│   └── validate_expected_fixes.py   # Validate test cases compile
├── docs/
│   ├── SETUP.md              # This file
│   └── COMPLEXITY_CLASSIFICATION.md  # Complexity system docs
├── evaluate.py               # Main evaluation script
├── config.yaml              # Evaluation configuration
└── requirements.txt         # Python dependencies
```

## Common Issues

### ModuleNotFoundError: No module named 'yaml'

```bash
pip install pyyaml
```

### ModuleNotFoundError: No module named 'pydantic'

```bash
pip install pydantic>=2.0
```

### ImportError: cannot import name 'MigrationComplexity'

Make sure you're using the latest schema:

```bash
python3 -c "from benchmarks.schema import MigrationComplexity; print(MigrationComplexity.TRIVIAL)"
```

### Java compilation errors

Make sure Java 11+ is installed:

```bash
java -version
javac -version
```

## Development Workflow

### 1. Generate Tests
```bash
python3 scripts/generate_tests.py --ruleset-path ~/rulesets/...
```

### 2. Classify Complexity
```bash
python3 scripts/classify_rule_complexity.py benchmarks/test_cases/generated/quarkus.yaml
```

### 3. Fix Simple Cases
```bash
python3 scripts/fix_expected_fixes.py --file benchmarks/test_cases/generated/quarkus.yaml --complexity trivial,low
```

### 4. Validate
```bash
python3 scripts/validate_expected_fixes.py benchmarks/test_cases/generated/quarkus.yaml
```

### 5. Evaluate
```bash
python3 evaluate.py --test-file benchmarks/test_cases/generated/quarkus.yaml
```

### 6. Review Results
```bash
open results/evaluation_report_*.html
```

## Configuration

### config.yaml
Main evaluation configuration:
- Model selection and parameters
- Evaluation dimensions (compilation, security, quality)
- Prompt templates (fallback)
- Reporting options

### config/migration_guidance.yaml
Migration-specific guidance:
- Java EE → Quarkus
- Spring Boot → Quarkus
- EAP 7 → EAP 8

This guidance is injected into prompts to help LLMs generate better migrations.

## Next Steps

See [COMPLEXITY_CLASSIFICATION.md](COMPLEXITY_CLASSIFICATION.md) for detailed workflow on handling different migration complexity levels.
