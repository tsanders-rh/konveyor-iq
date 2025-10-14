# Konveyor AI Evaluation Framework

A comprehensive framework for evaluating LLM performance on application modernization tasks. Automatically generates test cases from Konveyor rules, validates code migrations, and produces professional reports with migration complexity analysis.

## ✨ Key Features

- 🤖 **Automatic test generation** from 2,680+ Konveyor rules with LLM code generation
- 📊 **Migration complexity classification** (TRIVIAL → EXPERT) with expected AI success rates
- 🔄 **Agentic workflows** for self-correcting code generation and fixing
- 📈 **Professional HTML reports** with Grafana-style design and complexity breakdowns
- 🎯 **Multi-dimensional evaluation**: Functional correctness, security, code quality, explainability
- ⚡ **Graceful interruption** with progress saving and resume capability
- 🔍 **Real Java compilation** with 200+ JARs from Maven Central

## 🚀 Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure API keys
cp config.example.yaml config.yaml
# Edit config.yaml with your OpenAI/Anthropic API keys

# 3. Setup Java dependencies (one-time)
cd evaluators/stubs && mvn clean package && cd ../..

# 4. Generate test suite with auto-generated code
python scripts/generate_tests.py --all-rulesets --target quarkus \
  --auto-generate --validate --model gpt-4-turbo

# 5. Classify by complexity
python scripts/classify_rule_complexity.py benchmarks/test_cases/generated/quarkus.yaml

# 6. Run evaluation
python evaluate.py --benchmark benchmarks/test_cases/generated/quarkus.yaml

# 7. View results
open results/evaluation_report_*.html
```

**See [WORKFLOW.md](WORKFLOW.md) for the complete recommended workflow.**

## 📋 Migration Complexity Classification

Automatically categorizes rules by difficulty to set appropriate AI expectations:

| Complexity | AI Success | Example | Automation Strategy |
|-----------|-----------|---------|---------------------|
| **TRIVIAL** | 95%+ | `javax.*` → `jakarta.*` namespace changes | ✅ Full automation |
| **LOW** | 80%+ | `@Stateless` → `@ApplicationScoped` | ✅ Automation with light review |
| **MEDIUM** | 60%+ | JMS → Reactive Messaging patterns | ⚡ AI acceleration + developer completion |
| **HIGH** | 30-50% | Spring Security → Quarkus Security | 🔍 AI scaffolding + expert review |
| **EXPERT** | <30% | Custom security realms, internal APIs | 📋 AI checklist + human migration |

**Why it matters:** Segmented analysis reveals AI value at each difficulty level, not just overall pass rate.

See [docs/COMPLEXITY_CLASSIFICATION.md](docs/COMPLEXITY_CLASSIFICATION.md) for details.

## 📦 Test Generation

Generate test cases from Konveyor rulesets with automatic code generation:

```bash
# Generate from specific migration path (Java EE → Quarkus)
python scripts/generate_tests.py --all-rulesets --source java-ee --target quarkus \
  --auto-generate --validate --model gpt-4-turbo

# With local rulesets (100x faster, no API rate limits)
git clone https://github.com/konveyor/rulesets.git ~/projects/rulesets
python scripts/generate_tests.py --all-rulesets --target quarkus \
  --local-rulesets ~/projects/rulesets \
  --auto-generate --validate --model gpt-4-turbo

# Process in batches for large test suites
python scripts/generate_tests.py --all-rulesets --target quarkus \
  --auto-generate --model gpt-4-turbo \
  --batch-size 20
```

**Features:**
- ✅ Auto-generates `code_snippet` and `expected_fix` using LLM
- ✅ `--validate` flag: Agentic workflow compiles and auto-fixes errors
- ✅ **Ctrl+C** to pause and save progress - resume by re-running same command
- ✅ Auto-detects language from rules (Java, XML, YAML, properties)
- ✅ Includes Konveyor migration guidance in prompts

**Output:** `benchmarks/test_cases/generated/quarkus.yaml`

See [docs/generating_tests.md](docs/generating_tests.md) for full documentation.

## 🔧 Test Validation & Fixing

### Validate Test Cases

```bash
# Check compilation status
python scripts/validate_expected_fixes.py benchmarks/test_cases/generated/quarkus.yaml
```

### Auto-Fix Compilation Errors

```bash
# Fix by complexity level (recommended: start with TRIVIAL/LOW)
python scripts/fix_expected_fixes.py \
  --file benchmarks/test_cases/generated/quarkus.yaml \
  --complexity trivial,low

# Preview fixes without applying
python scripts/fix_expected_fixes.py \
  --file benchmarks/test_cases/generated/quarkus.yaml \
  --dry-run
```

**Features:**
- ✅ Agentic workflow: Iterates with compilation error feedback (max 3 attempts)
- ✅ Migration-specific guidance (Java EE → Quarkus patterns)
- ✅ **Ctrl+C** to pause - progress saved incrementally
- ✅ Auto-skips non-compilable tests (marked with reasons)
- ✅ Validates each fix before applying

See [docs/automating_test_case_fixes.md](docs/automating_test_case_fixes.md) for details.

## 📊 Evaluation & Reports

### Run Evaluation

```bash
# Evaluate all complexity levels
python evaluate.py --benchmark benchmarks/test_cases/generated/quarkus.yaml

# Filter by complexity
python evaluate.py \
  --benchmark benchmarks/test_cases/generated/quarkus.yaml \
  --filter-complexity trivial,low

# Exclude EXPERT level
python evaluate.py \
  --benchmark benchmarks/test_cases/generated/quarkus.yaml \
  --exclude-complexity expert

# Parallel execution for multiple models
python evaluate.py \
  --benchmark benchmarks/test_cases/generated/quarkus.yaml \
  --parallel 4
```

### HTML Reports

**[📊 View Live Sample Report](https://tsanders-rh.github.io/konveyor-iq/)** - Interactive demo (no installation required)

Professional Grafana-style reports with:

- 🎨 **Dark theme** with Konveyor branding
- 📊 **Complexity breakdown table** - Pass rates by difficulty level (TRIVIAL → EXPERT)
- 🏆 **Model ranking** with composite scoring across all dimensions
- 🔍 **Individual test cards** with complexity badges
- 📈 **Interactive charts** - Response time, cost analysis, performance metrics
- 🔒 **Security analysis** - Vulnerability detection with severity levels
- 💡 **Explainability metrics** - Comment density, explanation quality scores
- ⚠️ **Detailed failure analysis** - Diff highlighting, compilation errors

**Output:** `results/evaluation_report_*.html`

## 🎯 Evaluation Dimensions

Tests evaluate LLM performance across:

1. **Functional Correctness** (40% weight)
   - Compiles successfully
   - Resolves original violation
   - No new violations introduced

2. **Compilation Rate** (15% weight)
   - Valid Java syntax
   - Correct imports and dependencies

3. **Code Quality** (15% weight)
   - Cyclomatic complexity
   - Maintainability index
   - Style adherence

4. **Security** (15% weight)
   - No SQL injection vulnerabilities
   - No hardcoded credentials
   - Migration-specific checks (lost @RolesAllowed, etc.)
   - Optional Semgrep integration for comprehensive analysis

5. **Explainability** (10% weight)
   - Explanation quality score (0-10)
   - Comment density (10-30% ideal)

6. **Performance Metrics** (5% weight)
   - Response time
   - Cost efficiency

## 🔒 Security Analysis

Hybrid approach for comprehensive security scanning:

```bash
# Install Semgrep (optional but recommended)
pip install semgrep

# Uncomment in config.yaml:
security:
  tools:
    - semgrep
```

**Without Semgrep:** Fast pattern-based checks for common vulnerabilities
**With Semgrep:** Comprehensive taint analysis and framework-specific rules

## 📁 Project Structure

```
konveyor-iq/
├── benchmarks/              # Test datasets
│   └── test_cases/
│       └── generated/       # Auto-generated from Konveyor rules
├── config/                  # Configuration files
│   └── migration_guidance.yaml  # Migration-specific prompts
├── docs/                    # Documentation
│   ├── SETUP.md
│   ├── COMPLEXITY_CLASSIFICATION.md
│   ├── generating_tests.md
│   └── automating_test_case_fixes.md
├── evaluators/              # Metric implementations
│   ├── functional.py        # Compilation & pattern validation
│   ├── security.py          # Security analysis
│   ├── quality.py           # Code quality metrics
│   └── stubs/              # Java compilation dependencies
│       ├── pom.xml         # Maven dependencies (200+ JARs)
│       └── lib/            # Downloaded JARs
├── models/                  # LLM adapters
│   ├── openai_adapter.py
│   ├── anthropic_adapter.py
│   └── google_adapter.py
├── reporters/               # Report generation
│   └── html_reporter.py    # Grafana-style HTML reports
├── scripts/                 # Utility scripts
│   ├── generate_tests.py   # Generate from Konveyor rules
│   ├── classify_rule_complexity.py  # Classify difficulty
│   ├── validate_expected_fixes.py   # Validate compilation
│   └── fix_expected_fixes.py       # Auto-fix errors
├── config.yaml              # Main configuration
├── evaluate.py              # Main evaluation script
├── WORKFLOW.md              # Recommended workflow
└── requirements.txt         # Python dependencies
```

## 📚 Documentation

- **[WORKFLOW.md](WORKFLOW.md)** - Complete workflow from generation to evaluation
- **[WORKFLOW_GENERATING_TESTS.md](WORKFLOW_GENERATING_TESTS.md)** - Technical architecture and JAR system
- **[docs/SETUP.md](docs/SETUP.md)** - Installation and configuration
- **[docs/COMPLEXITY_CLASSIFICATION.md](docs/COMPLEXITY_CLASSIFICATION.md)** - Classification system details
- **[docs/generating_tests.md](docs/generating_tests.md)** - Test generation guide
- **[docs/automating_test_case_fixes.md](docs/automating_test_case_fixes.md)** - Auto-fixing workflow
- **[docs/validating_expected_fixes.md](docs/validating_expected_fixes.md)** - Validation guide

## 🛠️ Advanced Features

### Agentic Workflows

Both test generation and fixing use agentic workflows for self-correction:

1. **Generate code** → Compile → Get errors
2. **Fix errors with LLM** (passes error feedback)
3. **Validate fix** → Compile → Repeat if needed (max 3 attempts)

This dramatically improves compilation success rates (50% → 85%+).

### Graceful Interruption

Press **Ctrl+C** (or Cmd+C) to pause long-running scripts:
- Finishes current operation
- Saves all progress to YAML
- Shows summary
- Resume by re-running same command

Supported in: `generate_tests.py`, `fix_expected_fixes.py`

### Migration Guidance System

Centralized, technology-specific guidance in `config/migration_guidance.yaml`:

- Java EE → Quarkus patterns
- Spring Boot → Quarkus patterns
- Messaging migrations
- Security migrations

Automatically injected into prompts based on test suite metadata.

### Konveyor Rule Integration

When test cases reference Konveyor rules via `source` URL:
1. Framework fetches official rule from GitHub
2. Extracts migration guidance (`message` field)
3. Includes in LLM prompt under "Konveyor Migration Guidance"

Ensures LLM receives authoritative migration patterns.

## 🔧 Configuration

Edit `config.yaml` to specify:
- **Models**: OpenAI (GPT-4, GPT-3.5), Anthropic (Claude), Google (Gemini)
- **Evaluation dimensions**: Enable/disable metrics
- **Security tools**: Pattern-based or Semgrep
- **Report format**: HTML, Markdown
- **Parallelization**: Number of concurrent workers

## 🎓 Example Results

```
Pass Rate by Complexity (gpt-4-turbo):
- TRIVIAL: 96% (24/25 tests)
- LOW:     84% (21/25 tests)
- MEDIUM:  68% (17/25 tests)
- HIGH:    44% (11/25 tests)
- EXPERT:  20% (5/25 tests)

Overall: 78% (78/125 tests)
```

This segmentation demonstrates AI value at each difficulty level.

## 🤝 Contributing

Contributions welcome! Areas of interest:
- New migration patterns for `evaluators/functional.py`
- Additional migration guidance for `config/migration_guidance.yaml`
- Enhanced security rules
- New LLM adapters

## 📄 License

Apache 2.0

---

**Quick Links:**
- [WORKFLOW.md](WORKFLOW.md) - Recommended workflow
- [docs/SETUP.md](docs/SETUP.md) - Installation guide
- [docs/COMPLEXITY_CLASSIFICATION.md](docs/COMPLEXITY_CLASSIFICATION.md) - Classification details
