# Workflow: Generating Test Cases and Keeping Stubs Up-to-Date

This document explains the complete workflow for generating test cases from Konveyor rulesets and ensuring the stubs JAR stays synchronized.

---

## The Problem

When auto-generating test cases, LLMs generate code that uses various Java libraries (MicroProfile Config, Quarkus extensions, Jakarta EE APIs, etc.). For these test cases to compile during evaluation, the `evaluators/stubs/stubs.jar` must contain stub definitions for all referenced classes.

**Without this workflow:**
- ❌ New test cases fail to compile
- ❌ Evaluation shows "compilation error" even when code is correct
- ❌ Manual stub creation is tedious and error-prone

**With this workflow:**
- ✅ Stubs are automatically generated from test imports
- ✅ Test cases compile successfully
- ✅ Focus on evaluation quality, not compilation issues

---

## Complete Workflow

### Step 1: Generate Test Cases from Konveyor Rulesets

Use the test generator to create test cases:

```bash
# Option A: Generate from all Quarkus rulesets (uses local clone - MUCH FASTER!)
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

### Step 2: Extract Imports and Generate Stubs

After generating test cases, update the stubs JAR:

```bash
# Run the stub updater on generated tests
python scripts/update_stubs_from_tests.py \
  benchmarks/test_cases/generated/quarkus.yaml

# Or update from ALL generated test files
python scripts/update_stubs_from_tests.py \
  benchmarks/test_cases/generated/*.yaml
```

**What this does:**
1. ✅ Scans all test cases for `import` statements
2. ✅ Identifies missing stub files
3. ✅ Auto-generates stub files for:
   - Annotations (`@ConfigProperty`, `@IfBuildProperty`)
   - Interfaces (`Config`, `ConfigSource`)
   - Classes (as needed)
4. ✅ Rebuilds `stubs.jar` automatically

**Output:**
```
Scanning test files for imports...
  • quarkus.yaml
Found 127 unique imports

Generating missing stubs...
  ✓ Created: src/org/eclipse/microprofile/config/Config.java
  ✓ Created: src/org/eclipse/microprofile/config/inject/ConfigProperty.java
  ✓ Created: src/io/quarkus/arc/properties/IfBuildProperty.java

Created 3 new stub files

Rebuilding stubs.jar...
  ✓ Stubs JAR rebuilt successfully
```

---

### Step 3: Run Evaluation

Now run your evaluation - all test cases should compile:

```bash
python evaluate.py \
  --benchmark benchmarks/test_cases/generated/quarkus.yaml \
  --limit 10
```

**Expected result:**
- ✅ Tests compile successfully
- ✅ Evaluation focuses on correctness, not compilation errors
- ✅ Clean results without missing import errors

---

## Automated Workflow (Recommended)

Combine all steps into a single workflow:

```bash
#!/bin/bash
# generate_and_evaluate.sh

set -e  # Exit on error

echo "Step 1: Generate test cases..."
python scripts/generate_tests.py --all-rulesets --target quarkus \
  --local-rulesets ~/projects/rulesets \
  --auto-generate \
  --model gpt-4-turbo \
  --batch-size 20

echo "Step 2: Update stubs from generated tests..."
python scripts/update_stubs_from_tests.py \
  benchmarks/test_cases/generated/*.yaml

echo "Step 3: Run evaluation..."
python evaluate.py \
  --benchmark benchmarks/test_cases/generated/quarkus.yaml

echo "✓ Complete! Check results/ for evaluation reports"
```

Make it executable:
```bash
chmod +x generate_and_evaluate.sh
./generate_and_evaluate.sh
```

---

## Manual Stub Addition (When Needed)

Sometimes you may need to manually create more sophisticated stubs. Here's how:

### 1. Create the Stub File

Example: `evaluators/stubs/src/org/eclipse/microprofile/config/Config.java`

```java
package org.eclipse.microprofile.config;

import java.util.Optional;

/**
 * Stub for MicroProfile Config interface.
 * Used for compilation testing only.
 */
public interface Config {
    <T> T getValue(String propertyName, Class<T> propertyType);
    <T> Optional<T> getOptionalValue(String propertyName, Class<T> propertyType);
    Iterable<String> getPropertyNames();
}
```

### 2. Rebuild the JAR

```bash
cd evaluators/stubs
./build.sh
```

### 3. Verify

```bash
ls -lh stubs.jar
# Should show increased file size
```

---

## Troubleshooting

### Issue: "cannot find symbol" compilation errors

**Cause:** Missing stub for a class/interface/annotation

**Solution:**
```bash
# Check what's missing from the error
# Error: cannot find symbol: class ConfigProperty

# Run stub updater
python scripts/update_stubs_from_tests.py benchmarks/test_cases/generated/*.yaml

# Or manually add the stub
# evaluators/stubs/src/org/eclipse/microprofile/config/inject/ConfigProperty.java
```

### Issue: Stub generator doesn't create the right type

**Cause:** Auto-detection uses naming conventions (may not always be correct)

**Solution:** Manually create the stub with correct type (interface vs class vs annotation)

### Issue: Generated tests use unavailable APIs

**Cause:** LLM hallucinated or used experimental APIs

**Solution:**
1. **Fix the test case** - Update `expected_fix` to use correct APIs
2. **Add guidance to prompts** - Update test suite prompt to prevent hallucination
3. **Filter rules** - Some rules may not be suitable for auto-generation

---

## Best Practices

### 1. Generate Tests in Batches
```bash
# Use --batch-size to save progress incrementally
python scripts/generate_tests.py --all-rulesets --target quarkus \
  --auto-generate --model gpt-4-turbo \
  --batch-size 20  # Saves every 20 rules
```

### 2. Update Stubs Immediately After Generation
```bash
# Add to your workflow
python scripts/generate_tests.py ... && \
python scripts/update_stubs_from_tests.py benchmarks/test_cases/generated/*.yaml
```

### 3. Preview Changes Before Committing
```bash
# Dry-run to see what would be created
python scripts/update_stubs_from_tests.py \
  benchmarks/test_cases/generated/*.yaml \
  --dry-run
```

### 4. Version Control Stubs
```bash
# Commit both test cases AND updated stubs
git add benchmarks/test_cases/generated/
git add evaluators/stubs/src/
git add evaluators/stubs/stubs.jar
git commit -m "Add Quarkus test cases with updated stubs"
```

---

## Common Import Patterns and Their Stubs

| Import | Stub Location | Type |
|--------|---------------|------|
| `org.eclipse.microprofile.config.Config` | `org/eclipse/microprofile/config/Config.java` | Interface |
| `org.eclipse.microprofile.config.inject.ConfigProperty` | `org/eclipse/microprofile/config/inject/ConfigProperty.java` | Annotation |
| `io.quarkus.runtime.StartupEvent` | `io/quarkus/runtime/StartupEvent.java` | Class |
| `io.quarkus.arc.properties.IfBuildProperty` | `io/quarkus/arc/properties/IfBuildProperty.java` | Annotation |
| `jakarta.enterprise.context.ApplicationScoped` | `jakarta/enterprise/context/ApplicationScoped.java` | Annotation |
| `jakarta.inject.Inject` | `jakarta/inject/Inject.java` | Annotation |

---

## Summary

✅ **Always run after generating tests:**
```bash
python scripts/update_stubs_from_tests.py benchmarks/test_cases/generated/*.yaml
```

✅ **This ensures:**
- No compilation errors from missing imports
- Clean evaluation results
- Focus on code quality, not build issues

✅ **Commit together:**
- Generated test cases
- Updated stub files
- Rebuilt stubs.jar

---

## Further Reading

- `scripts/generate_tests.py --help` - Test generation options
- `scripts/update_stubs_from_tests.py --help` - Stub updater options
- `evaluators/stubs/README.md` - Stub system documentation
- `CONTRIBUTING_TO_KONVEYOR.md` - How to contribute improvements upstream
