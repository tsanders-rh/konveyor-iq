# Validating Expected Fix Code

## Overview

The `validate_expected_fixes.py` script verifies that all `expected_fix` code segments in test case YAML files compile successfully. This helps catch issues where the "correct answer" defined in test cases doesn't actually compile.

## Why This Matters

When creating test cases, it's easy to write `expected_fix` code that:
- Has syntax errors
- References undefined classes/methods
- Uses incorrect imports
- Contains other compilation issues

If the expected fix doesn't compile, then:
1. LLMs have no correct example to follow
2. Test cases can't properly evaluate model performance
3. Migration guidance may be incorrect or incomplete

## Usage

### Validate All Test Cases

```bash
python scripts/validate_expected_fixes.py
```

This will scan all YAML files in `benchmarks/test_cases/` and validate every `expected_fix`.

### Validate a Specific File

```bash
python scripts/validate_expected_fixes.py --file benchmarks/test_cases/generated/quarkus.yaml
```

### Verbose Output

```bash
python scripts/validate_expected_fixes.py --verbose
```

Shows compilation status for ALL test cases, not just failures.

## Output Example

```
================================================================================
Validating: benchmarks/test_cases/generated/quarkus.yaml
================================================================================

✓ jms-to-reactive-quarkus-00000 - tc001: Compiles successfully
✗ jms-to-reactive-quarkus-00010 - tc001: COMPILATION FAILED
✓ jms-to-reactive-quarkus-00020 - tc001: Compiles successfully
...

--------------------------------------------------------------------------------
Summary for quarkus.yaml:
  Total: 150
  Passed: 120 (80.0%)
  Failed: 30 (20.0%)
--------------------------------------------------------------------------------

================================================================================
OVERALL SUMMARY
================================================================================

Files Validated: 1
Total Test Cases: 150
Passed: 120 (80.0%)
Failed: 30 (20.0%)

================================================================================
DETAILED FAILURES
================================================================================

1. jms-to-reactive-quarkus-00010 - tc001
   File: benchmarks/test_cases/generated/quarkus.yaml
   Context: @MessageDriven - EJBs are not supported in Quarkus

   Compilation Error:
   ----------------------------------------------------------------------------
   error: reference to Message is ambiguous
     both interface javax.jms.Message and interface
     org.eclipse.microprofile.reactive.messaging.Message match
   ----------------------------------------------------------------------------

   Expected Fix Code:
   ----------------------------------------------------------------------------
   import jakarta.enterprise.context.ApplicationScoped;
   import org.eclipse.microprofile.reactive.messaging.Incoming;
   import org.eclipse.microprofile.reactive.messaging.Message;

   @ApplicationScoped
   public class ExampleMessageBean {
       @Incoming("my-queue")
       public void onMessage(Message<String> message) {
           ...
       }
   }
   ----------------------------------------------------------------------------
```

## Common Failure Reasons

### 1. Missing Stub Classes

**Error**: `cannot find symbol: class Employee`

**Cause**: The expected_fix references domain classes that aren't in the stub library.

**Solutions**:
- Add the class to `evaluators/stubs/src/` and rebuild stubs.jar
- Simplify the expected_fix to use generic types
- Mark as `language: xml` if it's not Java code

### 2. Ambiguous Imports

**Error**: `reference to Message is ambiguous`

**Cause**: Multiple classes with the same name imported (e.g., `javax.jms.Message` and `org.eclipse.microprofile.reactive.messaging.Message`).

**Solution**: Use fully qualified names or remove conflicting imports.

### 3. Non-Java Code

**Error**: Various compilation errors

**Cause**: The test case contains XML, YAML, or configuration files that shouldn't be compiled.

**Solution**: Set `language: xml` or appropriate language in the test case metadata.

### 4. API Mismatches

**Error**: `method X in class Y cannot be applied to given types`

**Cause**: The expected_fix uses APIs that don't match the JARs in the classpath.

**Solution**: Verify the API usage matches the dependency versions in `evaluators/stubs/pom.xml`.

## Integration with CI/CD

Add to your CI pipeline to catch test case issues early:

```bash
# Validate all expected fixes
python scripts/validate_expected_fixes.py || exit 1
```

## Limitations

1. **Only validates Java code**: Non-Java test cases (XML, YAML, etc.) will fail compilation but that's expected
2. **Requires stubs**: Classes referenced must exist in `evaluators/stubs/lib/*.jar` or `stubs.jar`
3. **No runtime validation**: Only checks compilation, not runtime correctness

## Fixing Failed Test Cases

When the script reports failures:

1. **Review the compilation error** - What's missing or incorrect?
2. **Check the expected_fix code** - Does it match Quarkus best practices?
3. **Verify imports** - Are all necessary imports present?
4. **Test manually** - Try compiling the code yourself with javac
5. **Update the test case** - Fix the expected_fix in the YAML file
6. **Re-run validation** - Verify the fix compiles

## Example: Fixing an Ambiguous Import

**Before (fails):**
```yaml
expected_fix: |
  import org.eclipse.microprofile.reactive.messaging.Incoming;
  import org.eclipse.microprofile.reactive.messaging.Message;

  public class ExampleBean {
      @Incoming("queue")
      public void onMessage(Message<String> message) {
          ...
      }
  }
```

**After (compiles):**
```yaml
expected_fix: |
  import org.eclipse.microprofile.reactive.messaging.Incoming;

  public class ExampleBean {
      @Incoming("queue")
      public void onMessage(String message) {
          ...
      }
  }
```

Or use fully qualified name:
```yaml
expected_fix: |
  import org.eclipse.microprofile.reactive.messaging.Incoming;

  public class ExampleBean {
      @Incoming("queue")
      public void onMessage(org.eclipse.microprofile.reactive.messaging.Message<String> message) {
          ...
      }
  }
```
