# Migration Plan: From Stubs to Real JARs

## The Problem with Stubs

**Current approach:**
- Manually create stub files for every class/interface/annotation
- Guess whether something is a class, interface, or annotation
- No method signatures, return types, or parameter info
- Maintenance burden scales with test suite size

**Pain points:**
- ❌ `@ConfigProperties` was created as a class instead of annotation
- ❌ Need to manually fix each mistake
- ❌ Doesn't scale to thousands of test cases
- ❌ Stubs don't reflect actual APIs (missing methods, wrong signatures)

## The Better Solution: Real JARs

Use actual Maven dependencies for compilation. This is how production projects work.

### Benefits

✅ **Automatic**: No manual stub creation
✅ **Accurate**: Real method signatures, annotations, generics
✅ **Complete**: All classes/interfaces/annotations included
✅ **Maintainable**: Just update version numbers
✅ **Scalable**: Works for any number of test cases

### Implementation

#### Step 1: Create Maven POM for Dependencies

Create `evaluators/stubs/pom.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0
         http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>

    <groupId>org.konveyor.evaluation</groupId>
    <artifactId>test-dependencies</artifactId>
    <version>1.0.0</version>
    <packaging>pom</packaging>

    <name>Konveyor Evaluation - Test Dependencies</name>
    <description>Compile-time dependencies for test case evaluation</description>

    <properties>
        <maven.compiler.source>11</maven.compiler.source>
        <maven.compiler.target>11</maven.compiler.target>
        <quarkus.version>3.6.0</quarkus.version>
        <jakarta.version>10.0.0</jakarta.version>
        <microprofile.version>6.0</microprofile.version>
    </properties>

    <dependencies>
        <!-- Jakarta EE APIs -->
        <dependency>
            <groupId>jakarta.platform</groupId>
            <artifactId>jakarta.jakartaee-api</artifactId>
            <version>${jakarta.version}</version>
            <scope>provided</scope>
        </dependency>

        <!-- MicroProfile APIs -->
        <dependency>
            <groupId>org.eclipse.microprofile</groupId>
            <artifactId>microprofile</artifactId>
            <version>${microprofile.version}</version>
            <type>pom</type>
            <scope>provided</scope>
        </dependency>

        <!-- Quarkus Core -->
        <dependency>
            <groupId>io.quarkus</groupId>
            <artifactId>quarkus-arc</artifactId>
            <version>${quarkus.version}</version>
            <scope>provided</scope>
        </dependency>

        <!-- Quarkus Config -->
        <dependency>
            <groupId>io.quarkus</groupId>
            <artifactId>quarkus-config-yaml</artifactId>
            <version>${quarkus.version}</version>
            <scope>provided</scope>
        </dependency>

        <!-- Legacy javax for migration testing -->
        <dependency>
            <groupId>javax.enterprise</groupId>
            <artifactId>cdi-api</artifactId>
            <version>2.0</version>
            <scope>provided</scope>
        </dependency>

        <dependency>
            <groupId>javax.ejb</groupId>
            <artifactId>javax.ejb-api</artifactId>
            <version>3.2</version>
            <scope>provided</scope>
        </dependency>
    </dependencies>

    <build>
        <plugins>
            <!-- Download all dependencies to lib/ directory -->
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-dependency-plugin</artifactId>
                <version>3.6.0</version>
                <executions>
                    <execution>
                        <id>copy-dependencies</id>
                        <phase>package</phase>
                        <goals>
                            <goal>copy-dependencies</goal>
                        </goals>
                        <configuration>
                            <outputDirectory>${project.basedir}/lib</outputDirectory>
                            <includeScope>provided</includeScope>
                        </configuration>
                    </execution>
                </executions>
            </plugin>
        </plugins>
    </build>
</project>
```

#### Step 2: Download Dependencies

```bash
cd evaluators/stubs
mvn clean package

# This downloads all JARs to evaluators/stubs/lib/
```

#### Step 3: Update Compilation to Use Real JARs

Modify `evaluators/functional.py`:

```python
def _compile_java(self, code: str) -> tuple[bool, str]:
    """Compile Java code."""
    # ... existing code ...

    # Build classpath from lib directory
    lib_dir = Path(__file__).parent / "stubs" / "lib"
    if lib_dir.exists():
        jar_files = list(lib_dir.glob("*.jar"))
        if jar_files:
            classpath = ":".join(str(jar) for jar in jar_files)
            javac_cmd = ["javac", "-cp", classpath, str(java_file)]
    else:
        # Fallback to stubs.jar
        stub_jar = Path(__file__).parent / "stubs" / "stubs.jar"
        if stub_jar.exists():
            javac_cmd = ["javac", "-cp", str(stub_jar), str(java_file)]
        else:
            javac_cmd = ["javac", str(java_file)]

    # ... rest of compilation logic ...
```

#### Step 4: Gitignore the lib Directory

Add to `.gitignore`:
```
evaluators/stubs/lib/
evaluators/stubs/target/
```

We don't commit the JARs - just download them when needed.

### Migration Steps

1. **Create the POM file** (see Step 1 above)
2. **Run Maven** to download JARs: `cd evaluators/stubs && mvn clean package`
3. **Update Python code** to use lib/*.jar instead of stubs.jar
4. **Test** with existing test cases
5. **Deprecate stub generation** - no longer needed!

### Keeping Stubs for Edge Cases

We can keep a minimal `stubs.jar` for:
- Custom test classes (Order, User, Database, etc.)
- Mock/stub classes that don't exist in real projects
- Edge cases not covered by Maven Central

But 95% of imports will come from real JARs.

## Comparison

| Aspect | Current (Stubs) | Proposed (Real JARs) |
|--------|----------------|---------------------|
| Accuracy | ❌ Guessed types | ✅ Actual APIs |
| Completeness | ❌ Only what we add | ✅ All classes |
| Maintenance | ❌ Manual per import | ✅ Version bumps only |
| Scalability | ❌ Doesn't scale | ✅ Unlimited test cases |
| Annotation detection | ❌ Heuristics fail | ✅ Always correct |
| Method signatures | ❌ Missing/wrong | ✅ Exact match |
| Setup time | ✅ Quick (pre-built) | ⚠️ Initial Maven run |
| Disk space | ✅ 200KB | ⚠️ ~50MB (one-time) |

## Recommendation

**Switch to real JARs.** The initial setup is worth it because:
1. Eliminates the "class vs annotation" problem forever
2. Scales to any test suite size
3. Matches real-world compilation behavior
4. Industry standard approach

The 50MB of JARs is negligible compared to the maintenance burden of managing stubs.

## Hybrid Approach (Recommended)

Best of both worlds:

1. **Real JARs** for all framework/library code (Quarkus, Jakarta, MicroProfile)
2. **Small stubs.jar** for test-specific classes (Database, Order, User)

This gives us:
- ✅ Accurate compilation for framework code
- ✅ Lightweight custom test fixtures
- ✅ No dependency on external repositories during testing (JARs cached locally)

## Next Steps

1. Create `evaluators/stubs/pom.xml` (provided above)
2. Run `mvn package` to download dependencies
3. Update `evaluators/functional.py` to use lib/*.jar
4. Test with current test suite
5. Delete auto-generated stub files (keep only custom ones)

This will solve the scalability problem once and for all.
