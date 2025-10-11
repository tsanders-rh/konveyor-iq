# Konveyor AI Evaluation Framework - Roadmap

This document outlines potential enhancements to improve the evaluation framework's capabilities, usability, and real-world applicability.

## High Priority Enhancements

### 1. Automated Test Case Generation from Konveyor Rules

**Status:** 🟢 Completed
**Priority:** High
**Complexity:** Medium
**Impact:** High - Dramatically reduces manual test case creation
**Completed:** 2024-10-11

**Description:**
Automatically generate test case templates by parsing Konveyor ruleset YAML files. Extract rule patterns, messages, and conditions to create skeleton test cases.

**Implementation:**
```bash
# Generate test cases from a ruleset
python scripts/generate_tests.py \
  --ruleset https://github.com/konveyor/rulesets/.../200-ee-to-quarkus.windup.yaml \
  --output benchmarks/test_cases/generated/
```

**Features:**
- Parse all Konveyor ruleset files
- Extract `when` conditions to understand code patterns
- Use rule `message` for context
- Generate template test cases with placeholders
- Support batch generation across multiple rulesets
- Create both positive (should fix) and negative (should not break) test cases

**Benefits:**
- Scale test coverage quickly
- Ensure alignment with official Konveyor rules
- Reduce manual effort by 80%+
- Keep tests synchronized with ruleset updates

**Files to Create:**
- `scripts/generate_tests.py` - Main generator
- `templates/test_case_template.yaml` - Template structure
- `docs/generating_tests.md` - User guide

---

### 2. Real Codebase Scanning & Evaluation

**Status:** 🔴 Not Started
**Priority:** High
**Complexity:** High
**Impact:** High - Validates on real-world code

**Description:**
Evaluate LLM performance on actual Java EE/Spring applications instead of synthetic test cases. Discover violations in real code, generate fixes, and measure success.

**Implementation:**
```bash
# Scan and evaluate a real repository
python evaluate.py \
  --mode real-repo \
  --repo /path/to/java-ee-app \
  --analyzer konveyor-analyzer \
  --rules ee-to-quarkus,persistence-to-quarkus
```

**Workflow:**
1. Clone or point to existing Java repository
2. Run Konveyor analyzer to discover violations
3. For each violation:
   - Extract code snippet with context
   - Send to LLM for fixing
   - Apply fix and re-analyze
   - Measure if violation resolved
4. Generate comprehensive report

**Features:**
- Integration with konveyor-analyzer CLI
- Configurable context extraction (method, class, file)
- Safe sandbox for applying/testing fixes
- Git diff generation for review
- Support for popular open-source Java EE apps as benchmarks

**Benefits:**
- Real-world validation
- Discover edge cases not in synthetic tests
- Generate training data from actual code
- Demonstrate practical value to users

**Files to Create:**
- `real_repo_evaluator.py` - Main orchestrator
- `code_extractors/java_context.py` - Extract code with context
- `analyzers/konveyor_adapter.py` - Integrate with analyzer
- `benchmarks/real_repos.yaml` - List of test repositories

---

### 3. Regression Testing & Historical Tracking

**Status:** 🔴 Not Started
**Priority:** High
**Complexity:** Medium
**Impact:** High - Prevents quality degradation

**Description:**
Track evaluation metrics over time to detect regressions, monitor improvements, and establish quality baselines.

**Implementation:**
```bash
# Run with baseline comparison
python evaluate.py \
  --benchmark benchmarks/test_cases/java-ee-quarkus-migration.yaml \
  --baseline results/history/2024-10-01_baseline.json \
  --alert-on-regression
```

**Features:**
- Store timestamped results in `results/history/`
- Compare current run against baseline
- Track metrics: pass rate, cost, response time, security issues
- Alert if pass rate drops >5% or cost increases >20%
- Generate trend charts (weekly, monthly)
- Support for custom regression thresholds

**Data Structure:**
```yaml
history/
  2024-10-01_gpt4-turbo_baseline.json
  2024-10-05_gpt4-turbo.json
  2024-10-11_gpt4-turbo.json
  regression_report.html  # Trend visualization
```

**Benefits:**
- Catch quality regressions early
- Track model improvements over versions
- Justify infrastructure costs with data
- Identify optimal model upgrade timing

**Files to Create:**
- `reporters/regression_reporter.py` - Compare runs
- `storage/history_manager.py` - Manage historical data
- `templates/regression_report.html` - Trend visualizations

---

### 4. CI/CD Integration

**Status:** 🔴 Not Started
**Priority:** High
**Complexity:** Low
**Impact:** Medium - Automates quality checks

**Description:**
Integrate evaluation into GitHub Actions to automatically test on every commit, PR, or schedule.

**Implementation:**
```yaml
# .github/workflows/evaluate.yml
name: LLM Evaluation

on:
  push:
    branches: [main]
  pull_request:
  schedule:
    - cron: '0 0 * * 0'  # Weekly

jobs:
  evaluate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run Evaluation
        run: |
          python evaluate.py --benchmark benchmarks/test_cases/
      - name: Compare vs Baseline
        run: |
          python scripts/compare_baseline.py
      - name: Post Results
        uses: actions/github-script@v6
        # Post results as PR comment
```

**Features:**
- Run on PR to test changes
- Scheduled weekly runs for monitoring
- Fail CI if pass rate < threshold
- Post results as PR comments
- Upload reports as artifacts
- Support for secrets (API keys)

**Benefits:**
- Automated quality gates
- Early detection of prompt regressions
- Continuous monitoring
- Team visibility into LLM performance

**Files to Create:**
- `.github/workflows/evaluate.yml` - GitHub Actions workflow
- `.github/workflows/nightly.yml` - Scheduled full evaluation
- `scripts/compare_baseline.py` - Baseline comparison
- `scripts/post_pr_comment.py` - GitHub PR commenting

---

## Medium Priority Enhancements

### 5. Multi-Model Prompt Optimization

**Status:** 🔴 Not Started
**Priority:** Medium
**Complexity:** Medium
**Impact:** Medium - Optimizes prompt effectiveness

**Description:**
A/B test different prompt strategies to find the optimal configuration per model.

**Configuration:**
```yaml
# config.yaml
prompt_experiments:
  - name: "baseline"
    template: "default"
    temperature: 0.7

  - name: "few-shot-3"
    template: "few_shot"
    num_examples: 3
    temperature: 0.5

  - name: "chain-of-thought"
    template: "cot"
    reasoning_steps: true
    temperature: 0.7

  - name: "structured-output"
    template: "structured"
    response_format: "json"
```

**Features:**
- Test multiple prompt variations simultaneously
- Compare pass rates across strategies
- Measure cost vs. accuracy tradeoff
- Automatically select best-performing approach
- Support for few-shot learning with examples
- Chain-of-thought prompting option

**Benefits:**
- Optimize per-model performance
- Find cost-effective strategies
- Improve migration accuracy
- Data-driven prompt engineering

**Files to Create:**
- `experiments/prompt_optimizer.py` - A/B testing engine
- `prompts/few_shot_examples.yaml` - Example library
- `prompts/chain_of_thought.yaml` - CoT templates
- `reporters/experiment_reporter.py` - Compare results

---

### 6. Interactive Fix Iteration & Self-Correction

**Status:** 🔴 Not Started
**Priority:** Medium
**Complexity:** Medium
**Impact:** High - Improves fix quality dramatically

**Description:**
Allow LLMs to learn from failures by feeding compilation errors and test failures back as additional context for retry attempts.

**Workflow:**
```python
max_attempts = 3
attempt = 1

while not test_passed and attempt <= max_attempts:
    if attempt == 1:
        fix = llm.generate(base_prompt)
    else:
        # Include previous errors in prompt
        fix = llm.generate(base_prompt + error_feedback)

    result = evaluate_fix(fix)

    if result.compiles and result.tests_pass:
        break
    else:
        error_feedback = format_errors(result)

    attempt += 1
```

**Features:**
- Provide compilation errors to LLM
- Share static analysis violations
- Include test failure messages
- Track improvement across iterations
- Measure success rate by attempt number
- Configurable max retry attempts

**Benefits:**
- Improve pass rate by 20-30%
- Learn from mistakes like human developers
- Reduce need for perfect first-try prompts
- Generate better training data

**Configuration:**
```yaml
iteration:
  enabled: true
  max_attempts: 3
  feedback_types:
    - compilation_errors
    - static_analysis
    - test_failures
    - security_issues
```

**Files to Update:**
- `evaluate.py` - Add iteration loop
- `models/base.py` - Support context accumulation
- `reporters/html_reporter.py` - Show iteration history

---

### 7. Cost Optimization Dashboard

**Status:** 🔴 Not Started
**Priority:** Medium
**Complexity:** Low
**Impact:** Medium - Helps budget planning

**Description:**
Analyze cost vs. quality tradeoffs to recommend optimal model selection for different budgets.

**Report Features:**
```
Cost-Effectiveness Analysis
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Budget Tiers:
  Economy (<$0.05/fix):
    → gpt-3.5-turbo: $0.027/fix, 75% pass rate
    → Recommendation: Good for development/testing

  Standard ($0.05-$0.20/fix):
    → gpt-4o: $0.176/fix, 85% pass rate
    → Recommendation: Balanced production use

  Premium (>$0.20/fix):
    → claude-sonnet-4: $0.272/fix, 92% pass rate
    → Recommendation: Critical migrations only

ROI Analysis:
  Manual developer fix: ~30 min @ $75/hr = $37.50
  gpt-3.5-turbo: $0.027 (99.9% savings, 75% success)
  gpt-4o: $0.176 (99.5% savings, 85% success)
  claude-sonnet-4: $0.272 (99.3% savings, 92% success)

Recommendation: Use gpt-4o for 95% of fixes, claude-sonnet-4
for high-risk migrations, gpt-3.5-turbo for initial testing.
```

**Benefits:**
- Budget-conscious model selection
- Justify costs with ROI data
- Optimize spend without sacrificing quality
- Plan for scale

**Files to Create:**
- `reporters/cost_optimizer.py` - Generate recommendations
- `templates/cost_dashboard.html` - Interactive cost explorer

---

### 8. Export for Fine-Tuning

**Status:** 🔴 Not Started
**Priority:** Medium
**Complexity:** Low
**Impact:** High - Enables custom models

**Description:**
Export successful fixes as training datasets for fine-tuning custom models.

**Implementation:**
```bash
# Export passed test cases as fine-tuning data
python export.py \
  --results results/latest/ \
  --filter passed \
  --format openai-jsonl \
  --output datasets/migration_training.jsonl
```

**Output Format (OpenAI JSONL):**
```jsonl
{"messages": [
  {"role": "system", "content": "You are a Java EE to Quarkus migration expert..."},
  {"role": "user", "content": "Rule: Replace @Stateless...\n\nKonveyor Guidance: Stateless EJBs can be converted...\n\nCode:\nimport javax.ejb.Stateless;..."},
  {"role": "assistant", "content": "FIXED CODE:\nimport jakarta.enterprise.context.ApplicationScoped;...\n\nEXPLANATION: Replaced @Stateless with @ApplicationScoped..."}
]}
```

**Features:**
- Filter by pass rate, model, rule type
- Support multiple formats: OpenAI, Anthropic, HuggingFace
- Include Konveyor guidance in prompts
- Deduplication of similar examples
- Stratified sampling for balanced datasets
- Train/validation/test split

**Benefits:**
- Build specialized migration models
- Reduce long-term costs (fine-tuned < API calls)
- Improve quality on domain-specific tasks
- Offline deployment capability

**Files to Create:**
- `export.py` - Main export script
- `exporters/openai_format.py` - OpenAI JSONL
- `exporters/anthropic_format.py` - Anthropic format
- `exporters/huggingface_format.py` - HF datasets

---

## Low Priority (Nice to Have)

### 9. Parallel & Incremental Evaluation

**Status:** 🔴 Not Started
**Priority:** Low
**Complexity:** Medium
**Impact:** Medium - Speeds up evaluation

**Features:**
- Parallel API requests (10-20 concurrent)
- Incremental mode: only test changed test cases
- Resume from failure
- Distributed evaluation across machines

**Implementation:**
```bash
# Only test new/changed since last run
python evaluate.py --incremental --baseline results/last_run.json

# Parallel execution
python evaluate.py --parallel 10

# Distributed
python evaluate.py --distributed --workers 5
```

---

### 10. Human Review Interface

**Status:** 🔴 Not Started
**Priority:** Low
**Complexity:** High
**Impact:** Low - Manual process

**Description:**
Web-based UI for reviewing generated fixes, approving/rejecting, and providing feedback.

**Features:**
- Side-by-side code comparison
- Approve/reject buttons
- Edit and retest capability
- Export approved fixes
- Team collaboration features

**Tech Stack:**
- FastAPI backend
- React frontend
- SQLite database for reviews

---

## Quick Wins (Easy Implementations)

### A. JSON/CSV Export
Export results in machine-readable formats for analysis in Jupyter, Excel, or BI tools.

```bash
python evaluate.py --export-format json,csv
```

**Complexity:** Low
**Implementation Time:** 1-2 hours

---

### B. Verbose Logging Mode
Log full prompts and responses for debugging.

```bash
python evaluate.py --verbose --log-file debug.log
```

**Complexity:** Low
**Implementation Time:** 30 minutes

---

### C. Filter by Test Case ID
Run specific test cases for debugging.

```bash
python evaluate.py --test-case tc001,tc002,tc003
```

**Complexity:** Low
**Implementation Time:** 1 hour

---

### D. Model Timeout Configuration
Handle slow/stuck model responses gracefully.

```yaml
models:
  - name: gpt-4
    timeout_seconds: 60
    retry_on_timeout: true
```

**Complexity:** Low
**Implementation Time:** 1 hour

---

### E. Summary Email Reports
Send evaluation results via email after completion.

```yaml
reporting:
  email:
    enabled: true
    recipients: [team@example.com]
    smtp_server: smtp.gmail.com
```

**Complexity:** Low
**Implementation Time:** 2 hours

---

### F. Support for Local Models
Integrate with Ollama, vLLM, or other local model servers.

```yaml
models:
  - name: codellama-local
    provider: ollama
    endpoint: http://localhost:11434
```

**Complexity:** Medium
**Implementation Time:** 3-4 hours

---

## Implementation Priority Recommendation

**For Konveyor Use Case:**

1. **Phase 1 (Month 1):** Foundational Scale
   - ✅ Automated test case generation (#1)
   - ✅ Export for fine-tuning (#8)
   - ✅ Quick wins: JSON export, filtering

2. **Phase 2 (Month 2):** Quality & Monitoring
   - ✅ Regression tracking (#3)
   - ✅ CI/CD integration (#4)
   - ✅ Cost optimization dashboard (#7)

3. **Phase 3 (Month 3):** Advanced Features
   - ✅ Real codebase scanning (#2)
   - ✅ Interactive fix iteration (#6)
   - ✅ Prompt optimization (#5)

4. **Phase 4 (Future):**
   - Parallel/incremental evaluation (#9)
   - Human review interface (#10)

---

## Contributing

Want to implement any of these features? See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

**How to propose new enhancements:**
1. Open an issue with the `enhancement` label
2. Describe the use case and benefits
3. Include implementation sketch if possible
4. Tag with priority (high/medium/low)

---

## Tracking

Track implementation progress at: https://github.com/tsanders-rh/konveyor-iq/projects/1

**Status Legend:**
- 🔴 Not Started
- 🟡 In Progress
- 🟢 Completed
- 🔵 Planned
