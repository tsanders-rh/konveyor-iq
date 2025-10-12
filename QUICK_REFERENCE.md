# Quick Reference: Test Generation and Evaluation

## The Simpler Workflow (Post-Migration)

We now use **real JAR dependencies** - no stub generation needed!

```bash
# 1. One-time setup (only needed once)
cd evaluators/stubs && mvn clean package

# 2. Generate tests
python scripts/generate_tests.py --all-rulesets --target quarkus \
  --local-rulesets ~/projects/rulesets \
  --auto-generate --model gpt-4-turbo

# 3. Run evaluation
python evaluate.py --benchmark benchmarks/test_cases/generated/quarkus.yaml
```

**That's it!** No stub generation step needed.

---

## What Changed?

### Before (Pure Stubs)
```
1. Generate tests
2. python scripts/update_stubs_from_tests.py *.yaml  ← REMOVED!
3. Fix @ConfigProperties class vs annotation errors   ← REMOVED!
4. Run evaluation
```

### After (Real JARs)
```
1. mvn package  (one-time setup)
2. Generate tests
3. Run evaluation  ← Clean, simple!
```

**Why the change?**
- ✅ Real JARs from Maven Central (Jakarta, Quarkus, MicroProfile)
- ✅ No more guessing class vs annotation
- ✅ Always accurate compilation
- ✅ Scales to unlimited test cases

---

## One-Time Setup

```bash
# Clone Konveyor rulesets (optional but MUCH faster)
git clone https://github.com/konveyor/rulesets.git ~/projects/rulesets

# Download real dependencies (one-time, ~1 minute)
cd evaluators/stubs
mvn clean package
# This downloads 78 JARs (~25MB) to lib/ directory
```

---

## Generate Tests

```bash
# Full Quarkus migration suite
python scripts/generate_tests.py --all-rulesets --target quarkus \
  --local-rulesets ~/projects/rulesets \
  --auto-generate \
  --model gpt-4-turbo \
  --batch-size 20
```

**Output:** `benchmarks/test_cases/generated/quarkus.yaml`

---

## Run Evaluation

```bash
# Evaluate all test cases
python evaluate.py --benchmark benchmarks/test_cases/generated/quarkus.yaml

# Evaluate first N test cases (for testing)
python evaluate.py --benchmark benchmarks/test_cases/generated/quarkus.yaml --limit 10
```

---

## Updating Framework Versions

```bash
# Edit pom.xml
vim evaluators/stubs/pom.xml
# Change: <quarkus.version>3.8.0</quarkus.version>

# Re-download JARs
cd evaluators/stubs && mvn clean package
```

---

## Troubleshooting

### "cannot find symbol" errors

**Framework class:**
```bash
cd evaluators/stubs && mvn clean package
```

**Custom test class:**
```bash
cd evaluators/stubs && ./build.sh
```

### Maven not installed

```bash
# macOS
brew install maven

# Linux
sudo apt-get install maven
```

---

## What Got Fixed Today

| Issue | Before | After |
|-------|--------|-------|
| @ConfigProperties | ❌ Created as class | ✅ Real annotation from JAR |
| Compilation errors | ❌ Manual stub fixes | ✅ Always correct |
| Scalability | ❌ Manual work per import | ✅ Unlimited tests |
| Workflow complexity | ❌ 4 steps | ✅ 2 steps |

---

## Files You Care About

| File | Purpose |
|------|---------|
| `evaluators/stubs/pom.xml` | Maven deps (update versions here) |
| `evaluators/stubs/lib/` | Downloaded JARs (gitignored, 25MB) |
| `evaluators/stubs/stubs.jar` | Custom test classes (committed, 200KB) |
| `WORKFLOW_GENERATING_TESTS.md` | Complete workflow guide |
| `evaluators/stubs/README.md` | Stub architecture docs |

---

## Summary

✅ **No more stub generation** - Real JARs handle everything
✅ **Simpler workflow** - 2 steps instead of 4
✅ **Always accurate** - Real APIs, not guesses
✅ **Scales infinitely** - Works for any test suite size

The migration to real JARs permanently solved the scalability problem!
