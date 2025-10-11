# Usage Guide

## Setup

### 1. Create Virtual Environment (Recommended)

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure API Keys

```bash
cp config.example.yaml config.yaml
```

Edit `config.yaml` and add your API keys:

```yaml
models:
  - name: "gpt-4-turbo"
    provider: "openai"
    api_key: "sk-..."  # Or use ${OPENAI_API_KEY}
```

Or export as environment variables:

```bash
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
```

## Running Evaluations

### Basic Usage

```bash
python evaluate.py --benchmark benchmarks/test_cases/java-ee-quarkus-migration.yaml
```

### Custom Configuration

```bash
python evaluate.py \
  --config my-config.yaml \
  --benchmark benchmarks/test_cases/java-ee-quarkus-migration.yaml \
  --output my-results/
```

### Generate Only HTML Report

```bash
python evaluate.py \
  --benchmark benchmarks/test_cases/java-ee-quarkus-migration.yaml \
  --format html
```

### Parallel Execution

Speed up evaluations by running multiple tests in parallel:

```bash
# Use 4 parallel workers (good for evaluating multiple models)
python evaluate.py \
  --benchmark benchmarks/test_cases/java-ee-quarkus-migration.yaml \
  --parallel 4

# Use 8 parallel workers for large test suites
python evaluate.py \
  --benchmark benchmarks/test_cases/java-ee-quarkus-migration.yaml \
  --parallel 8
```

**Benefits:**
- Significantly faster when testing multiple models (3-4x speedup typical)
- Each model evaluation runs independently via API calls
- Thread-safe result collection

**Recommendations:**
- Use `--parallel N` where N = number of models you're testing
- Higher values may hit API rate limits
- Default is 1 (sequential execution)

### Viewing Results

After running evaluation, the script outputs clickable `file://` URLs:

```
HTML report: results/evaluation_report_20241010_142530.html
  → file:///Users/tsanders/Workspace/konveyor-iq/results/evaluation_report_20241010_142530.html
```

**Click the URL** (Cmd+Click on Mac, Ctrl+Click on Windows/Linux) to open the report directly in your browser.

This works in:
- ✅ VS Code integrated terminal
- ✅ iTerm2
- ✅ Most modern terminal emulators

Alternatively, use shell commands:
```bash
# Open HTML report in default browser
open results/evaluation_report_*.html

# View markdown report
cat results/evaluation_report_*.md

# View JSON results
cat results/results_*.json | jq
```

## Creating Test Cases

### Test Suite Structure

Create a YAML file in `benchmarks/test_cases/`:

```yaml
name: "My Test Suite"
description: "Description of test suite"
version: "1.0.0"

rules:
  - rule_id: "my-rule-001"
    description: "What this rule checks"
    severity: "high"
    category: "migration"

    test_cases:
      - id: "tc001"
        language: "java"
        context: "Description of this test case"
        code_snippet: |
          // Original code with violation
          public class Example {
              // code here
          }

        expected_fix: |
          // Expected corrected code
          public class Example {
              // fixed code here
          }
```

### Test Case Fields

- **id**: Unique identifier for the test case
- **language**: Programming language (java, python, etc.)
- **context**: Description/context for the fix
- **code_snippet**: Original code with violation
- **expected_fix**: Expected corrected code (optional)
- **test_code**: Unit test to verify correctness (optional)
- **expected_metrics**: Expected metric values (optional)

## Customizing Evaluation

### Enable/Disable Dimensions

Edit `config.yaml`:

```yaml
evaluation_dimensions:
  functional_correctness:
    enabled: true
    compile_check: true

  code_quality:
    enabled: true
    tools:
      - pylint
      - radon

  security:
    enabled: true

  efficiency:
    enabled: false  # Requires runtime execution

  explainability:
    enabled: true
```

### Adjust Thresholds

```yaml
evaluation_dimensions:
  code_quality:
    thresholds:
      max_complexity: 10
      min_pylint_score: 7.0
```

## Understanding Results

### Pass/Fail Criteria

A test case **passes** if:
- ✓ Resolves the original violation
- ✓ Does not introduce new violations
- ✓ Compiles successfully (if enabled)
- ✓ No high-severity security issues

### Metrics Explained

**Functional Correctness**
- `functional_correctness`: Does the fix resolve the violation?
- `compiles`: Does the code compile?
- `introduces_violations`: Are new violations introduced?

**Code Quality**
- `pylint_score`: 0-10 score from pylint
- `cyclomatic_complexity`: Complexity metric
- `maintainability_index`: 0-100 maintainability score

**Security**
- `security_issues`: Total security issues found
- `high_severity_security`: Count of high-severity issues

**Performance**
- `response_time_ms`: LLM response latency
- `tokens_used`: Total tokens consumed
- `estimated_cost`: Cost in USD

## Report Formats

### HTML Report

Interactive dashboard with:
- Model comparison charts
- Response time distributions
- Per-rule performance breakdown
- Detailed results table

Open in browser:
```bash
open results/evaluation_report_*.html
```

### Markdown Report

Text-based report with:
- Summary statistics
- Per-model metrics
- Failure analysis with examples

View with:
```bash
cat results/evaluation_report_*.md
```

### Raw JSON

All evaluation data in JSON format:
```bash
cat results/results_*.json | jq
```

## Advanced Usage

### Comparing Multiple Models

Add models to `config.yaml`:

```yaml
models:
  - name: "gpt-4-turbo"
    provider: "openai"
    # ...

  - name: "gpt-3.5-turbo"
    provider: "openai"
    # ...

  - name: "claude-3-5-sonnet"
    provider: "anthropic"
    # ...
```

All models will be evaluated in parallel.

### Batch Evaluation

Evaluate multiple test suites:

```bash
for suite in benchmarks/test_cases/*.yaml; do
  python evaluate.py --benchmark "$suite"
done
```

### Custom Prompts

**RECOMMENDED:** Define prompts in your test case YAML files for technology-specific guidance:

```yaml
name: "My Migration Test Suite"
description: "Test cases for my migration"
version: "1.0.0"

prompt: |
  You are helping migrate code based on static analysis rules.

  Rule Violation:
  {rule_description}

  Konveyor Migration Guidance:
  {konveyor_message}

  Original Code:
  ```{language}
  {code_snippet}
  ```

  Context: {context}

  Provide the COMPLETE corrected code and a brief explanation.

rules:
  - rule_id: "..."
    # ... your rules
```

**Alternatively (not recommended):** You can modify the fallback prompt in `config.yaml`, but this applies to all test suites without custom prompts:

```yaml
prompts:
  default: |
    Fix the following code violation:

    Rule: {rule_description}

    Code:
    {code_snippet}

    Provide the fixed code and explanation.
```

**Auto-generated prompts:** When using `--all-rulesets` with `--source` and `--target` filters, appropriate technology-specific prompts are automatically generated (e.g., Java EE→Quarkus, EAP7→EAP8, Spring Boot→Quarkus).

## Integrating with Konveyor Analyzer

To integrate with actual Konveyor static analysis:

1. Install Konveyor analyzer
2. Update `config.yaml`:

```yaml
static_analysis:
  analyzer_command: "konveyor-analyzer"
  rules_path: "path/to/rules/"
```

3. The framework will automatically re-run analysis on generated fixes

## Troubleshooting

### API Rate Limits

Reduce parallel requests in `config.yaml`:

```yaml
execution:
  parallel_requests: 1  # Slower but avoids rate limits
```

### Compilation Failures

Ensure Java/Python compilers are installed:

```bash
javac -version
python --version
```

### Missing Evaluators

Install required tools:

```bash
pip install pylint radon bandit black
```

## Contributing Test Cases

To contribute test cases:

1. Create YAML file in `benchmarks/test_cases/`
2. Follow the schema in `benchmarks/schema.py`
3. Include diverse complexity levels
4. Add clear expected fixes and context
