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
export GOOGLE_API_KEY="AIza-your-key-here"  # Optional: for Google Gemini

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

The evaluation script outputs clickable file:// URLs that you can **Cmd+Click** (Mac) or **Ctrl+Click** (Windows/Linux) to open directly.

Alternatively, use these commands:

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
  # OpenAI models
  - name: "gpt-4-turbo"
    provider: "openai"
    api_key: "${OPENAI_API_KEY}"

  - name: "gpt-4o"  # Recommended: best cost/performance
    provider: "openai"
    api_key: "${OPENAI_API_KEY}"

  # Anthropic models
  - name: "claude-3-7-sonnet-latest"  # Recommended: best quality
    provider: "anthropic"
    api_key: "${ANTHROPIC_API_KEY}"

  # Google Gemini models (requires GOOGLE_API_KEY)
  - name: "gemini-1.5-pro"  # Large context window (2M tokens)
    provider: "google"
    api_key: "${GOOGLE_API_KEY}"
    temperature: 0.7
    max_tokens: 8192
```

**Recommended Starting Lineup:**
- **gpt-4o** - Best cost/performance balance (~$0.15/100 tests)
- **claude-3-7-sonnet-latest** - Best overall quality (~$0.27/100 tests)
- **gemini-1.5-pro** - Best for large context (~$0.15/100 tests)

See [docs/model_recommendations.md](docs/model_recommendations.md) for detailed model comparison.

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
    enabled: true  # Uses pattern-based checks by default
  efficiency:
    enabled: false  # Disable if not needed
  explainability:
    enabled: true  # Evaluates explanation quality and comments
```

### Enhance Security Analysis (Optional)

Install Semgrep for comprehensive security scanning:

```bash
pip install semgrep

# Update config.yaml
# security:
#   tools:
#     - semgrep
```

Without Semgrep, the framework uses built-in pattern-based security checks for common vulnerabilities (SQL injection, hardcoded credentials, etc.).

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
  → file:///Users/tsanders/Workspace/konveyor-iq/results/results_20241010_142530.json
Markdown report: results/evaluation_report_20241010_142530.md
  → file:///Users/tsanders/Workspace/konveyor-iq/results/evaluation_report_20241010_142530.md
HTML report: results/evaluation_report_20241010_142530.html
  → file:///Users/tsanders/Workspace/konveyor-iq/results/evaluation_report_20241010_142530.html

============================================================
Evaluation Complete
============================================================
```

**💡 Tip:** The `file://` URLs are clickable in most terminals (VS Code, iTerm2, etc.). Just Cmd+Click (Mac) or Ctrl+Click (Windows/Linux) to open reports directly!

## Understanding the Reports

### HTML Report Includes:

Professional Grafana-style dark theme with Konveyor branding:

- 🎨 **Grafana-style interface**: Dark theme with professional appearance and Konveyor logo
- 📊 **Overall metrics**: Pass rates, costs, response times
- 🏆 **Top performing models ranking**: Comprehensive composite scoring based on:
  - Functional correctness (40%), Compilation (15%), Quality (15%)
  - Security (15%), Explainability (10%), Speed (2.5%), Cost (2.5%)
- 📈 **Interactive Chart.js visualizations**: Model comparison, time distributions, scalable per-rule performance
- 📋 **Detailed tables**: Per-model and per-rule breakdowns
- 🔍 **Enhanced failure analysis**:
  - Click-to-expand failures with side-by-side code comparison
  - Diff highlighting showing incorrect lines in red
  - Detailed failure explanations based on metrics
  - Filter by failure type (compilation, regression, security)
- 🔒 **Security issues display**:
  - Severity-based color coding (HIGH/MEDIUM/LOW)
  - Detailed descriptions and line numbers
- 📝 **Code quality & explainability metrics**:
  - Cyclomatic complexity, maintainability index
  - Explanation quality scores (0-10)
  - Comment density with ideal range highlighting (10-30%)

### Key Metrics to Watch:

- **Overall Score**: Composite ranking score (0-100) weighing all dimensions
- **Pass Rate**: % of test cases that passed all checks (40% weight)
- **Functional Correctness**: % that resolved violations without introducing new issues
- **Code Quality**: Complexity, maintainability index (15% weight)
- **Security Issues**: Count of vulnerabilities detected (15% weight)
- **Explainability**: Quality of explanations and code documentation (10% weight)
- **Response Time**: Average latency per request (2.5% weight)
- **Cost**: Total cost across all evaluations (2.5% weight)

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
