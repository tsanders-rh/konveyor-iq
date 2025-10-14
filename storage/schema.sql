-- Konveyor IQ Database Schema
-- Supports SQLite and PostgreSQL

-- Evaluation runs (top-level grouping)
CREATE TABLE evaluation_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,  -- Use SERIAL for PostgreSQL
    run_id TEXT UNIQUE NOT NULL,           -- UUID for external reference
    name TEXT,                              -- Optional run name
    test_suite_name TEXT NOT NULL,
    test_suite_version TEXT NOT NULL,
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    status TEXT NOT NULL,                   -- 'running', 'completed', 'failed'
    config_snapshot TEXT,                   -- JSON of config used
    git_commit TEXT,                        -- Git SHA if in repo
    git_branch TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_runs_started_at ON evaluation_runs(started_at);
CREATE INDEX idx_runs_suite ON evaluation_runs(test_suite_name);
CREATE INDEX idx_runs_status ON evaluation_runs(status);

-- Models tested in each run
CREATE TABLE run_models (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    model_name TEXT NOT NULL,
    model_version TEXT,                     -- e.g., 'gpt-4-turbo-2024-04-09'
    total_tests INTEGER DEFAULT 0,
    passed_tests INTEGER DEFAULT 0,
    failed_tests INTEGER DEFAULT 0,
    total_cost REAL DEFAULT 0.0,
    avg_response_time_ms REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (run_id) REFERENCES evaluation_runs(run_id) ON DELETE CASCADE
);

CREATE INDEX idx_run_models_run_id ON run_models(run_id);
CREATE INDEX idx_run_models_model ON run_models(model_name);

-- Individual test results
CREATE TABLE test_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    test_case_id TEXT NOT NULL,
    rule_id TEXT NOT NULL,
    model_name TEXT NOT NULL,

    -- Test execution
    executed_at TIMESTAMP NOT NULL,
    passed BOOLEAN NOT NULL,
    failure_reason TEXT,

    -- LLM output
    generated_code TEXT,
    generated_explanation TEXT,
    raw_response TEXT,

    -- Prompt tracking
    prompt_source TEXT,                     -- 'custom', 'config:<migration>', 'default'
    prompt_hash TEXT,                       -- Hash for deduplication

    -- Metrics
    functional_correctness BOOLEAN,
    compiles BOOLEAN,
    introduces_violations BOOLEAN DEFAULT FALSE,

    -- Quality metrics
    pylint_score REAL,
    cyclomatic_complexity INTEGER,
    maintainability_index REAL,
    style_violations INTEGER DEFAULT 0,

    -- Security
    security_issues INTEGER DEFAULT 0,
    high_severity_security INTEGER DEFAULT 0,

    -- Explainability
    has_explanation BOOLEAN DEFAULT FALSE,
    explanation_quality_score REAL,

    -- Performance
    response_time_ms REAL NOT NULL,
    tokens_used INTEGER,
    estimated_cost REAL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (run_id) REFERENCES evaluation_runs(run_id) ON DELETE CASCADE
);

CREATE INDEX idx_test_results_run_id ON test_results(run_id);
CREATE INDEX idx_test_results_rule_id ON test_results(rule_id);
CREATE INDEX idx_test_results_model ON test_results(model_name);
CREATE INDEX idx_test_results_passed ON test_results(passed);
CREATE INDEX idx_test_results_executed_at ON test_results(executed_at);
CREATE INDEX idx_test_results_composite ON test_results(rule_id, model_name, executed_at);

-- Rule metadata (cached from test suites)
CREATE TABLE rules (
    rule_id TEXT PRIMARY KEY,
    description TEXT,
    severity TEXT,                          -- 'low', 'medium', 'high', 'critical'
    category TEXT,
    migration_complexity TEXT,              -- 'trivial', 'low', 'medium', 'high', 'expert'
    migration_pattern TEXT,
    source_url TEXT,
    first_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    test_case_count INTEGER DEFAULT 0
);

CREATE INDEX idx_rules_complexity ON rules(migration_complexity);
CREATE INDEX idx_rules_category ON rules(category);

-- Aggregated performance metrics (materialized view / cache table)
CREATE TABLE rule_performance_summary (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rule_id TEXT NOT NULL,
    model_name TEXT NOT NULL,
    time_period TEXT NOT NULL,              -- 'all', '30d', '7d', '24h'

    -- Counts
    total_tests INTEGER NOT NULL,
    passed_tests INTEGER NOT NULL,
    failed_tests INTEGER NOT NULL,
    pass_rate REAL NOT NULL,

    -- Averages
    avg_response_time_ms REAL,
    avg_tokens_used REAL,
    avg_cost REAL,
    avg_quality_score REAL,
    avg_explanation_score REAL,

    -- Trends
    pass_rate_trend REAL,                   -- Change vs previous period
    cost_trend REAL,

    last_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(rule_id, model_name, time_period)
);

CREATE INDEX idx_perf_summary_rule ON rule_performance_summary(rule_id);
CREATE INDEX idx_perf_summary_model ON rule_performance_summary(model_name);
CREATE INDEX idx_perf_summary_composite ON rule_performance_summary(rule_id, model_name, time_period);

-- Cost tracking
CREATE TABLE cost_tracking (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    model_name TEXT NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    tests_executed INTEGER NOT NULL,
    total_cost REAL NOT NULL,
    total_tokens INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (run_id) REFERENCES evaluation_runs(run_id) ON DELETE CASCADE
);

CREATE INDEX idx_cost_tracking_model ON cost_tracking(model_name);
CREATE INDEX idx_cost_tracking_timestamp ON cost_tracking(timestamp);

-- Alerts / anomalies (future feature)
CREATE TABLE performance_alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    alert_type TEXT NOT NULL,               -- 'pass_rate_drop', 'cost_spike', 'latency_increase'
    severity TEXT NOT NULL,                 -- 'info', 'warning', 'critical'
    rule_id TEXT,
    model_name TEXT,
    message TEXT NOT NULL,
    threshold_value REAL,
    actual_value REAL,
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    acknowledged BOOLEAN DEFAULT FALSE,
    acknowledged_at TIMESTAMP,
    acknowledged_by TEXT
);

CREATE INDEX idx_alerts_detected_at ON performance_alerts(detected_at);
CREATE INDEX idx_alerts_acknowledged ON performance_alerts(acknowledged);
