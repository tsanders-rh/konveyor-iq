# Recommended Workflow

## Quick Start: From Konveyor Rules to AI Evaluation

### 1. Generate Test Cases
```bash
# Generate from all Quarkus rulesets
python scripts/generate_tests.py --all-quarkus

# Or generate from specific migration path with auto-generation
python scripts/generate_tests.py --all-rulesets --source java-ee --target quarkus \
  --auto-generate --model gpt-4-turbo

# With validation (agentic workflow - compiles and fixes errors automatically)
python scripts/generate_tests.py --all-rulesets --source java-ee --target quarkus \
  --auto-generate --validate --model gpt-4-turbo
```

**Output:** `benchmarks/test_cases/generated/quarkus.yaml` (or similar)

**Pro tips:**
- Use `--auto-generate --validate` for higher quality test cases (compiles on first try)
- Process in batches with `--batch-size 20` for large test suites
- Press **Ctrl+C** to pause and save progress - re-run same command to resume

### 2. Classify Migration Complexity
```bash
# Preview classifications
python scripts/classify_rule_complexity.py benchmarks/test_cases/generated/quarkus.yaml --dry-run

# Apply classifications
python scripts/classify_rule_complexity.py benchmarks/test_cases/generated/quarkus.yaml
```

**Why?** Sets appropriate expectations for AI success rates by difficulty level.

**Output:** YAML file updated with `migration_complexity` field for each rule.

### 3. Validate Test Cases
```bash
# Check compilation status
python scripts/validate_expected_fixes.py benchmarks/test_cases/generated/quarkus.yaml
```

**Typical results:**
- ~50% compilation failures (due to `javax.*` vs `jakarta.*` namespace issues)
- Some non-compilable tests properly skipped

### 4. Fix Compilation Errors by Complexity

**Start with TRIVIAL/LOW** (mechanical changes - highest success rate):
```bash
python scripts/fix_expected_fixes.py \
  --file benchmarks/test_cases/generated/quarkus.yaml \
  --complexity trivial,low
```

**Then try MEDIUM** (requires context understanding):
```bash
python scripts/fix_expected_fixes.py \
  --file benchmarks/test_cases/generated/quarkus.yaml \
  --complexity medium
```

**HIGH/EXPERT** (architectural changes - may need manual review):
```bash
# Use dry-run first to see what would be attempted
python scripts/fix_expected_fixes.py \
  --file benchmarks/test_cases/generated/quarkus.yaml \
  --complexity high,expert \
  --dry-run
```

**Key features:**
- ✅ Agentic workflow: Iterates until compilation succeeds (max 3 attempts)
- ✅ Passes compilation errors to LLM for self-correction
- ✅ Includes migration guidance (Java EE → Quarkus patterns)
- ✅ Explicitly instructs LLM to use `jakarta.*` not `javax.*`
- ✅ Skips non-compilable tests automatically
- ✅ Validates each fix before applying

**Pro tips:**
- Large test suites? Process incrementally - progress saved after each fix
- Press **Ctrl+C** to interrupt gracefully - re-run same command to resume
- Use `--verbose` to see detailed LLM responses and compilation errors
- Use `--dry-run` first to preview what would be fixed

### 5. Re-validate
```bash
python scripts/validate_expected_fixes.py benchmarks/test_cases/generated/quarkus.yaml
```

**Expected improvement:** 80-95% pass rate on TRIVIAL/LOW, 60%+ on MEDIUM.

### 6. Run AI Evaluation

**Evaluate by complexity level:**
```bash
# TRIVIAL only (expect 95%+ success)
python evaluate.py \
  --benchmark benchmarks/test_cases/generated/quarkus.yaml \
  --filter-complexity trivial

# TRIVIAL + LOW (expect 80-95% success)
python evaluate.py \
  --benchmark benchmarks/test_cases/generated/quarkus.yaml \
  --filter-complexity trivial,low

# All except EXPERT (production-ready migrations)
python evaluate.py \
  --benchmark benchmarks/test_cases/generated/quarkus.yaml \
  --exclude-complexity expert
```

### 7. Review Results

Open the HTML report:
```bash
open results/evaluation_report_*.html
```

**Look for:**
- **Complexity breakdown table** - Shows pass rates by difficulty level (TRIVIAL → EXPERT)
- **Model performance comparison** - See which models excel at each complexity tier
- **Individual test cards** - Each shows complexity badge and detailed results
- **Detailed failure analysis** - Compilation errors, security issues, code quality
- **Security metrics** - Vulnerability detection and code quality scores

## Expected Success Rates

| Complexity | AI Success | Recommendation |
|-----------|-----------|----------------|
| **TRIVIAL** | 95%+ | ✅ Full automation |
| **LOW** | 80%+ | ✅ Automation with light review |
| **MEDIUM** | 60%+ | ⚡ AI acceleration + developer completion |
| **HIGH** | 30-50% | 🔍 AI scaffolding + expert review |
| **EXPERT** | <30% | 📋 AI checklist + human migration |

## Troubleshooting

### "Found X compilation failures"
**Solution:** Run the fix script with `--complexity trivial,low` first. This addresses most namespace issues.

### "Failed to fix after 3 attempts"
**Common causes:**
- HIGH/EXPERT complexity (architectural changes beyond simple fixes)
- Spring → Quarkus security migrations (need manual patterns)

**Solution:** Either manually fix or mark as `compilable: false` with reason.

### "Script taking too long / want to pause?"
**Solution:** Press **Ctrl+C** (or Cmd+C on Mac) to gracefully interrupt:
- Finishes current fix/generation
- Saves all progress to YAML file
- Shows summary of completed work
- Re-run the same command to resume from where you left off

Both `generate_tests.py` and `fix_expected_fixes.py` support graceful interruption.

### "Want to preview fixes before applying?"
**Solution:** Use `--dry-run` flag:
```bash
python scripts/fix_expected_fixes.py \
  --file benchmarks/test_cases/generated/quarkus.yaml \
  --complexity trivial,low \
  --dry-run
```
Shows what would be fixed without modifying files.

### "No module named 'yaml'" or "No module named 'pydantic'"
**Solution:** Install dependencies:
```bash
pip install -r requirements.txt
```

## Documentation

- **[SETUP.md](docs/SETUP.md)** - Installation and configuration
- **[COMPLEXITY_CLASSIFICATION.md](docs/COMPLEXITY_CLASSIFICATION.md)** - Detailed classification system
- **[README.md](README.md)** - Full feature documentation

## Key Insights

### Why 50% of tests initially fail compilation

**Root cause:** LLM-generated `expected_fix` code uses old Java EE namespace (`javax.*`) instead of Jakarta EE (`jakarta.*`).

**Evidence:**
- 583 `javax.*` imports in expected_fix code
- 507 `jakarta.*` imports in expected_fix code

**Solution:** The fix script now includes migration guidance that explicitly states:
> "Use Jakarta EE packages (jakarta.*) NOT Java EE (javax.*)"

This dramatically improves fix success rate for TRIVIAL/LOW complexity migrations.

### Why complexity classification matters

**Without classification:** Mixed 50% pass rate obscures AI value.

**With classification:**
- TRIVIAL: 95% pass rate → Demonstrates automation capability
- LOW: 82% pass rate → Shows strong automation with light review
- MEDIUM: 64% pass rate → Proves acceleration value
- HIGH: 45% pass rate → AI provides useful scaffolding
- EXPERT: 20% pass rate → AI assists with explanation/checklist

This segmentation sets appropriate expectations and demonstrates AI value at each level.
