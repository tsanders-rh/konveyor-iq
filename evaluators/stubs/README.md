# Java Stubs for Compilation Testing

This directory contains minimal stub classes for Java compilation testing.

## Purpose

These stubs allow the evaluator to compile Java code snippets without requiring full Java EE or Jakarta EE dependencies. They provide just enough interface/annotation definitions to satisfy the Java compiler.

## Structure

```
stubs/
├── src/                  # Stub source files
│   ├── javax/           # Java EE stubs (javax.*)
│   │   ├── ejb/        # EJB annotations
│   │   ├── enterprise/ # CDI context/inject
│   │   ├── inject/     # DI annotations
│   │   ├── jms/        # JMS messaging
│   │   ├── persistence/# JPA
│   │   └── transaction/# Transactions
│   ├── jakarta/         # Jakarta EE stubs (jakarta.*)
│   │   ├── enterprise/ # CDI context
│   │   ├── inject/     # DI annotations
│   │   ├── persistence/# JPA
│   │   └── transaction/# Transactions
│   ├── org/eclipse/microprofile/# MicroProfile
│   │   └── reactive/messaging/ # Reactive messaging
│   ├── io/quarkus/runtime/     # Quarkus runtime
│   └── common/          # Common utility stubs
├── build.sh             # Build script
└── stubs.jar            # Compiled stub JAR (~18KB)
```

## Building

```bash
./build.sh
```

This compiles all `.java` files in `src/` and packages them into `stubs.jar`.

## Adding New Stubs

1. Create new `.java` files in the appropriate package directory under `src/`
2. Implement minimal interface (empty methods, default values)
3. Run `./build.sh` to rebuild the JAR
4. Add auto-import mapping in `../functional.py` if needed

Example stub:

```java
package javax.enterprise.context;

import java.lang.annotation.*;

@Target({ElementType.TYPE})
@Retention(RetentionPolicy.RUNTIME)
public @interface ApplicationScoped {
}
```

## Current Stubs

### Jakarta EE / CDI
- `@ApplicationScoped` (both javax & jakarta)
- `@SessionScoped` (both javax & jakarta)
- `@RequestScoped` (both javax & jakarta)
- `@Named` (both javax & jakarta)
- `@Inject` (both javax & jakarta)
- `@Produces` (both javax & jakarta)
- `@Observes` (jakarta only)

### Jakarta Persistence / JPA
- `@PersistenceContext` (both javax & jakarta)
- `EntityManager` (both javax & jakarta)

### Jakarta Transactions
- `@Transactional` (both javax & jakarta)

### Java EE / EJB
- `@Stateless`
- `@Stateful`
- `@Singleton`
- `@Startup`
- `@MessageDriven` (with activationConfig support)
- `@EJB`
- `@ActivationConfigProperty`

### JMS (Java Message Service)
- `Message`
- `MessageListener`
- `TextMessage`
- `JMSException`

### MicroProfile Reactive Messaging
- `@Incoming` (org.eclipse.microprofile.reactive.messaging)

### Quarkus Runtime
- `StartupEvent` (io.quarkus.runtime)

### Common Domain Objects
- `Database`
- `User`
- `Order`
- `Payment`
- `UserService`
- `OrderService`

## Auto-Import Support

The framework automatically injects missing imports for common annotations. Mappings are defined in `../functional.py`:

```python
COMMON_IMPORTS = {
    "@ApplicationScoped": ["import javax.enterprise.context.ApplicationScoped;",
                           "import jakarta.enterprise.context.ApplicationScoped;"],
    "@Inject": ["import javax.inject.Inject;",
                "import jakarta.inject.Inject;"],
    # ... more mappings
}
```
