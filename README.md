# Konveyor AI Evaluation Framework

A comprehensive evaluation framework for assessing LLM-generated code fixes for rule-based static analysis violations.

## Overview

This framework evaluates LLM performance across multiple dimensions:
- **Functional Correctness**: Does the fix resolve the violation and compile/run?
  - Pattern-based validation (fallback when no analyzer available)
  - Konveyor analyzer integration (optional)
  - Auto-import stripping for missing stubs
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
│   ├── explainability.py   # Explanation quality
│   └── stubs/             # Java stubs for compilation
│       ├── src/           # Stub source files
│       ├── stubs.jar      # Compiled stub classes
│       └── build.sh       # Rebuild script
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

## Generating Test Cases Automatically ⚡

**NEW:** Automatically generate test case templates from Konveyor rulesets!

```bash
# Generate from a single ruleset
python scripts/generate_tests.py \
    --ruleset https://github.com/konveyor/rulesets/blob/main/default/generated/quarkus/200-ee-to-quarkus.windup.yaml

# Generate from ALL Quarkus rulesets (25+ rulesets)
python scripts/generate_tests.py --all-quarkus
```

This creates test case templates with:
- ✅ Rule metadata (ID, description, severity) pre-filled
- ✅ Source URL for automatic Konveyor guidance integration
- ✅ Code hints extracted from rule conditions
- ✅ TODO placeholders for code examples
- ✅ Konveyor migration guidance as comments

**Output:** `benchmarks/test_cases/generated/*.yaml`

Then simply:
1. Fill in the `code_snippet` with violating code
2. Fill in the `expected_fix` with corrected code
3. Run evaluation!

See [docs/generating_tests.md](docs/generating_tests.md) for full documentation.

## Adding Test Cases Manually

Alternatively, create YAML files manually in `benchmarks/test_cases/`:

```yaml
test_suite: "Java EE to Quarkus Migration"
rules:
  - rule_id: "java-deprecated-api-001"
    description: "Replace javax.ejb with CDI annotations"
    severity: "high"
    source: "https://github.com/konveyor/rulesets/blob/main/default/generated/quarkus/200-ee-to-quarkus.windup.yaml"  # Optional: Link to Konveyor rule
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

### Konveyor Rule Integration

When you provide a `source` URL pointing to a Konveyor ruleset, the framework automatically:
1. Fetches the corresponding rule from the Konveyor repository
2. Extracts the official migration guidance (`message` field)
3. Includes it in the LLM prompt under "Konveyor Migration Guidance"

This ensures the LLM receives authoritative migration guidance directly from Konveyor's ruleset definitions.

**Example:** For rule `ee-to-quarkus-00000`, the framework fetches:
> "Stateless EJBs can be converted to a CDI bean by replacing the `@Stateless` annotation with a scope eg `@ApplicationScoped`"

And includes it in the prompt sent to the LLM, improving migration accuracy.

## Configuration

Edit `config.yaml` to specify:
- Models to evaluate (OpenAI, Anthropic)
- Evaluation dimensions to include
- Static analysis configuration:
  - Set `analyzer_command: null` to use pattern-based validation (no external tool needed)
  - Set `analyzer_command: "/path/to/konveyor-analyzer"` to use real analyzer
- Prompt templates optimized for Quarkus/Jakarta EE migrations
- Report format preferences

## Features

### Pattern-Based Functional Validation

When no static analysis tool is available, the framework uses pattern-based validation to check if violations are resolved:

```python
# Checks if old patterns are removed and new patterns are added
patterns = {
    "ee-to-quarkus-00000": {
        "old": ["@Stateless", "import javax.ejb.Stateless"],
        "new": ["@ApplicationScoped"],
    }
}
```

**Supported migration patterns:**
- Java EE to Quarkus (EJB → CDI)
- javax.* → jakarta.* package migrations
- Message-driven beans → Reactive messaging
- Persistence API migrations

### Auto-Import Stripping

The framework automatically strips import statements that cause compilation failures due to missing stubs:

1. Attempts compilation
2. If "package does not exist" error occurs
3. Removes failing import statements
4. Retries compilation

This prevents false failures when LLMs add extra (harmless) imports.

### Java Stub Management

Stub classes enable compilation validation without full dependencies:

```bash
# Add new stub classes
cd evaluators/stubs/src
# Create new .java stub files

# Rebuild JAR
./build.sh
```

**Current stubs include:**
- Jakarta EE annotations (@ApplicationScoped, @SessionScoped, @RequestScoped, etc.)
- Java EE annotations (@Stateless, @Stateful, @Singleton, etc.)
- JMS classes (Message, MessageListener, TextMessage, JMSException)
- MicroProfile Reactive Messaging (@Incoming)
- Common domain objects (User, Order, Payment, Database)

### Security Analysis

**Hybrid approach** - uses best available method:

1. **Semgrep** (if installed): Comprehensive Java security analysis with OWASP Top 10 coverage
2. **Pattern-based** (fallback): Fast, built-in security checks for common vulnerabilities

**Pattern-based security checks:**
- **SQL Injection**: String concatenation in queries
- **Hardcoded Credentials**: Passwords, API keys in code
- **XXE Vulnerabilities**: Unsafe XML parsers
- **Weak Random**: Using `Random` instead of `SecureRandom` for security
- **Path Traversal**: Unsafe file operations
- **Insecure Deserialization**: ObjectInputStream without validation

**Migration-specific checks:**
- **Missing Authorization**: Lost @RolesAllowed in EJB → CDI migration
- **Unprotected Endpoints**: JAX-RS endpoints without security
- **Missing Transactions**: Lost @Transactional for data integrity
- **CSRF Protection**: Disabled CSRF on state-changing endpoints
- **Insecure HTTP**: Custom SSL configuration without validation

**Enable Semgrep** (optional):
```bash
pip install semgrep

# Update config.yaml
security:
  tools:
    - semgrep
```

### Explainability Analysis

**Heuristic-based evaluation** of code explanation quality:

**Explanation Quality Score (0-10):**
- Evaluates the quality of LLM-generated explanations
- Checks for:
  - **Change description**: Explains what was modified
  - **Reason/justification**: Explains why the change was needed
  - **Technical context**: Mentions relevant frameworks/patterns
  - **Migration-specific**: References source/target technologies
  - **Adequate length**: Not too brief (100+ chars) or verbose (2000+ chars)
- Scoring thresholds:
  - **7.0+**: GREEN (excellent explanation)
  - **5.0-7.0**: ORANGE (acceptable)
  - **<5.0**: RED (poor explanation)

**Comment Density (0-100%):**
- Measures ratio of comment lines to total lines in generated code
- Ideal range: **10-30%**
  - **10-30%**: GREEN (well-documented)
  - **>0% but not ideal**: ORANGE (under/over-commented)
  - **0%**: GRAY (no comments)
- Considers both inline comments (`//`) and block comments (`/* */`)
- Excludes blank lines from calculation

**Impact on Model Ranking:**
- Explainability contributes **10%** to overall composite score
- Average of explanation quality (scaled 0-100) and comment density score
- Encourages models to provide clear, well-documented fixes

## Reports

### HTML Reports (Interactive)
- 📊 Model comparison charts with Plotly
- 📈 Response time distributions
- 🎯 Per-rule performance breakdown with rule selector dropdown
- 🏆 **Top performing models ranking** with comprehensive composite scoring:
  - **40%** Pass rate (functional correctness)
  - **15%** Compilation rate
  - **15%** Code quality (complexity + maintainability)
  - **15%** Security (fewer issues = higher score)
  - **10%** Explainability (explanation quality + comment density)
  - **2.5%** Response time (speed)
  - **2.5%** Cost efficiency
  - Displays all metrics for top 3 models with medal rankings
- 🔍 **Enhanced failure analysis**:
  - Click-to-expand failure cards
  - **Diff highlighting** - incorrect lines highlighted in red
  - Expected code vs generated code side-by-side
  - **Detailed failure explanations** based on metrics
  - Filter by failure type (compilation, regression, security)
  - Color-coded badges for quick identification
  - Compilation error details
  - **Security issues display** with severity-based color coding:
    - 🔴 HIGH severity (red) - Critical security vulnerabilities
    - 🟠 MEDIUM severity (orange) - Important security concerns
    - 🔵 LOW severity (blue) - Minor security issues
    - Line numbers (when available from Semgrep)
    - Detailed descriptions for each issue
  - **Code quality and explainability metrics** visualization:
    - Cyclomatic complexity, maintainability index, style violations
    - Explanation quality score (0-10 scale)
    - Comment density percentage with ideal range highlighting (10-30%)

### Markdown Reports
- Per-model performance summary
- Per-rule accuracy breakdown
- Comparative analysis across models
- Failure examples with code snippets
- Cost analysis (tokens/requests)

## Evaluation Criteria

Tests **pass** only if ALL of the following are true:
- ✅ **Compiles successfully** (with Java stubs)
- ✅ **Resolves the original violation** (pattern-based or analyzer-based check)
- ✅ **Does not introduce new violations**
- ✅ **No high-severity security issues**

Tests **fail** if ANY of these occur:
- ❌ Compilation error (even after import stripping)
- ❌ Original violation pattern still present in code
- ❌ New static analysis violations introduced
- ❌ High-severity security issues detected

## Example Results

```
Pass Rate by Model (Java EE → Quarkus):
- gpt-4-turbo:    80% (8/10 tests passed)
- gpt-4o:         80% (8/10 tests passed)
- gpt-3.5-turbo:  80% (8/10 tests passed)

Common failure reasons:
- Does not resolve violation (4x) - Wrong migration pattern
- Compilation error (2x) - Missing stubs or syntax errors
```

## Extending the Framework

### Adding New Migration Patterns

Edit `evaluators/functional.py` to add pattern definitions:

```python
patterns = {
    "your-rule-id": {
        "old": ["@OldAnnotation", "import old.package"],
        "new": ["@NewAnnotation", "import new.package"],
    }
}
```

### Adding New Stubs

1. Create stub file in `evaluators/stubs/src/`
2. Run `./build.sh` to rebuild `stubs.jar`
3. Add auto-import mapping in `evaluators/functional.py` if needed

### Customizing Prompts

Edit `config.yaml` to customize the system prompt and user prompt templates:

```yaml
prompts:
  default: |
    You are helping migrate Java EE code to Quarkus...

    IMPORTANT:
    - Use Jakarta EE (jakarta.*) NOT Spring Framework
    - Follow Quarkus best practices
```

## License

Apache 2.0
