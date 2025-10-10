# Stub Classes for Compilation

This directory contains stub implementations of Java EE and Jakarta EE APIs used for compilation validation.

## What's Included

### Java EE (javax.*)
- `javax.ejb.Stateless` - EJB stateless annotation
- `javax.ejb.EJB` - EJB injection annotation
- `javax.persistence.PersistenceContext` - JPA persistence context
- `javax.persistence.EntityManager` - JPA entity manager
- `javax.transaction.Transactional` - Transaction annotation

### Jakarta EE (jakarta.*)
- `jakarta.enterprise.context.ApplicationScoped` - CDI scope
- `jakarta.inject.Inject` - CDI injection
- `jakarta.persistence.PersistenceContext` - JPA persistence context
- `jakarta.persistence.EntityManager` - JPA entity manager
- `jakarta.transaction.Transactional` - Transaction annotation

### Common Domain Objects
- `User`, `Order`, `Payment` - Common domain stubs

## Building

```bash
./build.sh
```

This compiles all stub classes and packages them into `stubs.jar`.

## Usage

The functional evaluator automatically uses this JAR when compiling generated code:

```python
# evaluators/functional.py
stub_jar = Path(__file__).parent / "stubs" / "stubs.jar"
javac_cmd = ["javac", "-cp", str(stub_jar), java_file]
```

## Adding New Stubs

1. Create `.java` file in appropriate package directory under `src/`
2. Run `./build.sh` to rebuild the JAR
3. Add to auto-import mapping in `functional.py` if needed

## Auto-Import Feature

The framework automatically injects missing imports for common annotations. See `COMMON_JAVA_IMPORTS` in `evaluators/functional.py`.
