# Automating Test Case Fixes

## Overview

The `fix_expected_fixes.py` script uses an LLM to automatically fix compilation errors in `expected_fix` code segments. This dramatically reduces the manual work required to maintain high-quality test cases.

## How It Works

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Validate expected_fix code                              │
│    → Find compilation errors                               │
└─────────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. For each failure:                                        │
│    → Build fix prompt with:                                 │
│      • Original code                                        │
│      • Expected fix (broken)                                │
│      • Compilation error                                    │
│      • Context                                              │
└─────────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. Query LLM for fix                                        │
│    → LLM analyzes error and generates corrected code        │
└─────────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. Validate fix compiles                                    │
│    → If fails, retry with updated error (up to 3 attempts)  │
└─────────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│ 5. Update YAML file                                         │
│    → Replace old expected_fix with corrected version        │
└─────────────────────────────────────────────────────────────┘
```

## Usage

### Validate Only (No Fixes)

Just check for compilation errors without attempting fixes:

```bash
# Using dedicated validator (fast, no API key needed)
python scripts/validate_expected_fixes.py --file benchmarks/test_cases/generated/quarkus.yaml

# OR using fix script in validate-only mode
python scripts/fix_expected_fixes.py --file benchmarks/test_cases/generated/quarkus.yaml --validate-only
```

### Basic Usage

Fix all compilation errors in a file:

```bash
python scripts/fix_expected_fixes.py --file benchmarks/test_cases/generated/quarkus.yaml
```

The script will:
1. **Automatically validate first** and show what needs fixing
2. Skip fixing if everything already compiles
3. Attempt to fix each compilation error with LLM
4. Update the YAML file with fixes

### Dry Run (Preview Changes)

See what would be fixed without modifying files:

```bash
python scripts/fix_expected_fixes.py --file benchmarks/test_cases/generated/quarkus.yaml --dry-run
```

### Fix Specific Rule

Only fix test cases for a specific rule:

```bash
python scripts/fix_expected_fixes.py \
  --file benchmarks/test_cases/generated/quarkus.yaml \
  --rule-id jms-to-reactive-quarkus-00010
```

### Use Different Model

Use a different LLM model (default is gpt-4-turbo):

```bash
python scripts/fix_expected_fixes.py \
  --file benchmarks/test_cases/generated/quarkus.yaml \
  --model claude-3-7-sonnet-latest
```

### Verbose Output

See detailed LLM responses and compilation attempts:

```bash
python scripts/fix_expected_fixes.py \
  --file benchmarks/test_cases/generated/quarkus.yaml \
  --verbose
```

## Example Session

```bash
$ python scripts/fix_expected_fixes.py --file benchmarks/test_cases/generated/quarkus.yaml

================================================================================
INITIAL VALIDATION
================================================================================

================================================================================
Validating: benchmarks/test_cases/generated/quarkus.yaml
================================================================================

✗ jms-to-reactive-quarkus-00010 - tc001: COMPILATION FAILED
✗ jms-to-reactive-quarkus-00020 - tc001: COMPILATION FAILED

--------------------------------------------------------------------------------
Summary for quarkus.yaml:
  Total: 50
  Passed: 48 (96.0%)
  Failed: 2 (4.0%)
--------------------------------------------------------------------------------

Found 2 compilation failure(s).
Proceeding with automated fixes...

================================================================================
Processing: benchmarks/test_cases/generated/quarkus.yaml
================================================================================

────────────────────────────────────────────────────────────────────────────────
Fixing: jms-to-reactive-quarkus-00010 - tc001
────────────────────────────────────────────────────────────────────────────────

Attempt 1/3...
  → Querying LLM for fix...
  → Validating fix compiles...
  ✓ Fix compiles successfully!

────────────────────────────────────────────────────────────────────────────────
Fixing: jms-to-reactive-quarkus-00020 - tc001
────────────────────────────────────────────────────────────────────────────────

Attempt 1/3...
  → Querying LLM for fix...
  → Validating fix compiles...
  ✓ Fix compiles successfully!

================================================================================
Applying 2 fix(es) to benchmarks/test_cases/generated/quarkus.yaml
================================================================================

✓ Updated benchmarks/test_cases/generated/quarkus.yaml

================================================================================
SUMMARY
================================================================================
Total compilation failures: 5
Fixes applied: 2
Fixes failed: 3
================================================================================
```

## What Gets Fixed

The script handles various compilation error types:

### ✅ Ambiguous Imports

**Before:**
```java
import jakarta.jms.Message;
import org.eclipse.microprofile.reactive.messaging.Incoming;
import org.eclipse.microprofile.reactive.messaging.Message;

public class ExampleBean {
    @Incoming("queue")
    public void onMessage(Message<String> message) {  // ❌ Ambiguous!
        ...
    }
}
```

**After:**
```java
import org.eclipse.microprofile.reactive.messaging.Incoming;

public class ExampleBean {
    @Incoming("queue")
    public void onMessage(String message) {  // ✅ Simple type
        ...
    }
}
```

### ✅ Incorrect Interface Implementation

**Before:**
```java
import org.eclipse.microprofile.reactive.messaging.Incoming;

public class MessageListener implements MessageListener {  // ❌ Wrong interface
    @Incoming("queue")
    public void onMessage(String message) {
        ...
    }
}
```

**After:**
```java
import org.eclipse.microprofile.reactive.messaging.Incoming;

public class MessageListener {  // ✅ No interface
    @Incoming("queue")
    public void onMessage(String message) {
        ...
    }
}
```

### ✅ Type Mismatches

**Before:**
```java
public void process(Message msg) {  // ❌ Wrong Message type
    String text = msg.getPayload();
}
```

**After:**
```java
public void process(String msg) {  // ✅ Correct type
    String text = msg;
}
```

## What Doesn't Get Fixed

### ❌ Missing Stub Classes

**Error:** `cannot find symbol: class Employee`

**Reason:** The code references domain classes not in the stub library.

**Solution:** This is intentional - add stubs separately or mark test as non-Java.

### ❌ Non-Java Code

**Error:** Various compilation errors on XML/YAML/properties files

**Reason:** The test case language is set to "java" but contains non-Java code.

**Solution:** Set `language: xml` or appropriate language in test case metadata.

### ❌ Semantic Errors

**Error:** Code compiles but implements wrong migration pattern

**Reason:** The LLM is fixing syntax, not validating migration correctness.

**Solution:** Manual review required - check against migration guidance.

## Important Rules for the LLM

The script instructs the LLM to:

1. **Fix ONLY compilation errors** - Don't change migration approach
2. **Prefer simpler types** - Use `String` over `Message<String>` when possible
3. **Remove conflicting imports** - Especially javax.jms.* vs reactive messaging
4. **Preserve migration patterns** - Keep all annotations and framework usage
5. **Return complete code** - Include all imports, class definition, methods

## Validation Loop

The script validates fixes in a loop:

```
Attempt 1:
  → LLM generates fix
  → Compile fix
  → ✓ Success OR ✗ Use new error for attempt 2

Attempt 2:
  → LLM generates fix based on new error
  → Compile fix
  → ✓ Success OR ✗ Use new error for attempt 3

Attempt 3:
  → LLM generates fix based on new error
  → Compile fix
  → ✓ Success OR ✗ Give up
```

Maximum 3 attempts per test case to avoid infinite loops.

## Cost Considerations

Each fix requires:
- 1-3 LLM API calls (depending on attempts needed)
- Typically ~500-1000 tokens per call

For a file with 50 failures:
- ~50-150 API calls
- ~$0.50-$2.00 with GPT-4 Turbo
- ~5-10 minutes of processing time

**Recommendation:** Use `--dry-run` first to see how many fixes are needed.

## Workflow

### Recommended Process

1. **Preview fixes (validates automatically):**
   ```bash
   python scripts/fix_expected_fixes.py --file path/to/tests.yaml --dry-run
   ```

2. **Apply fixes:**
   ```bash
   python scripts/fix_expected_fixes.py --file path/to/tests.yaml
   ```

   The script automatically:
   - Validates first and shows what needs fixing
   - Skips if everything compiles
   - Attempts fixes for each failure
   - Shows summary of results

3. **Review changes:**
   ```bash
   git diff path/to/tests.yaml
   ```

4. **Commit if satisfied:**
   ```bash
   git add path/to/tests.yaml
   git commit -m "Fix compilation errors in expected_fix code"
   ```

### Alternative: Validate-Only Workflow

If you just want to check without fixing:

```bash
# Fast validation (no API key needed)
python scripts/validate_expected_fixes.py --file path/to/tests.yaml

# OR use fix script in validate-only mode
python scripts/fix_expected_fixes.py --file path/to/tests.yaml --validate-only
```

### Incremental Fixing

Fix one rule at a time for easier review:

```bash
# Fix just one problematic rule
python scripts/fix_expected_fixes.py \
  --file benchmarks/test_cases/generated/quarkus.yaml \
  --rule-id jms-to-reactive-quarkus-00010

# Review the change
git diff benchmarks/test_cases/generated/quarkus.yaml

# Commit if good
git add benchmarks/test_cases/generated/quarkus.yaml
git commit -m "Fix jms-to-reactive-quarkus-00010 expected_fix"

# Repeat for next rule
python scripts/fix_expected_fixes.py \
  --file benchmarks/test_cases/generated/quarkus.yaml \
  --rule-id jms-to-reactive-quarkus-00020
```

## Limitations

1. **LLM is not perfect** - May introduce new bugs while fixing compilation
2. **Semantic validation missing** - Code compiles ≠ code is correct migration
3. **Context limitations** - LLM doesn't see full project context
4. **Cost** - Each fix costs money/tokens
5. **No undo** - Make sure to review `git diff` before committing

## Best Practices

### ✅ DO

- Use `--dry-run` first
- Review all changes with `git diff`
- Fix incrementally by rule_id for easier review
- Re-validate after applying fixes
- Test migrations manually for critical rules

### ❌ DON'T

- Blindly commit all fixes without review
- Skip validation after fixing
- Use on production test cases without backup
- Trust fixes for security-critical migrations without manual review

## Troubleshooting

### "Failed to fix after 3 attempts"

**Cause:** LLM can't resolve the compilation error

**Solutions:**
- Check if it's a missing stub class (expected)
- Try a different model with `--model`
- Fix manually and commit
- Review error with `--verbose`

### "Fix compiles but looks wrong"

**Cause:** LLM fixed syntax but changed semantics

**Solutions:**
- Revert the change: `git checkout path/to/file.yaml`
- Fix manually with correct migration pattern
- Update migration guidance in `config/migration_guidance.yaml`

### "Too many API errors"

**Cause:** Rate limiting or API quota exceeded

**Solutions:**
- Wait and retry
- Reduce parallel requests
- Use a different model
- Process in smaller batches with `--rule-id`

## Integration with CI/CD

### Pre-commit Hook

Validate expected fixes before committing:

```bash
#!/bin/bash
# .git/hooks/pre-commit

python scripts/validate_expected_fixes.py || {
    echo "❌ Expected fixes have compilation errors!"
    echo "Run: python scripts/fix_expected_fixes.py --file <file>"
    exit 1
}
```

### GitHub Actions

```yaml
name: Validate Test Cases
on: [pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Validate expected fixes
        run: python scripts/validate_expected_fixes.py
```

## Example Fix Session

Here's a real example of fixing the JMS ambiguous import issue:

```bash
$ python scripts/fix_expected_fixes.py \
    --file benchmarks/test_cases/generated/quarkus.yaml \
    --rule-id jms-to-reactive-quarkus-00010 \
    --verbose

================================================================================
Processing: benchmarks/test_cases/generated/quarkus.yaml
================================================================================

────────────────────────────────────────────────────────────────────────────────
Fixing: jms-to-reactive-quarkus-00010 - tc001
────────────────────────────────────────────────────────────────────────────────

Attempt 1/3...
  → Querying LLM for fix...

LLM Response:
The issue is that both `javax.jms.Message` and
`org.eclipse.microprofile.reactive.messaging.Message` are imported,
creating ambiguity. Since we're migrating to Reactive Messaging,
we should use String parameter instead of Message<String>.

FIXED CODE:
```java
import jakarta.enterprise.context.ApplicationScoped;
import org.eclipse.microprofile.reactive.messaging.Incoming;

@ApplicationScoped
public class ExampleMessageBean {

    @Incoming("my-queue")
    public void onMessage(String message) {
        try {
            System.out.println("Received message: " + message);
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}
```

  → Validating fix compiles...
  ✓ Fix compiles successfully!

================================================================================
Applying 1 fix(es) to benchmarks/test_cases/generated/quarkus.yaml
================================================================================

✓ Updated benchmarks/test_cases/generated/quarkus.yaml

================================================================================
SUMMARY
================================================================================
Total compilation failures: 1
Fixes applied: 1
Fixes failed: 0
================================================================================
```

Perfect! The LLM understood the ambiguous import issue and simplified to use `String` instead of `Message<String>`.
