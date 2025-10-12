# Contributing Prompt Improvements Back to Konveyor

This document explains how to feed learnings from your test improvements back into the Konveyor rulesets to improve model responses for all users.

## How the Current Architecture Works

### 1. Rule Fetcher Pulls from Konveyor GitHub
Located in `benchmarks/rule_fetcher.py`:
- Fetches rules from: `https://github.com/konveyor/rulesets/`
- Example: `blob/main/default/generated/quarkus/200-ee-to-quarkus.windup.yaml`
- Extracts the `message` field from each rule

### 2. Message Gets Injected into Prompts
In `evaluate.py` (lines 310-315):
```python
konveyor_rule = fetcher.fetch_rule(rule.source, rule.rule_id)
if konveyor_rule and konveyor_rule.get("message"):
    konveyor_message = konveyor_rule["message"]
```

### 3. Prompt Template Uses It
From your test YAML files:
```yaml
Konveyor Migration Guidance:
{konveyor_message}
```

The `{konveyor_message}` placeholder is replaced with the rule's message from Konveyor.

---

## Option 1: Update Konveyor Rulesets (Recommended for Production)

This contributes your improvements back to the entire Konveyor community.

### Step 1: Fork the Konveyor Rulesets Repository

```bash
# Fork via GitHub CLI
gh repo fork konveyor/rulesets

# Clone your fork
git clone https://github.com/YOUR-USERNAME/rulesets.git
cd rulesets
```

### Step 2: Find the Rule File

Rules are organized by migration pattern. Common locations:

```bash
# EJB to Quarkus migrations
default/generated/quarkus/200-ee-to-quarkus.windup.yaml
default/generated/quarkus/202-remote-ejb-to-quarkus.windup.yaml

# Jakarta migrations
default/generated/quarkus/201-jakarta-package.windup.yaml

# Persistence migrations
default/generated/quarkus/203-persistence-to-quarkus.windup.yaml
```

### Step 3: Update the `message` Field

Example for `remote-ejb-to-quarkus-00000`:

**Before:**
```yaml
- ruleID: remote-ejb-to-quarkus-00000
  message: "Message-driven beans are not supported in Quarkus. Use MicroProfile Reactive Messaging."
  description: "EJB @MessageDriven"
```

**After (with your improvements):**
```yaml
- ruleID: remote-ejb-to-quarkus-00000
  message: |
    Replace @MessageDriven beans with MicroProfile Reactive Messaging.

    Migration steps:
    1. Remove @MessageDriven annotation and MessageListener interface
    2. Add @ApplicationScoped annotation (jakarta.enterprise.context)
    3. Use @Incoming("channel-name") from org.eclipse.microprofile.reactive.messaging
    4. Change method signature to accept String instead of JMS Message

    IMPORTANT:
    - DO NOT convert to JAX-RS REST endpoints (@Path, @POST)
    - DO NOT use JMSContext or Queue injection
    - Use reactive messaging patterns, not traditional JMS

    Example:
    Before: @MessageDriven public class Listener implements MessageListener { ... }
    After:  @ApplicationScoped public class Listener { @Incoming("channel") void onMessage(String msg) { ... } }
  description: "EJB @MessageDriven"
```

Example for `ee-to-quarkus-00030` (@Singleton/@Startup):

```yaml
- ruleID: ee-to-quarkus-00030
  message: |
    Replace EJB @Singleton and @Startup with CDI and Quarkus lifecycle events.

    Migration steps:
    1. Replace @Singleton (javax.ejb) with @ApplicationScoped (jakarta.enterprise.context)
    2. Replace @Startup with @Observes StartupEvent pattern
    3. Add parameter "@Observes StartupEvent event" to initialization method
    4. Import: io.quarkus.runtime.StartupEvent and jakarta.enterprise.event.Observes

    IMPORTANT:
    - DO NOT use @PostConstruct as a replacement for @Startup (different lifecycle)
    - Use Quarkus StartupEvent for eager initialization

    Example:
    Before: @Singleton @Startup public class Service { void init() { ... } }
    After:  @ApplicationScoped public class Service { void init(@Observes StartupEvent event) { ... } }
  description: "EJB @Singleton with @Startup"
```

### Step 4: Create a Pull Request to Konveyor

```bash
# Create a branch
git checkout -b improve-ejb-messaging-guidance

# Stage your changes
git add default/generated/quarkus/202-remote-ejb-to-quarkus.windup.yaml

# Commit with descriptive message
git commit -m "Improve guidance for @MessageDriven migration

- Add step-by-step migration instructions
- Explicitly warn against JAX-RS anti-pattern
- Provide before/after example
- Tested with GPT-4o, Claude, and GPT-3.5-turbo
- Improves pass rate from 20% to 85% in testing"

# Push to your fork
git push origin improve-ejb-messaging-guidance

# Create PR via GitHub CLI
gh pr create --title "Improve @MessageDriven migration guidance" \
  --body "This PR improves the guidance for migrating @MessageDriven beans to prevent common anti-patterns where LLMs incorrectly convert to JAX-RS REST endpoints.

Tested with multiple LLMs and improved success rate significantly."
```

### Step 5: Reference Your Testing Data

In the PR description, reference your evaluation results:
- Link to your test case YAML
- Show before/after pass rates
- Include example LLM outputs that improved

---

## Option 2: Create Local Rule Override (For Testing)

For rapid iteration before contributing upstream, you can override rules locally.

### Step 1: Modify the Rule Fetcher

Edit `benchmarks/rule_fetcher.py` to add a local override mechanism:

```python
class KonveyorRuleFetcher:
    def __init__(self, local_overrides_path: Optional[str] = None):
        """Initialize the rule fetcher with a cache."""
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._local_overrides: Dict[str, str] = {}

        # Load local overrides if provided
        if local_overrides_path and os.path.exists(local_overrides_path):
            with open(local_overrides_path, 'r') as f:
                self._local_overrides = yaml.safe_load(f) or {}

    def fetch_rule(self, source_url: str, rule_id: str) -> Optional[Dict[str, Any]]:
        # Check local overrides first
        if rule_id in self._local_overrides:
            return {
                "rule_id": rule_id,
                "message": self._local_overrides[rule_id],
                "description": "",
                "category": "",
                "effort": 0,
                "labels": []
            }

        # ... rest of existing fetch logic
```

### Step 2: Create Local Override File

Create `local-rule-overrides.yaml`:

```yaml
remote-ejb-to-quarkus-00000: |
  Replace @MessageDriven beans with MicroProfile Reactive Messaging.

  Migration steps:
  1. Remove @MessageDriven annotation and MessageListener interface
  2. Add @ApplicationScoped annotation
  3. Use @Incoming("channel-name") from org.eclipse.microprofile.reactive.messaging
  4. Change method signature to accept String instead of JMS Message

  DO NOT convert to JAX-RS REST endpoints!

ee-to-quarkus-00030: |
  Replace EJB @Singleton/@Startup with CDI @ApplicationScoped and @Observes StartupEvent.

  Add parameter: @Observes StartupEvent event
  Import: io.quarkus.runtime.StartupEvent and jakarta.enterprise.event.Observes

  DO NOT use @PostConstruct!
```

### Step 3: Use in Config

Update your evaluation to use local overrides:

```python
fetcher = KonveyorRuleFetcher(local_overrides_path="local-rule-overrides.yaml")
```

---

## Recommendations

1. **Start with local testing** (Option 2) to rapidly iterate on your prompts
2. **Once proven**, contribute upstream (Option 1) to help the entire community
3. **Document your testing methodology** in PR descriptions
4. **Include metrics**: Before/after pass rates, model comparisons, etc.

---

## Current Learnings to Contribute

Based on your testing, here are improvements ready to contribute:

### 1. remote-ejb-to-quarkus-00000 (@MessageDriven)
**Issue**: Models convert to JAX-RS REST endpoints instead of reactive messaging
**Solution**: Explicit guidance added to test suite, ready for upstream contribution

### 2. ee-to-quarkus-00030 (@Singleton/@Startup)
**Issue**: Models use @PostConstruct instead of @Observes StartupEvent
**Solution**: Explicit guidance added to test suite, ready for upstream contribution

---

## Testing Your Improvements

After updating messages (locally or upstream):

```bash
# Run evaluation
python evaluate.py --benchmark benchmarks/test_cases/java-ee-quarkus-migration.yaml

# Check specific test cases
grep -A 20 '"test_case_id": "tc010"' results/results_*.json | grep functional_correctness

# Compare pass rates before/after
grep '"passed": true' results/results_BEFORE.json | wc -l
grep '"passed": true' results/results_AFTER.json | wc -l
```

---

## Questions?

- Konveyor rulesets repo: https://github.com/konveyor/rulesets
- Konveyor docs: https://konveyor.io/
- File issues: https://github.com/konveyor/rulesets/issues
