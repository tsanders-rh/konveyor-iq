# Quick Start Guide

Get started with Konveyor AI evaluation in 5 minutes!

## 1. Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# On Windows, use: venv\Scripts\activate
```

## 2. Install Dependencies

```bash
pip install -r requirements.txt
```

## 3. Set Up Configuration

```bash
# Copy example config
cp config.example.yaml config.yaml

# Set your API keys (choose one method)

# Method 1: Environment variables (recommended)
export OPENAI_API_KEY="sk-your-key-here"
export ANTHROPIC_API_KEY="sk-ant-your-key-here"

# Method 2: Edit config.yaml directly
# Replace ${OPENAI_API_KEY} with your actual key
```

## 4. Run Your First Evaluation

```bash
python evaluate.py --benchmark benchmarks/test_cases/java-ee-quarkus-migration.yaml
```

This will:
- Evaluate all test cases with configured models
- Generate HTML and Markdown reports
- Save results to `results/` directory

## 5. View Results

```bash
# Open HTML report in browser
open results/evaluation_report_*.html

# Or view markdown report
cat results/evaluation_report_*.md
```

## What's Next?

### Add More Models

Edit `config.yaml` to test additional models:

```yaml
models:
  - name: "gpt-4-turbo"
    provider: "openai"
    api_key: "${OPENAI_API_KEY}"

  - name: "claude-3-5-sonnet"  # Add this
    provider: "anthropic"
    api_key: "${ANTHROPIC_API_KEY}"
```

### Create Custom Test Cases

Create a new YAML file in `benchmarks/test_cases/`:

```yaml
name: "My Custom Tests"
description: "Custom rule violations for my migration"
version: "1.0.0"

rules:
  - rule_id: "custom-001"
    description: "My custom rule"
    severity: "high"
    category: "migration"
    test_cases:
      - id: "tc001"
        language: "java"
        context: "Test description"
        code_snippet: |
          // Your code here
        expected_fix: |
          // Expected fix here
```

Then run:

```bash
python evaluate.py --benchmark benchmarks/test_cases/my-custom-tests.yaml
```

### Customize Evaluation

Edit `config.yaml` to enable/disable evaluation dimensions:

```yaml
evaluation_dimensions:
  functional_correctness:
    enabled: true
  code_quality:
    enabled: true
  security:
    enabled: true
  efficiency:
    enabled: false  # Disable if not needed
```

## Example Output

After running evaluation, you'll see:

```
============================================================
Starting Evaluation
============================================================

Evaluating test suite: Java EE to Quarkus Migration
Total rules: 3
Total models: 2

Rule: java-ee-001-stateless-to-cdi (2 test cases)
  Test case: tc001
    Evaluating with gpt-4-turbo... ✓ PASS
    Evaluating with claude-3-5-sonnet... ✓ PASS
  Test case: tc002
    Evaluating with gpt-4-turbo... ✓ PASS
    Evaluating with claude-3-5-sonnet... ✗ FAIL

...

Raw results saved to: results/results_20241010_142530.json
Markdown report: results/evaluation_report_20241010_142530.md
HTML report: results/evaluation_report_20241010_142530.html

============================================================
Evaluation Complete
============================================================
```

## Understanding the Reports

### HTML Report Includes:

- 📊 **Overall metrics**: Pass rates, costs, response times
- 📈 **Interactive charts**: Model comparison, time distributions
- 📋 **Detailed tables**: Per-model and per-rule breakdowns
- ❌ **Failure analysis**: Examples of failed test cases

### Key Metrics to Watch:

- **Pass Rate**: % of test cases that passed all checks
- **Functional Correctness**: % that resolved violations
- **Response Time**: Average latency per request
- **Cost**: Total cost across all evaluations

## Need Help?

- See [USAGE.md](USAGE.md) for detailed documentation
- See [README.md](README.md) for project overview
- Check example test cases in `benchmarks/test_cases/`

## Common Issues

### "Config file not found"
```bash
cp config.example.yaml config.yaml
```

### "API key not set"
```bash
export OPENAI_API_KEY="your-key"
```

### "No module named..."
```bash
# Make sure you activated the virtual environment
source venv/bin/activate
pip install -r requirements.txt
```

### Deactivate Virtual Environment
When you're done working:
```bash
deactivate
```

Happy evaluating! 🚀
