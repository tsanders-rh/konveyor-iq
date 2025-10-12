# Konveyor Issue: Incorrect Guidance in jms-to-reactive-quarkus-00020

## Issue Summary

The Konveyor rule `jms-to-reactive-quarkus-00020` contains contradictory migration guidance that causes LLM-based code generation to fail. The rule's `message` field provides incorrect "After" example code that conflicts with the actual correct migration pattern.

## Affected Rule

- **Rule ID**: `jms-to-reactive-quarkus-00020`
- **Description**: "Configure message listener method with @Incoming"
- **Source File**: `rulesets/default/generated/quarkus/218-jms-to-reactive-quarkus.windup.yaml`
- **Severity**: medium
- **Category**: mandatory

## The Problem

### Incorrect Konveyor Guidance (from rule message field)

The rule's guidance message shows this **INCORRECT** "After" example:

```java
After:
 public class MessageListenerImpl implements MessageListener {{
 @Incoming("HELLOWORLDMDBQueue")
 public void onMessage(String message) {{
 // ...handler code
 }
 }
```

**Problem**: The class still `implements MessageListener`, which is incorrect for Quarkus Reactive Messaging.

### Correct Migration Pattern (from expected_fix)

The test case's `expected_fix` shows the **CORRECT** migration:

```java
import org.eclipse.microprofile.reactive.messaging.Incoming;

public class MessageListenerImpl {
    @Incoming("queue/HELLOWORLDMDBQueue")
    public void onMessage(String message) {
        // Message handling logic
        System.out.println("Received message: " + message);
    }
}
```

**Key Difference**: No `implements MessageListener` interface.

## Why This Matters

### The Interface Conflict

When migrating from JMS `@MessageDriven` beans to Quarkus Reactive Messaging:

1. **JMS MessageListener interface** requires:
   ```java
   void onMessage(Message msg)  // jakarta.jms.Message parameter
   ```

2. **Quarkus @Incoming** expects:
   ```java
   void onMessage(String message)  // String or Message<String> parameter
   ```

3. **If you keep `implements MessageListener`**, the Java compiler requires the exact JMS method signature, causing a compilation error:
   ```
   error: MessageListenerImpl is not abstract and does not override
   abstract method onMessage(Message) in MessageListener
   ```

### Impact on LLM-Based Migration Tools

LLMs (GPT-4, Claude, etc.) trained to follow migration guidance will:

1. Read the Konveyor rule's "After" example
2. Generate code that keeps `implements MessageListener`
3. Produce code that **fails to compile**

**Test Results** (from evaluation run 2025-10-12):
- **gpt-4-turbo**: Failed to compile (kept `implements MessageListener`)
- **claude-3-7-sonnet-latest**: Failed to compile (kept `implements MessageListener`)
- **gpt-3.5-turbo**: Failed to compile (kept `implements MessageListener`)

All models followed the incorrect Konveyor guidance over the correct expected_fix.

## Original Code Example

```java
import jakarta.ejb.ActivationConfigProperty;
import jakarta.ejb.MessageDriven;
import jakarta.jms.Message;
import jakarta.jms.MessageListener;

@MessageDriven(name = "HelloWorldQueueMDB", activationConfig = {
    @ActivationConfigProperty(propertyName = "destinationLookup",
                             propertyValue = "queue/HELLOWORLDMDBQueue")
})
public class MessageListenerImpl implements MessageListener {
    public void onMessage(Message msg) {
        // Message handling logic
        System.out.println("Received message: " + msg.toString());
    }
}
```

## Correct Migration (What Rule Should Show)

### Step 1: Remove JMS Annotations and Interfaces

```diff
- import jakarta.ejb.ActivationConfigProperty;
- import jakarta.ejb.MessageDriven;
- import jakarta.jms.Message;
- import jakarta.jms.MessageListener;
+ import org.eclipse.microprofile.reactive.messaging.Incoming;

- @MessageDriven(name = "HelloWorldQueueMDB", activationConfig = {
-     @ActivationConfigProperty(propertyName = "destinationLookup",
-                              propertyValue = "queue/HELLOWORLDMDBQueue")
- })
- public class MessageListenerImpl implements MessageListener {
+ public class MessageListenerImpl {
```

### Step 2: Update Method Signature and Add @Incoming

```diff
-     public void onMessage(Message msg) {
+     @Incoming("queue/HELLOWORLDMDBQueue")
+     public void onMessage(String message) {
          // Message handling logic
-         System.out.println("Received message: " + msg.toString());
+         System.out.println("Received message: " + message);
      }
  }
```

### Complete Corrected Code

```java
import org.eclipse.microprofile.reactive.messaging.Incoming;

public class MessageListenerImpl {
    @Incoming("queue/HELLOWORLDMDBQueue")
    public void onMessage(String message) {
        // Message handling logic
        System.out.println("Received message: " + message);
    }
}
```

**Optional**: If you need access to message metadata, use:
```java
import org.eclipse.microprofile.reactive.messaging.Incoming;
import org.eclipse.microprofile.reactive.messaging.Message;

public class MessageListenerImpl {
    @Incoming("queue/HELLOWORLDMDBQueue")
    public void onMessage(Message<String> message) {
        // Message handling logic
        System.out.println("Received message: " + message.getPayload());
    }
}
```

## Required Changes to Konveyor Rule

The rule's `message` field should be updated to:

### Before (Current - Incorrect):
```yaml
After:
 public class MessageListenerImpl implements MessageListener {{
 @Incoming("HELLOWORLDMDBQueue")
 public void onMessage(String message) {{
 // ...handler code
 }
 }
```

### After (Proposed - Correct):
```yaml
After:
 public class MessageListenerImpl {{
 @Incoming("HELLOWORLDMDBQueue")
 public void onMessage(String message) {{
 // ...handler code
 }
 }
```

**Key Change**: Remove `implements MessageListener` from the "After" example.

## Additional Guidance Needed

The rule message should explicitly state:

1. **REMOVE** the `implements MessageListener` interface
2. **REMOVE** all `jakarta.jms.*` imports
3. **CHANGE** method parameter from `Message msg` to `String message` (or `Message<String> message`)
4. **ADD** `@Incoming` annotation with the channel/queue name
5. **IMPORT** `org.eclipse.microprofile.reactive.messaging.Incoming`

## Compilation Errors Caused

When following the current (incorrect) guidance, developers/tools get:

```
error: MessageListenerImpl is not abstract and does not override
abstract method onMessage(Message) in MessageListener
public class MessageListenerImpl implements MessageListener {
       ^
```

Or if both interfaces are imported:

```
error: reference to MessageListener is ambiguous
public class MessageListenerImpl implements MessageListener {
                                            ^
  both interface javax.jms.MessageListener in javax.jms and
  interface jakarta.jms.MessageListener in jakarta.jms match
```

## Recommendations

1. **Update the rule message** in `218-jms-to-reactive-quarkus.windup.yaml` to remove `implements MessageListener` from the "After" example
2. **Add explicit guidance** to remove the JMS interfaces and imports
3. **Review related rules** (`jms-to-reactive-quarkus-00010`, `jms-to-reactive-quarkus-00000`) for similar issues
4. **Add validation** to ensure rule guidance examples compile successfully

## References

- **Quarkus Reactive Messaging Guide**: https://quarkus.io/guides/reactive-messaging
- **MicroProfile Reactive Messaging Spec**: https://download.eclipse.org/microprofile/microprofile-reactive-messaging-3.0/microprofile-reactive-messaging-spec-3.0.html
- **Test Case Source**: `benchmarks/test_cases/generated/quarkus.yaml` (rule: jms-to-reactive-quarkus-00020)

## Contact

This issue was identified during automated LLM-based code migration evaluation using the Konveyor AI Evaluation Framework.

**Reported by**: [Your Name/Team]
**Date**: 2025-10-12
**Environment**: Quarkus 3.6.0, Jakarta EE 10, MicroProfile Reactive Messaging 3.0
