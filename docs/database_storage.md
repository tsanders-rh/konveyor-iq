# Database Storage for Konveyor IQ

Store evaluation results in a relational database (SQLite or PostgreSQL) to enable:
- **Historical tracking** - Track model performance over time
- **Trend analysis** - Identify improvements/regressions
- **Rule-level insights** - See which rules consistently fail
- **Cost tracking** - Monitor spending across evaluations
- **Team collaboration** - Share results via centralized database

## Quick Start

### 1. Enable SQLite Storage (Local/Personal Use)

```yaml
# config.yaml
storage:
  type: "sqlite"
  path: "konveyor_iq.db"

reporting:
  write_to_database: true  # Write to DB in addition to files
```

Initialize the database:
```bash
python db_cli.py init --config config.yaml
```

### 2. Run Evaluations

Results will now be stored in the database automatically:
```bash
python evaluate.py --benchmark benchmarks/test_cases/generated/quarkus.yaml
```

### 3. Query Historical Data

```bash
# See recent evaluation runs
python db_cli.py query runs

# Compare model performance (last 30 days)
python db_cli.py query models --days 30

# Find failing rules
python db_cli.py query rules --threshold 50 --days 30

# Check performance trends for specific rule
python db_cli.py query trends --rule jakarta-package-00000 --days 30

# Detect regressions
python db_cli.py query regressions --threshold 10
```

## Storage Backends

### File Backend (Default)
```yaml
storage:
  type: "file"
  path: "results/"
```

**Pros:**
- No dependencies
- Portable (JSON files)
- Easy to share

**Cons:**
- No historical queries
- No trend analysis
- Difficult to aggregate across runs

### SQLite Backend (Recommended for Personal Use)
```yaml
storage:
  type: "sqlite"
  path: "konveyor_iq.db"
```

**Pros:**
- No setup required (stdlib)
- Full SQL queries
- Historical tracking
- Single file (easy backup)

**Cons:**
- Single writer (not ideal for CI/CD)
- Limited concurrency

**Best for:**
- Individual developers
- Local experimentation
- Quick historical analysis

### PostgreSQL Backend (Production/Team Use)
```yaml
storage:
  type: "postgresql"
  connection_string: "${DATABASE_URL}"
```

Example connection string:
```
postgresql://user:password@localhost:5432/konveyor_iq
```

**Pros:**
- Multi-user support
- High concurrency
- Advanced analytics
- Centralized team database

**Cons:**
- Requires PostgreSQL setup
- Network dependency

**Best for:**
- Team environments
- CI/CD pipelines
- Production monitoring
- Shared analytics dashboards

## Database Schema

See **[storage/schema.md](../storage/schema.md)** for the full Entity Relationship Diagram (ERD) and detailed schema documentation.

### Core Tables

**evaluation_runs** - Top-level evaluation runs
- `run_id` - Unique identifier
- `test_suite_name` - Which test suite was run
- `started_at`, `completed_at` - Timing
- `status` - running, completed, failed
- `git_commit`, `git_branch` - Version tracking

**test_results** - Individual test outcomes
- Links to run via `run_id`
- `rule_id`, `model_name` - What was tested
- `passed`, `failure_reason` - Outcome
- `generated_code`, `generated_explanation` - LLM output
- All metrics (compilation, quality, security, etc.)
- `response_time_ms`, `estimated_cost` - Performance

**rules** - Rule metadata cache
- `rule_id`, `description`, `severity`
- `migration_complexity` - TRIVIAL, LOW, MEDIUM, HIGH, EXPERT
- `test_case_count` - How many tests exist

**rule_performance_summary** - Aggregated metrics
- Pre-computed pass rates by rule/model/time period
- Used for fast dashboard queries

## CLI Commands

### Initialize Database
```bash
python db_cli.py init --config config.yaml
```

### Query Failing Rules
Find rules with low pass rates:
```bash
python db_cli.py query rules \
  --threshold 50 \    # Rules below 50% pass rate
  --min-tests 3 \     # Require at least 3 tests
  --days 30           # Last 30 days
```

Output:
```
Rules with pass rate < 50% (last 30 days):

Rule ID                                  Complexity   Pass Rate    Tests
--------------------------------------------------------------------------------
remote-ejb-to-quarkus-00000              high            0.0%     0/12
persistence-to-quarkus-00015             medium         40.0%     4/10
```

### Query Performance Trends
Track how a rule performs over time:
```bash
python db_cli.py query trends \
  --rule jakarta-package-00000 \
  --model gpt-4o \
  --days 30
```

Output:
```
Performance trends for jakarta-package-00000 (last 30 days):

Date         Model                          Pass Rate    Avg Time (ms)   Tests
----------------------------------------------------------------------------------
2025-01-15   gpt-4o                         100.0%            450         3/3
2025-01-20   gpt-4o                         100.0%            420         4/4
2025-01-25   gpt-4o                          90.0%            480         9/10
```

### Compare Models
See which model performs best:
```bash
python db_cli.py query models --days 30

# Filter by specific rule
python db_cli.py query models --rule jakarta-package-00000
```

Output:
```
Model Performance Comparison (last 30 days):

Model                          Pass Rate    Avg Time     Total Cost   Tests
---------------------------------------------------------------------------------
gpt-4o                            90.0%       450ms       $0.2195     90/100
claude-3-7-sonnet-latest          87.6%       550ms       $0.2002     87/100
gpt-3.5-turbo                     85.0%       320ms       $0.0185     85/100
```

### Complexity Breakdown
Pass rates by difficulty level:
```bash
python db_cli.py query complexity --days 30

# Filter by model
python db_cli.py query complexity --model gpt-4o
```

Output:
```
Pass Rate by Complexity (last 30 days):

Complexity      Pass Rate    Avg Time (ms)   Tests
------------------------------------------------------------
TRIVIAL            96.0%            350      24/25
LOW                84.0%            420      21/25
MEDIUM             68.0%            580      17/25
HIGH               44.0%            750      11/25
EXPERT             20.0%            920       5/25
```

### Detect Regressions
Find rules that used to pass but now fail:
```bash
python db_cli.py query regressions \
  --threshold 10 \      # Drop ≥ 10%
  --recent 7 \          # Last 7 days
  --historical 30       # Compare to previous 30 days
```

Output:
```
⚠ Performance Regressions Detected (drop ≥ 10%):

Rule ID                                  Model                     Drop      Historical → Recent
-----------------------------------------------------------------------------------------------
jakarta-package-00015                    gpt-4o                   15.2%     92.0% → 76.8%
persistence-to-quarkus-00020             claude-3-7-sonnet        12.5%     88.0% → 75.5%
```

### List Recent Runs
```bash
python db_cli.py query runs --limit 10
```

Output:
```
Recent Evaluation Runs:

Run ID                                Name                 Started              Status       Pass Rate
---------------------------------------------------------------------------------------------------
abc123-def456-...                     quarkus              2025-01-25 14:30:00  completed    87.6% (87/100)
xyz789-uvw123-...                     quarkus              2025-01-24 10:15:00  completed    85.0% (85/100)
```

### Export Data
Export run results to JSON:
```bash
# To file
python db_cli.py export --run-id abc123 --output results.json

# To stdout
python db_cli.py export --run-id abc123
```

## Integration with Evaluation Flow

The evaluation flow automatically writes to the database if `reporting.write_to_database: true` is set.

### Manual Integration

For custom scripts, use the `DatabaseWriter`:

```python
from storage.writer import DatabaseWriter

# Initialize writer
storage_config = {
    'type': 'sqlite',
    'path': 'konveyor_iq.db'
}

with DatabaseWriter(storage_config) as writer:
    # Start evaluation run
    run_id = writer.start_run(
        name="My Test Run",
        test_suite_name="quarkus",
        test_suite_version="1.0.0"
    )

    # Write results as they complete
    for result in evaluation_results:
        writer.write_result(run_id, result)

    # Or write in batch
    writer.write_results_batch(run_id, results)

    # Context manager auto-completes run on exit
```

## Advanced Analytics

### Programmatic Queries

Use the `Analytics` class for custom analysis:

```python
from storage import get_storage
from storage.analytics import Analytics

storage_config = {'type': 'sqlite', 'path': 'konveyor_iq.db'}
storage = get_storage(storage_config)

if hasattr(storage.backend, '_get_session'):
    session = storage.backend._get_session()
    analytics = Analytics(session)

    # Model comparison
    models = analytics.get_model_comparison(days=30)

    # Cost analysis
    costs = analytics.get_cost_analysis(group_by='model', days=30)

    # Complexity breakdown
    complexity = analytics.get_complexity_breakdown(
        model_name='gpt-4o',
        days=30
    )

    session.close()

storage.close()
```

## PostgreSQL Setup

### 1. Install PostgreSQL
```bash
# macOS
brew install postgresql
brew services start postgresql

# Ubuntu/Debian
sudo apt-get install postgresql postgresql-contrib
sudo systemctl start postgresql

# Docker
docker run -d \
  --name konveyor-iq-db \
  -e POSTGRES_DB=konveyor_iq \
  -e POSTGRES_USER=konveyor \
  -e POSTGRES_PASSWORD=yourpassword \
  -p 5432:5432 \
  postgres:15
```

### 2. Create Database
```bash
createdb konveyor_iq
```

### 3. Configure Connection
```yaml
# config.yaml
storage:
  type: "postgresql"
  connection_string: "postgresql://konveyor:yourpassword@localhost:5432/konveyor_iq"

# Or use environment variable
storage:
  type: "postgresql"
  connection_string: "${DATABASE_URL}"
```

```bash
export DATABASE_URL="postgresql://konveyor:yourpassword@localhost:5432/konveyor_iq"
```

### 4. Initialize Schema
```bash
python db_cli.py init --config config.yaml
```

## Use Cases

### 1. Track Model Improvements
Monitor if GPT-4o's performance improves after OpenAI releases new versions:
```bash
python db_cli.py query trends --rule <rule-id> --model gpt-4o --days 90
```

### 2. Identify Prompt Engineering Opportunities
Find rules with consistently low pass rates that need better prompts:
```bash
python db_cli.py query rules --threshold 50 --min-tests 10
```

### 3. Cost Forecasting
Estimate costs for running 234 tests:
```bash
python db_cli.py query models --days 30
# Use avg_cost_per_test × 234
```

### 4. A/B Test Prompt Variations
Store results from different prompt strategies, compare pass rates.

### 5. CI/CD Quality Gates
Fail builds if regressions detected:
```bash
python db_cli.py query regressions --threshold 10
exit_code=$?
if [ $exit_code -ne 0 ]; then
  echo "Regressions detected, failing build"
  exit 1
fi
```

### 6. Monthly Reporting
Generate executive summary:
```bash
# Last month's performance
python db_cli.py query models --days 30

# Cost analysis
python db_cli.py query models --days 30 | grep "Total Cost"

# Improvement trends
python db_cli.py query complexity --days 30
```

## Migration Guide

### From File-Based to SQLite

1. **Update config.yaml**
   ```yaml
   storage:
     type: "sqlite"
     path: "konveyor_iq.db"

   reporting:
     write_to_database: true
   ```

2. **Initialize database**
   ```bash
   python db_cli.py init --config config.yaml
   ```

3. **Run new evaluations**
   ```bash
   python evaluate.py --benchmark benchmarks/test_cases/generated/quarkus.yaml
   ```

4. **Verify data**
   ```bash
   python db_cli.py query runs
   ```

**Note:** Historical file-based results are NOT automatically imported. To import:
- Parse existing JSON files
- Use `DatabaseWriter` to insert results
- Set appropriate timestamps

### From SQLite to PostgreSQL

1. **Export SQLite data**
   ```bash
   sqlite3 konveyor_iq.db .dump > backup.sql
   ```

2. **Setup PostgreSQL** (see above)

3. **Update config.yaml**
   ```yaml
   storage:
     type: "postgresql"
     connection_string: "${DATABASE_URL}"
   ```

4. **Initialize PostgreSQL schema**
   ```bash
   python db_cli.py init --config config.yaml
   ```

5. **Migrate data** (manual step - convert SQLite dump to PostgreSQL format)
   Or re-run evaluations to populate new database.

## Troubleshooting

### Database Locked (SQLite)
SQLite doesn't handle concurrent writes well. Use PostgreSQL for CI/CD.

### Connection Refused (PostgreSQL)
Check connection string, verify PostgreSQL is running:
```bash
pg_isready -h localhost -p 5432
```

### Missing Dependencies
```bash
pip install sqlalchemy psycopg2-binary
```

### Slow Queries
Add indexes (already configured in schema.sql):
```sql
CREATE INDEX idx_test_results_composite ON test_results(rule_id, model_name, executed_at);
```

## Schema Reference

See `storage/schema.sql` for full DDL.

Key indexes:
- `test_results(rule_id, model_name, executed_at)` - Trend queries
- `test_results(executed_at)` - Time-based filters
- `test_results(passed)` - Pass rate calculations
- `evaluation_runs(started_at)` - Recent runs

## Dependencies

```bash
pip install sqlalchemy  # Required for all DB backends
pip install psycopg2-binary  # Only for PostgreSQL
```

SQLite is included in Python stdlib - no additional install needed.
