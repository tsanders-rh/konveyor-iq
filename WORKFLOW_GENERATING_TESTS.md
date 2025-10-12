# Workflow: Generating and Evaluating Test Cases

Complete workflow for generating test cases from Konveyor rulesets and running evaluations.

---

## Quick Start

```bash
# 1. One-time setup (only needed once)
cd evaluators/stubs && mvn clean package

# 2. Generate tests (with LLM auto-generation)
python scripts/generate_tests.py --all-rulesets --target quarkus \
  --local-rulesets ~/projects/rulesets \
  --auto-generate --model gpt-4-turbo

# 3. Run evaluation
python evaluate.py --benchmark benchmarks/test_cases/generated/quarkus.yaml
```

**That's it!** No stub generation step needed.

> 💡 **For detailed script options**, see [docs/generating_tests.md](docs/generating_tests.md)

---

## Why Real JARs?

We use **real JAR dependencies** from Maven Central instead of auto-generated stubs:

✅ **Always accurate** - Real annotations, interfaces, classes
✅ **Zero maintenance** - No guessing class vs annotation
✅ **Scales infinitely** - Works for any test suite size
✅ **Simple workflow** - 2 steps instead of 4

---

## Complete Workflow

### Step 1: One-Time Setup

Download real dependencies (only needed once per machine):

```bash
cd evaluators/stubs
mvn clean package
```

This downloads 78 JARs (~25MB) from Maven Central to `lib/` directory.

**You only need to do this once.** The JARs are cached locally.

---

### Step 2: Generate Test Cases

Clone Konveyor rulesets locally (recommended for speed):

```bash
git clone https://github.com/konveyor/rulesets.git ~/projects/rulesets
```

Generate test cases with LLM auto-generation:

```bash
python scripts/generate_tests.py --all-rulesets --target quarkus \
  --local-rulesets ~/projects/rulesets \
  --auto-generate --model gpt-4-turbo
```

**Output:** `benchmarks/test_cases/generated/quarkus.yaml`

> 💡 **See [docs/generating_tests.md](docs/generating_tests.md)** for:
> - All script options and filters
> - Manual test creation
> - Migration-specific prompts
> - Troubleshooting

---

### Step 3: Run Evaluation

```bash
python evaluate.py --benchmark benchmarks/test_cases/generated/quarkus.yaml
```

**That's it!** The evaluation automatically uses:
- Real JARs from `lib/` (framework code)
- Custom stubs from `stubs.jar` (test domain objects)

All test cases compile correctly without any stub generation step.

---

## Before & After

| Before (Pure Stubs) | After (Real JARs) |
|---------------------|-------------------|
| ❌ 4 steps | ✅ 2 steps |
| ❌ Manual stub fixes | ✅ Always correct |
| ❌ Class vs annotation errors | ✅ Real APIs |
| ❌ Doesn't scale | ✅ Unlimited tests |

---

## Updating Framework Versions

If you need newer Quarkus/Jakarta versions:

```bash
# Edit version in pom.xml
vim evaluators/stubs/pom.xml
# Change: <quarkus.version>3.8.0</quarkus.version>

# Re-download JARs
cd evaluators/stubs && mvn clean package
```

---

## Adding Custom Test Classes

For domain objects used across tests (not framework code):

```bash
# Add to src/common/
cat > evaluators/stubs/src/common/Product.java <<EOF
package common;

public class Product {
    private Long id;
    private String name;
    // getters/setters
}
EOF

# Rebuild stubs.jar
cd evaluators/stubs && ./build.sh
```

**Note:** This is rare. Most classes come from real JARs.

---

## Files You Care About

| File | Purpose |
|------|---------|
| `evaluators/stubs/pom.xml` | Maven deps (update versions here) |
| `evaluators/stubs/lib/` | Downloaded JARs (gitignored, 25MB) |
| `evaluators/stubs/stubs.jar` | Custom test classes (committed, 200KB) |
| `WORKFLOW_GENERATING_TESTS.md` | This guide |
| `evaluators/stubs/README.md` | Stub architecture docs |

---

## Troubleshooting

### "cannot find symbol" compilation errors

**Framework class (jakarta.*, org.eclipse.*, io.quarkus.*):**
```bash
# Re-run Maven to ensure JARs are downloaded
cd evaluators/stubs && mvn clean package
```

**Custom test class:**
```bash
# Add to src/common/ and rebuild stubs.jar
cd evaluators/stubs && ./build.sh
```

### Maven not installed

```bash
# macOS
brew install maven

# Linux
sudo apt-get install maven

# Or use CI with Maven pre-installed
```

---

## CI/CD

In GitHub Actions or other CI systems:

```yaml
steps:
  - run: cd evaluators/stubs && mvn clean package
  - run: python scripts/generate_tests.py --all-rulesets --target quarkus
  - run: python evaluate.py --benchmark benchmarks/test_cases/generated/quarkus.yaml
```

JARs are cached between builds.

---

## Summary

✅ **No more stub generation** - Real JARs handle everything
✅ **Simpler workflow** - 2 steps instead of 4
✅ **Always accurate** - Real APIs, not guesses
✅ **Scales infinitely** - Works for any test suite size

The migration to real JARs permanently solved the scalability problem!

---

## See Also

- **[docs/generating_tests.md](docs/generating_tests.md)** - Complete script reference and options
- **[evaluators/stubs/README.md](evaluators/stubs/README.md)** - Stub architecture details
- **[MIGRATION_TO_REAL_JARS.md](MIGRATION_TO_REAL_JARS.md)** - Migration rationale
