# Konveyor AI Evaluation Framework

A comprehensive evaluation framework for assessing LLM-generated code fixes for rule-based static analysis violations.

## Overview

This framework evaluates LLM performance across multiple dimensions:
- **Functional Correctness**: Does the fix resolve the violation and compile/run?
- **Code Quality**: Readability, style adherence, complexity metrics
- **Security & Safety**: Avoids insecure patterns
- **Efficiency**: Computational performance
- **Explainability**: Quality of explanations/comments
- **Robustness**: Consistency across prompt variations
- **Response Time**: Latency metrics

## Project Structure

```
konveyor-iq/
├── benchmarks/              # Test datasets
│   ├── rules/              # Rule definitions
│   └── test_cases/         # Violation test cases
├── evaluators/             # Metric implementations
│   ├── functional.py       # Functional correctness checks
│   ├── quality.py          # Code quality metrics
│   ├── security.py         # Security analysis
│   ├── efficiency.py       # Performance metrics
│   └── explainability.py   # Explanation quality
├── models/                 # LLM adapters
│   ├── base.py            # Base model interface
│   ├── openai_adapter.py  # OpenAI models
│   ├── anthropic_adapter.py # Claude models
│   └── local_adapter.py    # Local/HF models
├── reporters/              # Report generation
│   ├── html_reporter.py   # HTML dashboard
│   ├── markdown_reporter.py # Markdown reports
│   └── templates/         # Report templates
├── results/                # Evaluation outputs (gitignored)
├── config.yaml             # Configuration
├── evaluate.py             # Main evaluation script
└── requirements.txt        # Python dependencies
```

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Configure models and benchmarks
cp config.example.yaml config.yaml
# Edit config.yaml with your API keys and settings

# Run evaluation
python evaluate.py --benchmark benchmarks/test_cases/java-migration.yaml

# Generate report
python evaluate.py --report results/latest/
```

## Adding Test Cases

Create YAML files in `benchmarks/test_cases/`:

```yaml
test_suite: "Java EE to Quarkus Migration"
rules:
  - rule_id: "java-deprecated-api-001"
    description: "Replace javax.ejb with CDI annotations"
    severity: "high"
    test_cases:
      - id: "tc001"
        code_snippet: |
          @Stateless
          public class UserService {
              // code
          }
        expected_fix: |
          @ApplicationScoped
          public class UserService {
              // code
          }
        context: "EJB to CDI migration"
        expected_metrics:
          functional_correctness: true
          introduces_violations: false
```

## Configuration

Edit `config.yaml` to specify:
- Models to evaluate
- Evaluation dimensions to include
- Static analysis tools to use
- Report format preferences

## Reports

### HTML Reports (Interactive)
- 📊 Model comparison charts with Plotly
- 📈 Response time distributions
- 🎯 Per-rule performance breakdown
- 🔍 **Interactive failure analysis**:
  - Click-to-expand failure cards
  - Side-by-side code comparison
  - Filter by failure type (compilation, regression, security)
  - Color-coded badges for quick identification
  - Detailed metrics per failure

### Markdown Reports
- Per-model performance summary
- Per-rule accuracy breakdown
- Comparative analysis across models
- Failure examples with code snippets
- Cost analysis (tokens/requests)

## License

Apache 2.0
