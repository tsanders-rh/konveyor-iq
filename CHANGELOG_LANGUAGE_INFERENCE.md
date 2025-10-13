# Language Inference Feature

## Summary

Implemented automatic language detection in test case generation to prevent XML/YAML/properties files from being incorrectly marked as Java, which was causing false compilation failures.

## Problem

The automated fix script (`fix_expected_fixes.py`) had a low success rate (18%):
- Total compilation failures: 152
- Fixes applied: 28
- Fixes failed: 124

**Root cause:** 5 test cases containing XML (pom.xml) were incorrectly marked as `language: java`, causing compilation attempts to fail with "Could not extract class name from code" errors.

## Solution

### 1. Added Language Support to Schema

**File:** `benchmarks/schema.py`

Added new language types:
```python
class Language(str, Enum):
    JAVA = "java"
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    GO = "go"
    XML = "xml"           # NEW
    YAML = "yaml"         # NEW
    PROPERTIES = "properties"  # NEW
```

### 2. Implemented Language Inference

**File:** `scripts/generate_tests.py`

Added `_infer_language_from_rule()` method that inspects Konveyor rule `when` conditions:

```python
def _infer_language_from_rule(self, rule: Dict[str, Any]) -> str:
    """Infer the programming language from the rule's 'when' condition."""
    # Checks for:
    # - builtin.xml → 'xml'
    # - builtin.yaml/yml → 'yaml'
    # - builtin.properties → 'properties'
    # - builtin.json → 'json'
    # - java.referenced/dependency/typeusage → 'java'
    # - Default → 'java'
```

**Detection logic:**
- Recursively searches `when` conditions for language-specific analyzers
- Correctly handles nested conditions (`or`, `and`, `from`)
- Falls back to `java` if no specific language detected

### 3. Updated Validation and Fix Scripts

**Files:**
- `scripts/validate_expected_fixes.py`
- `scripts/fix_expected_fixes.py`

Both scripts now skip non-Java test cases during compilation validation:

```python
# Skip non-Java test cases
if test_case.language.value != "java":
    if self.verbose:
        print(f"⊘ {rule.rule_id} - {test_case.id}: Non-Java test case (language: {test_case.language.value}, skipped)")
    continue
```

### 4. Fixed Existing Test Cases

**Script:** `scripts/fix_xml_languages.sh`

Corrected 5 POM rules from `language: java` → `language: xml`:
- `springboot-parent-pom-to-quarkus-00000`
- `javaee-pom-to-quarkus-00000`
- `javaee-pom-to-quarkus-00010`
- `javaee-pom-to-quarkus-00030`
- `javaee-pom-to-quarkus-00050`

### 5. Added Quarkus Security Dependencies

**File:** `evaluators/stubs/pom.xml`

Added missing security JARs:
```xml
<dependency>
    <groupId>io.quarkus</groupId>
    <artifactId>quarkus-security</artifactId>
</dependency>
<dependency>
    <groupId>io.quarkus</groupId>
    <artifactId>quarkus-elytron-security-properties-file</artifactId>
</dependency>
```

Provides:
- `InMemorySecurityRealm.Builder`
- `BcryptUtil.bcryptHash()`
- `SecurityDomain.builder()`

## Results

**Before fixes:**
- Total test cases: 234
- Failed: 152 (64.9%)

**After fixes:**
- Total test cases: 234
- **Passed: 110 (47.0%)**
- **Failed: 119 (50.9%)**
- **Skipped: 5 (2.1% - XML test cases)**

**Improvement:**
- 33 fewer failures (22% reduction)
- XML test cases no longer cause false failures
- Future test generation will automatically use correct language

## Remaining Issues

Most remaining failures (90+) are from Hibernate Search internal APIs that aren't meant to be public. These may need to be:
1. Marked as non-compilable test cases
2. Updated to use public APIs only
3. Excluded from compilation validation

## Verification

Tested language inference on actual Konveyor rules:
```
✓ XML Rule - springboot-parent-pom-to-quarkus-00000: xml
✓ Java Rule - ee-to-quarkus-00000: java
✓ Java Rule - ee-to-quarkus-00010: java
```

## Documentation Updates

Updated:
- `docs/generating_tests.md` - Added "Automatic Language Detection" section
- `README.md` - Added language detection to "Generated Templates" features

## No Changes Needed to Konveyor Rules

The Konveyor rules are **already correct** - they use `builtin.xml` for XML files. The bug was in our generation script hardcoding `language: 'java'`. Future generations will automatically detect the correct language.
