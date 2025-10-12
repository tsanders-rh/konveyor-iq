# Evaluation Stubs and Dependencies

This directory contains dependencies for compiling Java test cases during evaluation.

## Architecture: Hybrid Approach

We use **real JARs from Maven Central** combined with **custom lightweight stubs**:

### ✅ Real JAR Dependencies (lib/)
Maven downloads actual framework JARs:
- **Jakarta EE APIs** (jakarta.*)
- **MicroProfile APIs** (org.eclipse.microprofile.*)
- **Quarkus libraries** (io.quarkus.*)
- **Legacy javax APIs** (javax.ejb, javax.jms, etc.)

**78 JARs, ~25MB total** (downloaded once, gitignored)

### ✅ Custom Stubs (src/ → stubs.jar)
Lightweight stubs for test-specific classes:
- Common domain objects (Order, User, Database, etc.)
- Simple POJOs used across test cases

**~200KB** (committed to git)

## Why This Approach?

| Previous (Pure Stubs) | Current (Hybrid) |
|----------------------|------------------|
| ❌ Guessed class vs annotation | ✅ Always correct |
| ❌ Missing method signatures | ✅ Exact API match |
| ❌ Manual work per import | ✅ Auto-updated |
| ❌ Doesn't scale | ✅ Unlimited tests |

**Example problem solved:** `@ConfigProperties` was incorrectly created as a class instead of annotation. With real JARs, this never happens.

## Setup

### First-Time Setup

Download real dependencies (one-time, ~1 minute):

```bash
cd evaluators/stubs
mvn clean package
```

This downloads 78 JARs to `lib/` directory.

### Updating Framework Versions

Edit `pom.xml`:

```xml
<properties>
    <quarkus.version>3.8.0</quarkus.version>  <!-- Change this -->
    <jakarta.version>10.0.0</jakarta.version>
</properties>
```

Then re-download:

```bash
mvn clean package
```

### Adding Custom Test Stubs

For domain objects used in tests:

```bash
# Example: Add Product stub
cat > src/common/Product.java <<EOF
package common;

public class Product {
    private Long id;
    private String name;

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    public String getName() { return name; }
    public void setName(String name) { this.name = name; }
}
EOF

# Rebuild stubs.jar
./build.sh
```

## How Compilation Works

The evaluator builds classpath from **both** sources:

```bash
# Automatic classpath (in functional.py):
javac -cp "lib/*:stubs.jar" TestCase.java
```

1. **Real JARs** provide framework classes (Jakarta, Quarkus, MicroProfile)
2. **stubs.jar** provides test-specific classes (Order, User, Database)

Result: Perfect compilation with zero maintenance.

## Structure

```
evaluators/stubs/
├── pom.xml              # Maven dependencies
├── build.sh             # Rebuild stubs.jar
├── lib/                 # Downloaded JARs (gitignored, 25MB)
│   ├── jakarta.jakartaee-api-10.0.0.jar
│   ├── quarkus-arc-3.6.0.jar
│   ├── microprofile-config-api-3.0.2.jar
│   └── ... (78 total)
├── src/                 # Custom stub sources
│   └── common/          # Test domain objects
│       ├── Database.java
│       ├── User.java
│       ├── Order.java
│       └── ...
├── stubs.jar            # Compiled stubs (committed, 200KB)
└── README.md            # This file
```

## When to Add Each

### Add to pom.xml (Real JARs)
✅ Framework/library code (Jakarta, Quarkus, MicroProfile)
✅ Published artifacts on Maven Central
✅ Any javax.* or jakarta.* package

### Add to src/ (Custom Stubs)
✅ Test-specific domain objects
✅ Simple POJOs used across tests
✅ Classes that don't exist in real projects

## Troubleshooting

### "cannot find symbol" errors

**Check if it's a framework class:**
```bash
# Search in real JARs
find lib -name "*.jar" -exec jar tf {} \; | grep ClassName
```

If found: Re-run `mvn package` to ensure lib/ is populated.

If not found: Add to pom.xml or create custom stub.

### Maven download fails

**Network issues:**
```bash
# Try with explicit Maven repository
mvn clean package -U
```

**Missing artifact:**
Update version in `pom.xml` or check Maven Central.

## CI/CD Integration

```bash
# One-time setup in CI
cd evaluators/stubs && mvn clean package

# Run evaluation (reuses downloaded JARs)
cd ../.. && python evaluate.py --benchmark ...
```

## Benefits Summary

✅ **No guessing**: Annotations, interfaces, classes always correct
✅ **Complete APIs**: All methods, generics, return types exact
✅ **Scalable**: Works for any number of test cases
✅ **Maintainable**: Version bumps instead of manual stub creation
✅ **Accurate**: Matches production compilation behavior

## Migration Notes

Old pure-stub approach is deprecated. See `MIGRATION_TO_REAL_JARS.md` for migration guide.

The hybrid approach solves the "class vs annotation" problem permanently and scales to thousands of auto-generated test cases.
