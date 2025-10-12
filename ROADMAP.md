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

### 6. Rule Message Optimization via Feedback Loop

**Status:** 🔴 Not Started
**Priority:** Medium
**Complexity:** Medium
**Impact:** High - Improves Konveyor rule quality and LLM success rates

**Description:**
Analyze evaluation results to identify poorly-performing rules, use LLMs to generate improved guidance messages, validate improvements, and export optimized messages for contribution back to the Konveyor rulesets repository.

**Implementation:**
```bash
# Analyze existing evaluation results
python scripts/optimize_rules.py \
    --results results/results_20241011.json \
    --threshold 0.5  # Rules below 50% pass rate
```

**Workflow:**
1. **Identify Problematic Rules** - Analyze evaluation results to find rules with low pass rates (<50%)
2. **Analyze Failure Patterns** - Group failures by error type (compilation, wrong pattern, incomplete fix, etc.)
3. **Generate Improved Messages** - Use GPT-4/Claude to suggest enhanced guidance based on:
   - Original Konveyor message
   - Observed failure patterns
   - Successful fixes from other models
   - Common pitfalls identified
4. **Validate Improvements** - Re-run evaluation with enhanced messages to measure impact
5. **Export for Contribution** - Generate YAML patches or GitHub PRs for konveyor/rulesets

**Output Format:**
```yaml
rule_improvements:
  - rule_id: jms-to-reactive-quarkus-00000
    original_pass_rate: 33%  # 1/3 models passed

    original_message: |
      Usage of JMS is not supported in Quarkus. It is recommended to use
      Quarkus' SmallRye Reactive Messaging instead of JMS...

    suggested_message: |
      JMS is not supported in Quarkus. Migrate to SmallRye Reactive Messaging:

      Step 1: Replace JMS dependency with:
      <dependency>
        <groupId>io.quarkus</groupId>
        <artifactId>quarkus-smallrye-reactive-messaging</artifactId>
      </dependency>

      Step 2: Replace @MessageDriven with @ApplicationScoped
      Step 3: Use @Incoming("channel-name") on message handler methods
      Step 4: Configure channels in application.properties

      Common pitfall: Don't forget to remove @ActivationConfigProperty -
      it's not used in reactive messaging.

    new_pass_rate: 100%  # 3/3 models passed with improved message
    improvement: +67%

    failed_models_before: [gpt-4o, claude-3-5-sonnet]
    failed_models_after: []

    pr_url: https://github.com/konveyor/rulesets/pulls/1234
```

**Features:**
- Automatic detection of low-performing rules
- LLM-powered message enhancement suggestions
- A/B testing to validate improvements
- Statistical significance testing
- Contribution-ready output (YAML patches, PRs)
- Track improvement metrics over time
- Integration with Konveyor rulesets repo

**Benefits:**
- Improve Konveyor rule quality systematically
- Increase LLM migration success rates
- Reduce manual rule authoring effort
- Data-driven rule improvement process
- Community contributions with validated improvements
- Close the feedback loop between evaluation and rule creation

**Metrics Tracked:**
- Pass rate improvement per rule
- Cost per successful fix (before/after)
- Number of models that benefit
- False positive reduction
- Time saved on manual debugging

**Files to Create:**
- `scripts/optimize_rules.py` - Main optimization engine
- `analyzers/failure_analyzer.py` - Categorize and analyze failures
- `generators/message_enhancer.py` - LLM-powered message generation
- `exporters/ruleset_patcher.py` - Generate Konveyor PR patches
- `docs/rule_optimization.md` - User guide

---

### 7. Interactive Fix Iteration & Self-Correction

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

### 8. Cost Analysis Dashboard (HTML-based)

**Status:** 🟡 In Progress
**Priority:** Medium
**Complexity:** Low
**Impact:** Medium - Helps budget planning

**Description:**
Generate interactive HTML dashboards that analyze cost vs. quality tradeoffs, combining Konveyor analysis reports with LLM evaluation results to provide actionable recommendations for budget planning and model selection.

**Implementation:**
```bash
# Generate cost dashboard from evaluation results
python scripts/generate_cost_dashboard.py \
  --konveyor-analysis analysis/results.json \
  --evaluation-results results/results_latest.json \
  --output reports/cost_dashboard.html

# Optionally specify hourly rate for manual dev cost comparison
python scripts/generate_cost_dashboard.py \
  --konveyor-analysis analysis.json \
  --evaluation-results results.json \
  --hourly-rate 100 \
  --output dashboard.html
```

**Dashboard Features:**
- **Executive Summary Panels**
  - Total estimated cost (LLM + manual)
  - Automation rate percentage
  - ROI calculation
  - Timeline estimation

- **Cost Analysis Charts**
  - Model cost breakdown (per-fix cost × success rate)
  - LLM vs Manual vs Hybrid cost comparison
  - Violation distribution by category

- **Optimization Tables**
  - Optimal model selection by rule category
  - Detailed rule-by-rule cost analysis
  - Recommended action plan with phases

- **Performance Visualizations**
  - Model performance by rule category
  - Success rate trends over time
  - Interactive Chart.js charts

**Output Format:**
- Single HTML file with embedded CSS/JavaScript
- Works offline, no server required
- Can be emailed to stakeholders
- Print-friendly for PDF export
- Interactive charts using Chart.js

**Benefits:**
- Budget-conscious model selection
- Justify costs with ROI data
- Optimize spend without sacrificing quality
- Plan for scale
- **Portable** - single file, no infrastructure needed
- **Shareable** - email to non-technical stakeholders
- **Archival** - static snapshot for project records

**Files to Create:**
- `scripts/generate_cost_dashboard.py` - Dashboard generator from evaluation results
- `dashboards/cost_dashboard_mockup.html` - ✅ Template/mockup (COMPLETED)
- `docs/cost_dashboard.md` - User guide for generating dashboards

---

### 9. Export for Fine-Tuning

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

### 10. Parallel & Incremental Evaluation

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

### 11. Human Review Interface

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
