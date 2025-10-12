# Quick Reference: Fixing Compilation Errors in Generated Tests

## The Problem
Auto-generated test cases use imports that don't exist in `stubs.jar`, causing compilation errors.

## The Solution
Run this command after generating test cases:

```bash
python scripts/update_stubs_from_tests.py benchmarks/test_cases/generated/*.yaml
```

**This will:**
1. ✅ Scan test files for all `import` statements
2. ✅ Generate missing stub files automatically
3. ✅ Rebuild `stubs.jar` with new stubs
4. ✅ Fix compilation errors

## Complete Workflow

### One-Time Setup
```bash
# Clone Konveyor rulesets locally (MUCH faster than fetching from GitHub)
git clone https://github.com/konveyor/rulesets.git ~/projects/rulesets
```

### Every Time You Generate Tests

```bash
# Step 1: Generate test cases
python scripts/generate_tests.py --all-rulesets --target quarkus \
  --local-rulesets ~/projects/rulesets \
  --auto-generate --model gpt-4-turbo

# Step 2: Update stubs (CRITICAL - don't skip!)
python scripts/update_stubs_from_tests.py \
  benchmarks/test_cases/generated/*.yaml

# Step 3: Run evaluation
python evaluate.py --benchmark benchmarks/test_cases/generated/quarkus.yaml
```

## What Just Got Fixed

**Before today:**
- ❌ `springboot-cloud-config-client-to-quarkus-00000` - compilation errors
- ❌ Manual stub creation required
- ❌ Time-consuming debugging

**After today:**
- ✅ Automatic stub generation from test imports
- ✅ All MicroProfile Config stubs added:
  - `Config` interface
  - `@ConfigProperty` annotation
  - `@IfBuildProperty` annotation
- ✅ Compilation errors fixed
- ✅ Documented workflow for future test generation

## Files Created Today

| File | Purpose |
|------|---------|
| `scripts/update_stubs_from_tests.py` | Auto-generates stubs from test imports |
| `WORKFLOW_GENERATING_TESTS.md` | Complete workflow documentation |
| `CONTRIBUTING_TO_KONVEYOR.md` | How to contribute improvements upstream |
| `QUICK_REFERENCE.md` | This file - quick commands |
| `evaluators/stubs/src/org/eclipse/microprofile/config/Config.java` | Config interface stub |
| `evaluators/stubs/src/org/eclipse/microprofile/config/ConfigSource.java` | ConfigSource interface stub |
| `evaluators/stubs/src/org/eclipse/microprofile/config/inject/ConfigProperty.java` | @ConfigProperty annotation stub |
| `evaluators/stubs/src/io/quarkus/arc/properties/IfBuildProperty.java` | @IfBuildProperty annotation stub |

## Never Worry About Stubs Again

Just remember: **After generating tests, run the stub updater!**

```bash
python scripts/update_stubs_from_tests.py benchmarks/test_cases/generated/*.yaml
```

That's it! The script handles everything else automatically.
