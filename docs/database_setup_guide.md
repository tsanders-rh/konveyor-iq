# Database Storage Setup Guide

Complete guide to deploying and configuring database storage for Konveyor IQ.

## Prerequisites

- Python 3.9+
- Git (for version tracking in database)
- One of:
  - SQLite (built into Python - no install needed)
  - PostgreSQL 12+ (for team/production use)

## Installation Steps

### 1. Install Python Dependencies

#### Option A: SQLite (Recommended for Personal Use)

```bash
# Install SQLAlchemy (only additional dependency needed)
pip install sqlalchemy>=2.0.0

# Or install from storage requirements file
pip install -r storage/requirements.txt
```

**Total dependencies added**: 1 package (sqlalchemy)

#### Option B: PostgreSQL (Team/Production Use)

```bash
# Install SQLAlchemy + PostgreSQL adapter
pip install sqlalchemy>=2.0.0 psycopg2-binary>=2.9.0

# Or uncomment PostgreSQL line in storage/requirements.txt and run:
pip install -r storage/requirements.txt
```

**Total dependencies added**: 2 packages (sqlalchemy, psycopg2-binary)

### 2. Update Main Requirements (Optional)

If you want database dependencies available by default, update the main `requirements.txt`:

```bash
# Add to requirements.txt
echo "sqlalchemy>=2.0.0  # Database storage backend" >> requirements.txt

# For PostgreSQL support
echo "psycopg2-binary>=2.9.0  # PostgreSQL adapter (optional)" >> requirements.txt
```

### 3. Configure Storage Backend

Edit `config.yaml`:

#### For SQLite (Local Development)

```yaml
storage:
  type: "sqlite"
  path: "konveyor_iq.db"

reporting:
  write_to_database: true  # Enable DB writes
```

#### For PostgreSQL (Production)

```yaml
storage:
  type: "postgresql"
  connection_string: "${DATABASE_URL}"

reporting:
  write_to_database: true
```

Set environment variable:
```bash
export DATABASE_URL="postgresql://user:password@localhost:5432/konveyor_iq"
```

### 4. Initialize Database Schema

```bash
python db_cli.py init --config config.yaml
```

Expected output:
```
Initializing database: sqlite
✓ Database initialized successfully
```

### 5. Verify Installation

```bash
# Check that tables were created (SQLite)
sqlite3 konveyor_iq.db ".tables"

# Expected output:
# cost_tracking            performance_alerts
# evaluation_runs          rule_performance_summary
# rules                    run_models
# test_results

# Check that CLI works
python db_cli.py query runs --limit 5
```

## PostgreSQL Setup (Detailed)

### Local Development

#### macOS (Homebrew)

```bash
# Install PostgreSQL
brew install postgresql@15
brew services start postgresql@15

# Create database
createdb konveyor_iq

# Create user (optional)
psql postgres -c "CREATE USER konveyor WITH PASSWORD 'yourpassword';"
psql postgres -c "GRANT ALL PRIVILEGES ON DATABASE konveyor_iq TO konveyor;"

# Set connection string
export DATABASE_URL="postgresql://konveyor:yourpassword@localhost:5432/konveyor_iq"

# Initialize schema
python db_cli.py init --config config.yaml
```

#### Ubuntu/Debian

```bash
# Install PostgreSQL
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib

# Start service
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database and user
sudo -u postgres psql -c "CREATE DATABASE konveyor_iq;"
sudo -u postgres psql -c "CREATE USER konveyor WITH PASSWORD 'yourpassword';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE konveyor_iq TO konveyor;"

# Set connection string
export DATABASE_URL="postgresql://konveyor:yourpassword@localhost:5432/konveyor_iq"

# Initialize schema
python db_cli.py init --config config.yaml
```

#### Docker

```bash
# Run PostgreSQL container
docker run -d \
  --name konveyor-iq-db \
  -e POSTGRES_DB=konveyor_iq \
  -e POSTGRES_USER=konveyor \
  -e POSTGRES_PASSWORD=yourpassword \
  -p 5432:5432 \
  -v konveyor_iq_data:/var/lib/postgresql/data \
  postgres:15

# Wait for container to start
sleep 5

# Set connection string
export DATABASE_URL="postgresql://konveyor:yourpassword@localhost:5432/konveyor_iq"

# Initialize schema
python db_cli.py init --config config.yaml
```

### Production Deployment

#### AWS RDS

1. **Create RDS PostgreSQL Instance**
   - Engine: PostgreSQL 15
   - Instance class: db.t3.micro (start small)
   - Storage: 20GB GP3
   - Enable automated backups
   - VPC: Configure security groups

2. **Get Connection Details**
   ```
   Endpoint: konveyor-iq.xxxxx.us-east-1.rds.amazonaws.com
   Port: 5432
   Database: konveyor_iq
   ```

3. **Set Connection String**
   ```bash
   export DATABASE_URL="postgresql://admin:password@konveyor-iq.xxxxx.us-east-1.rds.amazonaws.com:5432/konveyor_iq"
   ```

4. **Initialize Schema**
   ```bash
   python db_cli.py init --config config.yaml
   ```

#### Google Cloud SQL

1. **Create Cloud SQL Instance**
   ```bash
   gcloud sql instances create konveyor-iq \
     --database-version=POSTGRES_15 \
     --tier=db-f1-micro \
     --region=us-central1
   ```

2. **Create Database**
   ```bash
   gcloud sql databases create konveyor_iq --instance=konveyor-iq
   ```

3. **Create User**
   ```bash
   gcloud sql users create konveyor \
     --instance=konveyor-iq \
     --password=yourpassword
   ```

4. **Get Connection Name**
   ```bash
   gcloud sql instances describe konveyor-iq --format="value(connectionName)"
   # Output: project-id:region:instance-name
   ```

5. **Connect via Cloud SQL Proxy**
   ```bash
   cloud_sql_proxy -instances=project-id:region:konveyor-iq=tcp:5432
   ```

6. **Set Connection String**
   ```bash
   export DATABASE_URL="postgresql://konveyor:yourpassword@localhost:5432/konveyor_iq"
   ```

#### Azure Database for PostgreSQL

1. **Create PostgreSQL Server**
   ```bash
   az postgres server create \
     --resource-group konveyor-rg \
     --name konveyor-iq-db \
     --location eastus \
     --admin-user konveyor \
     --admin-password yourpassword \
     --sku-name B_Gen5_1
   ```

2. **Configure Firewall**
   ```bash
   az postgres server firewall-rule create \
     --resource-group konveyor-rg \
     --server konveyor-iq-db \
     --name AllowMyIP \
     --start-ip-address YOUR_IP \
     --end-ip-address YOUR_IP
   ```

3. **Create Database**
   ```bash
   az postgres db create \
     --resource-group konveyor-rg \
     --server-name konveyor-iq-db \
     --name konveyor_iq
   ```

4. **Set Connection String**
   ```bash
   export DATABASE_URL="postgresql://konveyor@konveyor-iq-db:yourpassword@konveyor-iq-db.postgres.database.azure.com:5432/konveyor_iq?sslmode=require"
   ```

## Deployment Checklist

### Pre-Deployment

- [ ] Install Python dependencies (sqlalchemy, psycopg2-binary if PostgreSQL)
- [ ] Choose storage backend (SQLite vs PostgreSQL)
- [ ] Set up database (create DB, configure credentials)
- [ ] Update `config.yaml` with storage settings
- [ ] Set environment variables (DATABASE_URL if PostgreSQL)
- [ ] Test connection: `python db_cli.py init --config config.yaml`

### Post-Deployment

- [ ] Run test evaluation to verify database writes work
- [ ] Query recent runs: `python db_cli.py query runs`
- [ ] Set up backups (automated for cloud DBs)
- [ ] Configure monitoring/alerting (optional)
- [ ] Document connection details for team

## Configuration Examples

### Development (SQLite)

```yaml
# config.yaml
storage:
  type: "sqlite"
  path: "konveyor_iq.db"

reporting:
  formats:
    - html
    - markdown
  output_dir: "results/"
  write_to_database: true  # Write to both files AND database
```

### Staging (PostgreSQL - Single Server)

```yaml
# config.yaml
storage:
  type: "postgresql"
  connection_string: "${DATABASE_URL}"

reporting:
  formats:
    - html
  output_dir: "results/"
  write_to_database: true
```

```bash
# .env file (for staging server)
DATABASE_URL=postgresql://konveyor:stagingpass@staging-db.internal:5432/konveyor_iq
```

### Production (PostgreSQL - Multi-Region)

```yaml
# config.yaml
storage:
  type: "postgresql"
  connection_string: "${DATABASE_URL}"

reporting:
  formats:
    - html
  output_dir: "s3://konveyor-iq-results/"  # Optional: Store HTML reports in S3
  write_to_database: true
```

```bash
# .env file (production)
DATABASE_URL=postgresql://konveyor:prod_secret@prod-db.us-east-1.rds.amazonaws.com:5432/konveyor_iq?sslmode=require
```

## CI/CD Integration

### GitHub Actions

```yaml
# .github/workflows/evaluate.yml
name: Konveyor IQ Evaluation

on:
  push:
    branches: [main]
  schedule:
    - cron: '0 0 * * *'  # Daily at midnight

jobs:
  evaluate:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_DB: konveyor_iq
          POSTGRES_USER: konveyor
          POSTGRES_PASSWORD: test_password
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r storage/requirements.txt

      - name: Initialize database
        env:
          DATABASE_URL: postgresql://konveyor:test_password@localhost:5432/konveyor_iq
        run: |
          python db_cli.py init --config config.yaml

      - name: Run evaluation
        env:
          DATABASE_URL: postgresql://konveyor:test_password@localhost:5432/konveyor_iq
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          python evaluate.py --benchmark benchmarks/test_cases/generated/quarkus.yaml

      - name: Check for regressions
        env:
          DATABASE_URL: postgresql://konveyor:test_password@localhost:5432/konveyor_iq
        run: |
          python db_cli.py query regressions --threshold 10
          # Exit code will be non-zero if regressions found
```

### GitLab CI

```yaml
# .gitlab-ci.yml
stages:
  - evaluate
  - analyze

variables:
  DATABASE_URL: "postgresql://konveyor:password@postgres:5432/konveyor_iq"

services:
  - postgres:15

before_script:
  - pip install -r requirements.txt
  - pip install -r storage/requirements.txt
  - python db_cli.py init --config config.yaml

evaluate:
  stage: evaluate
  script:
    - python evaluate.py --benchmark benchmarks/test_cases/generated/quarkus.yaml
  artifacts:
    paths:
      - results/

analyze:
  stage: analyze
  script:
    - python db_cli.py query models --days 7
    - python db_cli.py query regressions --threshold 10
```

## Backup and Recovery

### SQLite Backups

```bash
# Backup
cp konveyor_iq.db konveyor_iq.db.backup-$(date +%Y%m%d)

# Or use SQLite backup command
sqlite3 konveyor_iq.db ".backup 'konveyor_iq.db.backup'"

# Restore
cp konveyor_iq.db.backup konveyor_iq.db

# Automated daily backups
echo "0 2 * * * cp /path/to/konveyor_iq.db /backups/konveyor_iq.db.\$(date +\%Y\%m\%d)" | crontab -
```

### PostgreSQL Backups

```bash
# Backup (dump)
pg_dump -h localhost -U konveyor konveyor_iq > backup-$(date +%Y%m%d).sql

# Restore
psql -h localhost -U konveyor konveyor_iq < backup-20250125.sql

# Automated backups (cron)
echo "0 2 * * * pg_dump -h localhost -U konveyor konveyor_iq > /backups/konveyor_iq-\$(date +\%Y\%m\%d).sql" | crontab -
```

## Troubleshooting

### SQLite Issues

**Error: "database is locked"**
```bash
# SQLite doesn't handle concurrent writes well
# Solution: Use PostgreSQL for CI/CD, or serialize evaluations
```

**Error: "unable to open database file"**
```bash
# Check file permissions
ls -la konveyor_iq.db

# Fix permissions
chmod 644 konveyor_iq.db
```

### PostgreSQL Issues

**Error: "FATAL: role 'konveyor' does not exist"**
```bash
# Create user
psql postgres -c "CREATE USER konveyor WITH PASSWORD 'yourpassword';"
```

**Error: "FATAL: database 'konveyor_iq' does not exist"**
```bash
# Create database
createdb konveyor_iq
# Or
psql postgres -c "CREATE DATABASE konveyor_iq;"
```

**Error: "connection refused"**
```bash
# Check PostgreSQL is running
pg_isready -h localhost -p 5432

# Start PostgreSQL
# macOS:
brew services start postgresql@15
# Linux:
sudo systemctl start postgresql
```

**Error: "could not connect to server: Connection refused"**
```bash
# Check connection string
echo $DATABASE_URL

# Verify PostgreSQL is listening
netstat -an | grep 5432
```

### Dependency Issues

**Error: "No module named 'sqlalchemy'"**
```bash
pip install sqlalchemy>=2.0.0
```

**Error: "No module named 'psycopg2'"**
```bash
pip install psycopg2-binary>=2.9.0
```

## Monitoring

### Basic Health Check

```bash
# Check database connectivity
python -c "from storage import get_storage; storage = get_storage({'type': 'sqlite', 'path': 'konveyor_iq.db'}); print('✓ Connected'); storage.close()"

# Check recent activity
python db_cli.py query runs --limit 5
```

### PostgreSQL Monitoring

```sql
-- Active connections
SELECT count(*) FROM pg_stat_activity WHERE datname = 'konveyor_iq';

-- Database size
SELECT pg_size_pretty(pg_database_size('konveyor_iq'));

-- Table sizes
SELECT
  schemaname,
  tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Slow queries (if logging enabled)
SELECT query, mean_exec_time, calls
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;
```

## Performance Tuning

### PostgreSQL Configuration

```ini
# /etc/postgresql/15/main/postgresql.conf

# Memory settings
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 16MB

# Connection settings
max_connections = 100

# Query performance
random_page_cost = 1.1  # For SSD
effective_io_concurrency = 200

# Write performance
checkpoint_completion_target = 0.9
wal_buffers = 16MB
```

### Index Optimization

```sql
-- Check index usage
SELECT
  schemaname,
  tablename,
  indexname,
  idx_scan as index_scans
FROM pg_stat_user_indexes
ORDER BY idx_scan;

-- Rebuild indexes if needed
REINDEX TABLE test_results;
```

## Migration from File Storage

If you have existing file-based results and want to import them:

```python
# import_historical_data.py
import json
import glob
from pathlib import Path
from storage.writer import DatabaseWriter

config = {'type': 'sqlite', 'path': 'konveyor_iq.db'}

with DatabaseWriter(config) as writer:
    # Find all result files
    for run_dir in Path('results/').iterdir():
        if not run_dir.is_dir():
            continue

        # Read run metadata
        run_file = run_dir / 'run.json'
        if not run_file.exists():
            continue

        with open(run_file) as f:
            run_data = json.load(f)

        # Create run in DB
        run_id = writer.start_run(**run_data)

        # Import results
        results_file = run_dir / 'results' / 'test_results.jsonl'
        if results_file.exists():
            with open(results_file) as f:
                for line in f:
                    result = json.loads(line)
                    writer.write_result(run_id, result)

        writer.complete_run(run_id)

print("Historical data imported successfully!")
```

## Summary

**Minimum Setup (SQLite)**:
1. `pip install sqlalchemy`
2. Update `config.yaml` with SQLite settings
3. `python db_cli.py init`
4. Run evaluations as normal

**Production Setup (PostgreSQL)**:
1. `pip install sqlalchemy psycopg2-binary`
2. Set up PostgreSQL (local/cloud)
3. Update `config.yaml` with connection string
4. `python db_cli.py init`
5. Configure backups and monitoring

Total setup time: **5-10 minutes** for SQLite, **30-60 minutes** for PostgreSQL (including cloud setup).
