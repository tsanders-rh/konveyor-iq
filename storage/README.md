# Konveyor IQ Storage Layer

Relational database storage for tracking evaluation results over time.

## Features

- **Multiple backends**: File (JSON), SQLite, PostgreSQL
- **Historical tracking**: Track model performance trends
- **Analytics queries**: Identify failing rules, detect regressions, compare models
- **Cost tracking**: Monitor spending across evaluations
- **Team collaboration**: Share results via centralized database

## Quick Start

### 1. Install Dependencies

```bash
# Install from this directory
pip install -r requirements.txt

# Or from project root
pip install sqlalchemy
```

### 2. Configure Storage

Edit `config.yaml`:

```yaml
storage:
  type: "sqlite"  # or "file", "postgresql"
  path: "konveyor_iq.db"

reporting:
  write_to_database: true
```

### 3. Initialize Database

```bash
python db_cli.py init --config config.yaml
```

### 4. Query Results

```bash
# Compare models
python db_cli.py query models --days 30

# Find failing rules
python db_cli.py query rules --threshold 50

# Detect regressions
python db_cli.py query regressions
```

## Architecture

```
storage/
├── __init__.py           # Public API
├── models.py             # SQLAlchemy ORM models
├── backend.py            # Backend implementations (File, SQLite, PostgreSQL)
├── storage.py            # Storage abstraction layer
├── analytics.py          # Query/analytics module
├── writer.py             # Helper for writing results
├── schema.sql            # Database schema (DDL)
└── README.md             # This file
```

## Usage

### Using Storage Directly

```python
from storage import get_storage

config = {
    'type': 'sqlite',
    'path': 'konveyor_iq.db'
}

storage = get_storage(config)

# Create run
run_id = storage.create_run(
    test_suite_name='quarkus',
    test_suite_version='1.0.0'
)

# Save results
storage.save_test_result({
    'run_id': run_id,
    'test_case_id': 'test-001',
    'rule_id': 'jakarta-package-00000',
    'model_name': 'gpt-4o',
    'passed': True,
    'response_time_ms': 450,
    # ... other fields
})

storage.close()
```

### Using DatabaseWriter (Recommended)

```python
from storage.writer import DatabaseWriter

config = {'type': 'sqlite', 'path': 'konveyor_iq.db'}

with DatabaseWriter(config) as writer:
    run_id = writer.start_run(
        name="My Evaluation",
        test_suite_name="quarkus"
    )

    for result in results:
        writer.write_result(run_id, result)

    # Auto-completes run on exit
```

### Using Analytics

```python
from storage import get_storage
from storage.analytics import Analytics

storage = get_storage(config)
session = storage.backend._get_session()
analytics = Analytics(session)

# Model comparison
models = analytics.get_model_comparison(days=30)

# Failing rules
failing = analytics.get_failing_rules(threshold=50)

# Detect regressions
regressions = analytics.detect_regressions(threshold=10)

session.close()
storage.close()
```

## Database Schema

See **[schema.md](schema.md)** for the Entity Relationship Diagram (ERD) with visual representation and detailed table descriptions.

### Core Tables

- **evaluation_runs** - Top-level runs
- **test_results** - Individual test outcomes
- **rules** - Rule metadata cache
- **rule_performance_summary** - Aggregated metrics
- **cost_tracking** - Cost per run
- **performance_alerts** - Anomaly detection (future)

See `schema.sql` for full DDL and `schema.md` for ERD and query examples.

## Backends

### File Backend (Default)
- No dependencies
- JSON files in `results/` directory
- No historical queries

### SQLite Backend
- Requires: `sqlalchemy`
- Single-file database
- Full SQL queries and analytics
- Best for personal use

### PostgreSQL Backend
- Requires: `sqlalchemy`, `psycopg2-binary`
- Multi-user support
- Best for teams and CI/CD

## Documentation

See [docs/database_storage.md](../docs/database_storage.md) for:
- Full CLI reference
- Advanced queries
- PostgreSQL setup guide
- Migration strategies
- Use cases and examples

## Dependencies

```bash
# Required
pip install sqlalchemy>=2.0.0

# Optional (PostgreSQL only)
pip install psycopg2-binary>=2.9.0
```

## License

Apache 2.0
