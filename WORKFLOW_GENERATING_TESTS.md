# Workflow: Generating and Evaluating Test Cases

This document explains the complete workflow for generating test cases from Konveyor rulesets.

---

## The New Approach (Post-Migration)

We now use **real JAR dependencies** instead of auto-generated stubs. This eliminates the stub generation step entirely!

**Benefits:**
- ✅ No stub generation needed
- ✅ Framework code always compiles correctly
- ✅ Simpler workflow (2 steps instead of 3)
- ✅ Scales to unlimited test cases

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

Use the test generator to create test cases:

```bash
# Option A: Use local ruleset clone (MUCH FASTER - recommended!)
git clone https://github.com/konveyor/rulesets.git ~/projects/rulesets

python scripts/generate_tests.py --all-rulesets --target quarkus \
  --local-rulesets ~/projects/rulesets \
  --auto-generate \
  --model gpt-4-turbo \
  --batch-size 20

# This creates: benchmarks/test_cases/generated/quarkus.yaml
```

**What this does:**
- Scans Konveyor rulesets for all Quarkus-targeted rules
- Uses GPT-4-Turbo to auto-generate code examples
- Creates test cases with `code_snippet` and `expected_fix`
- Saves incrementally (safe to interrupt and resume)

**Output:**
```
benchmarks/test_cases/generated/
├── quarkus.yaml              # 337 rules, 2680 test cases
├── java-ee-to-quarkus.yaml   # Filtered by source
└── springboot-to-quarkus.yaml
```

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

## What Changed?

### Old Workflow (Before Migration)
```
1. Generate tests
2. Run update_stubs_from_tests.py  ← Manual stub generation
3. Fix class vs annotation errors     ← Manual fixes
4. Run evaluation
```

### New Workflow (After Migration)
```
1. Generate tests
2. Run evaluation  ← That's it!
```

**Why?**
- Real JARs provide all framework classes (Jakarta, Quarkus, MicroProfile)
- Custom test classes (Order, User, Database) already in committed stubs.jar
- No stub generation needed!

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

## CI/CD Integration

```yaml
# Example GitHub Actions workflow
jobs:
  evaluate:
    steps:
      - name: Setup dependencies (one-time)
        run: cd evaluators/stubs && mvn clean package

      - name: Generate tests
        run: python scripts/generate_tests.py --all-rulesets --target quarkus

      - name: Run evaluation
        run: python evaluate.py --benchmark benchmarks/test_cases/generated/quarkus.yaml
```

JARs are cached between builds for speed.

---

## Summary

✅ **Simpler workflow**: No stub generation step
✅ **More accurate**: Real APIs, not guessed stubs
✅ **More scalable**: Works for any number of tests
✅ **More maintainable**: Version bumps instead of manual work

The migration to real JARs eliminated the most error-prone step from the workflow!

---

## See Also

- `evaluators/stubs/README.md` - Detailed stub architecture
- `MIGRATION_TO_REAL_JARS.md` - Migration rationale and benefits
- `QUICK_REFERENCE.md` - Quick command reference
