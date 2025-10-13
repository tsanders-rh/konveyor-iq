# Migration Complexity Classification

## Overview

This document explains the migration complexity classification system for evaluating AI-generated code migrations.

## Problem Statement

Not all code migration tasks are equally suitable for AI automation. Some migrations are simple mechanical changes (e.g., namespace updates), while others require architectural redesign (e.g., Spring Security → Quarkus Security).

By classifying migrations by complexity, we can:
- Set appropriate expectations for AI success rates
- Focus automated fixes on suitable tasks
- Identify migrations that need human review
- Report results segmented by difficulty level

## Complexity Levels

### TRIVIAL
**Mechanical find/replace operations**

- Namespace changes (`javax.*` → `jakarta.*`)
- Direct 1:1 annotation swaps
- Import statement updates
- No logic changes required

**Expected AI Success Rate:** 95%+

**Examples:**
```java
// Before: javax.enterprise.context.ApplicationScoped
// After:  jakarta.enterprise.context.ApplicationScoped
```

### LOW
**Straightforward API equivalents**

- `@Stateless` → `@ApplicationScoped`
- `@Autowired` → `@Inject`
- Single-class migrations with clear patterns
- Simple configuration changes

**Expected AI Success Rate:** 80%+

**Examples:**
```java
// Before: @Stateless @EJB
// After:  @ApplicationScoped @Inject
```

### MEDIUM
**Requires understanding context**

- `@MessageDriven` → MicroProfile Reactive Messaging
- Configuration pattern changes
- May need additional dependencies
- Multiple related changes

**Expected AI Success Rate:** 60%+

**Examples:**
- JMS → Reactive Messaging
- Spring Config → MicroProfile Config

### HIGH
**Architectural changes**

- Spring Security → Quarkus Security
- Complex pub/sub patterns
- Requires understanding cross-cutting concerns
- Multiple files may need coordination

**Expected AI Success Rate:** 30-50%

**Recommendation:** AI provides starting point + explanation, human reviews and completes

**Examples:**
- Security configurations
- Transaction boundary redesigns
- Complex messaging patterns

### EXPERT
**Likely requires human judgment**

- Custom security realms
- Performance-critical code
- Distributed systems changes
- Business logic intertwined with framework

**Expected AI Success Rate:** <30%

**Recommendation:** AI generates migration checklist + identifies risks, human performs migration

## Workflow

### Step 1: Classify Rules

Run the classification script to analyze and tag all rules:

```bash
# Dry run to see classifications
python3 scripts/classify_rule_complexity.py benchmarks/test_cases/generated/quarkus.yaml --dry-run

# Apply classifications
python3 scripts/classify_rule_complexity.py benchmarks/test_cases/generated/quarkus.yaml

# Verbose mode for detailed scoring
python3 scripts/classify_rule_complexity.py benchmarks/test_cases/generated/quarkus.yaml --verbose
```

The script analyzes:
- Rule descriptions
- Code patterns
- Import statements
- Annotation complexity
- Security-related keywords

### Step 2: Fix by Complexity Level

Fix compilation errors starting with the easiest categories:

```bash
# Fix only TRIVIAL cases (namespace changes)
python3 scripts/fix_expected_fixes.py \
    --file benchmarks/test_cases/generated/quarkus.yaml \
    --complexity trivial

# Fix TRIVIAL + LOW cases
python3 scripts/fix_expected_fixes.py \
    --file benchmarks/test_cases/generated/quarkus.yaml \
    --complexity trivial,low

# Fix specific complexity level
python3 scripts/fix_expected_fixes.py \
    --file benchmarks/test_cases/generated/quarkus.yaml \
    --complexity medium \
    --verbose
```

### Step 3: Validate Results

Validate that fixes worked:

```bash
python3 scripts/validate_expected_fixes.py benchmarks/test_cases/generated/quarkus.yaml -v
```

### Step 4: Evaluate AI Models

Run evaluation segmented by complexity:

```bash
# Evaluate on TRIVIAL cases only
python3 evaluate.py \
    --test-file benchmarks/test_cases/generated/quarkus.yaml \
    --filter-complexity trivial

# Evaluate on all but EXPERT
python3 evaluate.py \
    --test-file benchmarks/test_cases/generated/quarkus.yaml \
    --exclude-complexity expert
```

## Classification Algorithm

The `classify_rule_complexity.py` script uses pattern matching:

1. **Keyword Analysis**
   - Scans rule description, code snippets, expected fixes
   - Matches against complexity-specific patterns

2. **Import Analysis**
   - Counts `javax.*` vs `jakarta.*` imports
   - Identifies Spring vs Quarkus vs security imports
   - Flags Wildfly/internal frameworks

3. **Annotation Analysis**
   - Counts total annotations
   - Identifies complex annotations (@EnableWebSecurity, @MessageDriven, etc.)

4. **Scoring**
   - Weights patterns by complexity level
   - Returns highest matching complexity

## Reporting

The HTML reporter segments results by complexity:

- **Overall pass rate by complexity level**
- **Detailed breakdown per complexity tier**
- **Model performance across complexity spectrum**

This helps demonstrate:
- AI excels at TRIVIAL/LOW migrations (automation)
- AI provides good starting points for MEDIUM (acceleration)
- AI assists with HIGH/EXPERT (explanation + scaffolding)

## Manual Override

You can manually set complexity in YAML:

```yaml
- rule_id: my-custom-rule
  description: Complex security migration
  migration_complexity: high  # Manual override
  test_cases:
    - ...
```

## Best Practices

1. **Start with TRIVIAL**
   - Fix namespace issues first
   - Establishes baseline AI competency
   - Quick wins

2. **Progress to LOW/MEDIUM**
   - Use rich migration guidance
   - Expect some manual tweaking
   - Good ROI on AI assistance

3. **Handle HIGH/EXPERT Separately**
   - Don't expect full automation
   - Evaluate AI's explanation quality
   - Use AI for scaffolding + risk identification

4. **Report Segmented Results**
   - Don't mix complexity levels
   - Show AI value at each tier
   - Set appropriate expectations

## Schema Reference

```python
class MigrationComplexity(str, Enum):
    TRIVIAL = "trivial"   # Mechanical changes
    LOW = "low"           # API equivalents
    MEDIUM = "medium"     # Context understanding
    HIGH = "high"         # Architectural changes
    EXPERT = "expert"     # Human review needed

class Rule(BaseModel):
    rule_id: str
    description: str
    migration_complexity: Optional[MigrationComplexity]
    test_cases: List[TestCase]
```

## Example Results

### Before Classification
```
Overall Pass Rate: 50% (116/234 failures)
```
**Problem:** Mixed complexity levels obscure AI value

### After Classification
```
TRIVIAL: 95% pass rate (19/20)
LOW:     82% pass rate (41/50)
MEDIUM:  64% pass rate (96/150)
HIGH:    45% pass rate (8/18)
EXPERT:  20% pass rate (1/5)
```
**Insight:** AI excels at mechanical changes, provides good assistance for complex migrations

## Future Enhancements

1. **Auto-complexity from Konveyor metadata**
   - Parse rule severity/category
   - Analyze transformation patterns

2. **Machine learning classification**
   - Train on human-labeled examples
   - More accurate complexity prediction

3. **Complexity-aware prompting**
   - Different prompts per complexity level
   - More guidance for HIGH/EXPERT cases

4. **Human-in-loop workflows**
   - Interactive fixing for HIGH complexity
   - Expert review queues
