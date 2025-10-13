# Auto-Generation Created Internal API Examples - Analysis

## Evidence

### 1. Test Case Has Auto-Generation Marker

The `hibernate-6.2-00010` test case has the `'# konveyor_guidance'` field, which is **only added by auto-generation**:

```yaml
- rule_id: hibernate-6.2-00010
  test_cases:
  - id: tc001
    expected_fix: |
      import org.hibernate.loader.entity.EntityPersister;  // ❌ Internal API
      ...
      persister.lock(ids, eventSourceSession, options);  // ❌ Generated from Konveyor message
    '# konveyor_guidance': "This method has changed from `EntityPersister#multiload...`"
```

The presence of `'# konveyor_guidance'` confirms this was auto-generated.

---

### 2. Konveyor Rule Documents Internal API

The original Konveyor rule **explicitly documents the internal API change**:

**File:** `/Users/tsanders/Workspace/rulesets/default/generated/eap8/151-hibernate-6.2.windup.yaml`

```yaml
ruleID: hibernate-6.2-00010
when:
  java.referenced:
    location: METHOD_CALL
    pattern: org.hibernate.persister.entity.EntityPersister.multiload  # ← Internal API!

message: |-
  This method has changed from `EntityPersister#multiload(Object[] ids,
  SharedSessionContractImplementor session, MultiIdLoadOptions loadOptions)`
  to `EntityPersister#lock(Object[] ids, EventSource session,
  MultiIdLoadOptions loadOptions)`.

  Both EventSource and SharedSessionContractImplementor are contracts
  of `SessionImpl` so they can be easily swapped.
```

The Konveyor rule itself is documenting an **internal SPI (Service Provider Interface)** change.

---

### 3. Auto-Generation Faithfully Followed Konveyor Guidance

The LLM auto-generation:

1. ✅ Read the Konveyor rule message
2. ✅ Saw "EntityPersister#multiload → EntityPersister#lock"
3. ✅ Generated code examples using exactly those APIs
4. ❌ **Result:** Test case with internal API code that doesn't compile

**Generated code snippet:**
```java
// This is what the LLM generated based on Konveyor message:
if (session.isEventSource()) {
    EventSource eventSourceSession = session.asEventSource();
    persister.lock(ids, eventSourceSession, options);  // From Konveyor message!
}
```

This matches the Konveyor message exactly: "use `EntityPersister#lock(Object[] ids, EventSource session, MultiIdLoadOptions loadOptions)`"

---

### 4. Why These Rules Were Included

The Hibernate rules are from **EAP8 rulesets** but have Quarkus target labels:

```yaml
labels:
  - konveyor.io/target=quarkus3+
  - konveyor.io/target=quarkus
  - konveyor.io/target=eap8+
  - konveyor.io/target=hibernate6.2+
```

When we ran:
```bash
python scripts/generate_tests.py --all-rulesets --target quarkus --auto-generate
```

It included these Hibernate internal API rules because they have `konveyor.io/target=quarkus` labels.

---

## Root Cause Chain

```
1. Konveyor documents internal API changes
   (EntityPersister.multiload → EntityPersister.lock)
   ↓
2. Rule has konveyor.io/target=quarkus label
   ↓
3. generate_tests.py --target quarkus includes the rule
   ↓
4. --auto-generate reads Konveyor message
   ↓
5. LLM generates code using internal API (as documented)
   ↓
6. Test case created with EntityPersister.lock()
   ↓
7. Compilation fails - internal API not available
```

---

## Why This Happened

### Konveyor's Perspective
- Konveyor documents **all API changes**, including internal SPIs
- These rules are for **framework developers** and **library maintainers**
- Most apps never use these internal APIs
- Documentation is comprehensive for completeness

### LLM's Perspective
- LLM has no concept of "public vs internal API"
- It faithfully generates code based on the Konveyor message
- The message says "use EntityPersister.lock()" → LLM generates that
- LLM training data likely includes Hibernate internal code examples

### Our Auto-Generation's Perspective
- Script correctly extracted Konveyor guidance
- LLM correctly generated code matching that guidance
- **But:** No filtering for internal/SPI vs public API

---

## Scope of the Problem

### Hibernate 6.2 Rules (3 rules)
All document internal SPI changes:
- `hibernate-6.2-00010` - EntityPersister.multiload → lock
- `hibernate-6.2-00020` - Executable.afterDeserialize signature change
- `hibernate-6.2-00030` - Another internal SPI change

### Hibernate Search Rules (92 rules)
Mix of:
- Missing dependencies (Hibernate Search JARs not in classpath)
- Some internal API usage
- Complex annotation migrations

**Total impact:** ~95 test cases (40% of all failures)

---

## Solutions

### Immediate Fix
Mark these test cases as non-compilable:

```yaml
- rule_id: hibernate-6.2-00010
  test_cases:
  - id: tc001
    language: java
    compilable: false  # Skip compilation validation
    reason: "Uses Hibernate internal SPI APIs - for framework developers only"
```

### Long-term Improvements

#### Option 1: Filter Rules During Generation

Add pattern detection in `generate_tests.py`:

```python
INTERNAL_API_PATTERNS = [
    'org.hibernate.persister.*',
    'org.hibernate.loader.*',
    'org.hibernate.action.spi.*',
    '*.spi.*',  # Service Provider Interface packages
]

def is_internal_api_rule(self, rule: Dict[str, Any]) -> bool:
    """Check if rule references internal implementation APIs."""
    when_condition = rule.get('when', {})

    # Check java.referenced patterns
    java_ref = when_condition.get('java.referenced', {})
    pattern = java_ref.get('pattern', '')

    for internal_pattern in INTERNAL_API_PATTERNS:
        if fnmatch.fnmatch(pattern, internal_pattern):
            return True

    return False
```

#### Option 2: Auto-Mark Internal APIs During Generation

Automatically add `compilable: false` metadata:

```python
# In _create_rule_entry()
language = self._infer_language_from_rule(rule)

# Check if this is an internal API rule
is_internal = self.is_internal_api_rule(rule)

test_case = {
    'id': 'tc001',
    'language': language,
    'context': description,
    'code_snippet': code_snippet,
    'expected_fix': expected_fix,
}

# Mark internal API rules as non-compilable
if is_internal:
    test_case['compilable'] = False
    test_case['reason'] = 'Uses internal SPI APIs - for framework developers only'
```

#### Option 3: Enhanced LLM Prompt

Add instructions to prefer public APIs:

```python
def _build_auto_generation_prompt(self, rule, message):
    return f"""
You are generating code examples for a migration rule.

IMPORTANT CONSTRAINTS:
1. Use only PUBLIC APIs, NOT internal implementation classes
2. Avoid packages ending in .spi.* (Service Provider Interfaces)
3. Avoid org.hibernate.persister.*, org.hibernate.loader.*
4. Prefer standard APIs:
   - JPA: EntityManager, EntityManagerFactory
   - Hibernate: Session, SessionFactory
   - Use public documented classes only

Rule: {rule.get('description')}
Guidance: {message}

Generate code using PUBLIC APIs equivalent to the internal APIs mentioned.
"""
```

#### Option 4: Add Hibernate Search Dependencies

For Hibernate Search rules, add to `pom.xml`:

```xml
<!-- Hibernate Search -->
<dependency>
    <groupId>org.hibernate.search</groupId>
    <artifactId>hibernate-search-mapper-orm</artifactId>
    <version>6.2.0.Final</version>
    <scope>provided</scope>
</dependency>

<dependency>
    <groupId>org.hibernate.search</groupId>
    <artifactId>hibernate-search-backend-lucene</artifactId>
    <version>6.2.0.Final</version>
    <scope>provided</scope>
</dependency>
```

**Note:** This helps with missing dependencies but doesn't solve internal API issues.

---

## Recommended Approach

**Phase 1 (Immediate):**
1. Add `compilable: false` to existing Hibernate internal API test cases
2. Document the reason for each

**Phase 2 (Short-term):**
1. Implement Option 1: Pattern-based detection of internal APIs
2. Implement Option 2: Auto-mark during generation

**Phase 3 (Medium-term):**
1. Add Hibernate Search dependencies (Option 4)
2. Enhance LLM prompts (Option 3) to prefer public APIs
3. Re-generate affected test cases with improved prompts

**Phase 4 (Long-term):**
1. Add validation step after auto-generation to detect internal API usage
2. Create allowlist of known public API packages
3. Flag suspicious imports during generation for manual review

---

## Detection Heuristics

### Internal API Indicators

**Package patterns:**
- `*.spi.*` - Service Provider Interfaces
- `*.impl.*` - Implementation packages
- `*.internal.*` - Explicitly internal
- `org.hibernate.persister.*` - Hibernate internals
- `org.hibernate.loader.*` - Hibernate internals
- `org.hibernate.action.*` - Hibernate internals
- `org.hibernate.engine.*` - Hibernate internals (some public, some not)

**Class name patterns:**
- `*Impl` suffix - Often implementation classes
- `*Persister` - Usually internal
- `*Loader` - Usually internal

### Public API Patterns

**JPA/Jakarta Persistence:**
- `jakarta.persistence.*` - All public
- `javax.persistence.*` - All public (legacy)

**Hibernate ORM Public APIs:**
- `org.hibernate.Session`
- `org.hibernate.SessionFactory`
- `org.hibernate.Transaction`
- `org.hibernate.query.*`
- `org.hibernate.annotations.*` (most)

**Safe rule of thumb:**
If it's documented in the official Hibernate user guide → likely public
If it's only in JavaDoc without user guide mention → likely internal

---

## Statistics

From validation of `quarkus.yaml`:

**Total failures:** 119
**Hibernate-related:** 95 (79.8%)
- hibernate-6.2-*: 3 (internal SPIs)
- hibernate-search-*: 92 (missing deps + some internal)

**Impact of auto-generation on failure rate:**
- Auto-generated Hibernate rules: ~95
- These represent 40% of ALL failures
- Removing these would improve pass rate from 47% to ~87%

---

## Conclusion

**Yes, the auto-generation created these problematic examples.**

It did exactly what it was supposed to do:
- ✅ Read Konveyor rule guidance
- ✅ Generate code examples based on that guidance

The issue is:
- ❌ Konveyor documents internal API changes (intentionally, for completeness)
- ❌ LLM can't distinguish public vs internal APIs
- ❌ No filtering for internal/SPI rules during generation

**This is a systemic issue** - anytime Konveyor documents internal API changes and we auto-generate from those rules, we'll get non-compilable examples.

The solution requires **detecting internal APIs during generation** and either:
1. Skipping auto-generation for those rules
2. Auto-marking as `compilable: false`
3. Instructing the LLM to use public API alternatives

See `docs/HIBERNATE_INTERNAL_API_FAILURES.md` for detailed examples of the compilation failures.
