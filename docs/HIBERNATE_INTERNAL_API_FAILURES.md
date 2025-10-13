# Hibernate Internal API Failures - Examples

## Overview

These test cases reference Hibernate internal implementation classes that are not part of the public API or are missing from our compilation classpath.

---

## Example 1: hibernate-6.2-00010 - Internal EntityPersister API

**Rule:** EntityPersister#multiload method has changed
**Issue:** References internal Hibernate ORM classes that aren't in public API

### Expected Fix Code (from test case):
```java
import org.hibernate.engine.spi.SharedSessionContractImplementor;
import org.hibernate.engine.spi.SessionImplementor;
import org.hibernate.event.spi.EventSource;
import org.hibernate.loader.entity.EntityPersister;  // ❌ Internal API
import org.hibernate.loader.entity.MultiIdLoadOptions;  // ❌ Internal API

public class HibernateMultiLoadExample {
    public void loadEntities(SharedSessionContractImplementor session,
                            EntityPersister persister) {
        Object[] ids = new Object[] {1, 2, 3};
        MultiIdLoadOptions options = new MultiIdLoadOptions();

        // Fixed code
        if (session.isEventSource()) {
            EventSource eventSourceSession = session.asEventSource();
            persister.lock(ids, eventSourceSession, options);  // ❌ Method doesn't exist
        }
    }
}
```

### Compilation Error:
```
error: cannot find symbol
    persister.lock(ids, eventSourceSession, options);
             ^
  symbol:   method lock(Object[],EventSource,MultiIdLoadOptions)
  location: variable persister of type EntityPersister
```

### Why It Fails:
1. **`EntityPersister`** is in `org.hibernate.loader.entity` package - this is an **internal implementation package**
2. The `lock()` method with this specific signature doesn't exist in the public API
3. These are low-level Hibernate internals not meant for direct application use

### What This Rule Is For:
This is an **EAP7 → EAP8 migration rule** for code that's using Hibernate internal APIs directly. Most applications don't do this - it's typically only framework/library code.

---

## Example 2: hibernate-search-00010 - Missing Hibernate Search JARs

**Rule:** Constants for Hibernate Search configuration property keys have changed
**Issue:** Hibernate Search JARs not in our classpath

### Expected Fix Code:
```java
import org.hibernate.search.mapper.orm.cfg.HibernateOrmMapperSettings;  // ❌ Not in classpath
import javax.persistence.EntityManager;
import javax.persistence.PersistenceContext;

public class SearchConfigurationExample {
    @PersistenceContext
    private EntityManager entityManager;

    public void configureSearch() {
        entityManager.getEntityManagerFactory()
            .getProperties()
            .put(HibernateOrmMapperSettings.MAPPING_CONFIGURER,  // ❌ Class not found
                 new CustomSearchMapping());
    }
}
```

### Compilation Error:
```
error: cannot find symbol
    ...put(HibernateOrmMapperSettings.MAPPING_CONFIGURER, ...);
                                     ^
  symbol:   variable MAPPING_CONFIGURER
  location: class HibernateOrmMapperSettings
```

### Why It Fails:
1. **Hibernate Search is not in our classpath** - we only have hibernate-core
2. We'd need to add `hibernate-search-mapper-orm` JAR
3. But Hibernate Search has 50+ classes and many are also internal APIs

---

## Example 3: hibernate-search-00020 - Complex API Migration

**Rule:** Property hibernate.search.analyzer not available anymore
**Issue:** Multiple missing annotation classes

### Expected Fix Code:
```java
import org.hibernate.search.mapper.pojo.mapping.definition.annotation.FullTextField;
import org.hibernate.search.mapper.pojo.mapping.definition.annotation.Indexed;
import org.hibernate.search.mapper.pojo.mapping.definition.annotation.KeywordField;
import org.hibernate.search.mapper.pojo.bridge.mapping.annotation.IdentifierBridgeRef;
import org.hibernate.search.engine.backend.types.Projectable;
import org.hibernate.search.engine.backend.types.Sortable;

@Entity
@Indexed  // ❌ Wrong import - needs Hibernate Search version
public class Book {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @KeywordField(name = "id",
                  sortable = Sortable.YES,  // ❌ Enum not found
                  projectable = Projectable.YES,  // ❌ Enum not found
                  identifierBridge = @IdentifierBridgeRef(type = Long.class))
    private Long id;

    @FullTextField(analyzer = "default")
    private String title;
}
```

### Compilation Error:
```
error: incompatible types: Indexed cannot be converted to Annotation
@Indexed
 ^
error: cannot find symbol
    sortable = Sortable.YES, projectable = Projectable.YES
                       ^
  symbol:   variable YES
  location: class Sortable
```

### Why It Fails:
1. Hibernate Search 6.x annotations conflict with javax.persistence annotations
2. Missing Hibernate Search backend types (Sortable, Projectable enums)
3. Complex migration requiring full Hibernate Search stack

---

## Root Causes Summary

### 1. Internal Implementation APIs (hibernate-6.2-*)
- Rules reference `org.hibernate.loader.entity.EntityPersister` and similar internal classes
- These are **intentionally not public API** - shouldn't be used in application code
- Methods like `lock(Object[], EventSource, MultiIdLoadOptions)` don't exist in current version
- **These are advanced/low-level APIs** for Hibernate framework developers, not typical users

### 2. Missing Hibernate Search Dependencies (hibernate-search-*)
- We have `hibernate-core` but not `hibernate-search-mapper-orm`
- Hibernate Search is a separate module with 50+ JARs
- Even if we add it, many classes are also internal implementation details

### 3. Auto-Generated Code Issues
- LLM-generated expected_fix code uses internal APIs because:
  - Konveyor rules document internal API changes (for completeness)
  - LLM doesn't know which APIs are public vs internal
  - Training data includes internal Hibernate code examples

---

## Recommended Solutions

### Option 1: Mark as Non-Compilable
Add metadata to skip compilation validation:

```yaml
- rule_id: hibernate-6.2-00010
  test_cases:
  - id: tc001
    language: java
    compilable: false  # NEW: Skip compilation validation
    reason: "Uses Hibernate internal APIs not meant for application code"
```

### Option 2: Add Missing Dependencies
For Hibernate Search rules, add to `pom.xml`:

```xml
<dependency>
    <groupId>org.hibernate.search</groupId>
    <artifactId>hibernate-search-mapper-orm</artifactId>
    <version>6.2.0.Final</version>
    <scope>provided</scope>
</dependency>
```

**But:** Still won't solve internal API issues.

### Option 3: Rewrite Test Cases to Use Public APIs
Update expected_fix to use only public Hibernate APIs:

```java
// Instead of internal EntityPersister API:
// Use public JPA/Hibernate APIs like EntityManager, Session, etc.
EntityManager em = ...;
List<MyEntity> entities = em.createQuery(
    "SELECT e FROM MyEntity e WHERE e.id IN :ids", MyEntity.class)
    .setParameter("ids", Arrays.asList(1, 2, 3))
    .getResultList();
```

### Option 4: Exclude from Evaluation
Don't evaluate these advanced migration rules - they're for specialized cases:

```python
# In evaluate.py - skip rules with internal APIs
EXCLUDED_RULES = [
    'hibernate-6.2-*',      # Internal Hibernate APIs
    'hibernate-search-*',   # Missing dependencies + internal APIs
]
```

---

## Statistics

From validation results:
- **Total Hibernate failures: ~95**
  - hibernate-6.2-*: 3 rules (internal APIs)
  - hibernate-search-*: 92 rules (missing deps + some internal APIs)

These represent **40% of all remaining failures** (95 out of 119).

---

## Recommendation

**Short term:** Mark these test cases with `compilable: false` to skip validation
**Long term:** Update test case generation to detect internal API usage and either:
1. Generate public API alternatives
2. Auto-mark as non-compilable with explanation
3. Exclude internal API rules from auto-generation
