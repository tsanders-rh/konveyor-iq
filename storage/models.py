"""
SQLAlchemy ORM models for Konveyor IQ storage.
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, Text, DateTime,
    ForeignKey, Index, UniqueConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()


class EvaluationRun(Base):
    """Represents a complete evaluation run across one or more models."""
    __tablename__ = 'evaluation_runs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255))
    test_suite_name = Column(String(255), nullable=False, index=True)
    test_suite_version = Column(String(50), nullable=False)
    started_at = Column(DateTime, nullable=False, index=True)
    completed_at = Column(DateTime)
    status = Column(String(50), nullable=False, index=True)  # 'running', 'completed', 'failed'
    config_snapshot = Column(Text)  # JSON
    git_commit = Column(String(255))
    git_branch = Column(String(255))
    created_at = Column(DateTime, default=func.now())

    # Relationships
    models = relationship("RunModel", back_populates="run", cascade="all, delete-orphan")
    test_results = relationship("TestResult", back_populates="run", cascade="all, delete-orphan")
    cost_tracking = relationship("CostTracking", back_populates="run", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<EvaluationRun(run_id={self.run_id}, suite={self.test_suite_name}, status={self.status})>"


class RunModel(Base):
    """Models tested in a specific evaluation run."""
    __tablename__ = 'run_models'

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String(255), ForeignKey('evaluation_runs.run_id', ondelete='CASCADE'), nullable=False, index=True)
    model_name = Column(String(255), nullable=False, index=True)
    model_version = Column(String(255))
    total_tests = Column(Integer, default=0)
    passed_tests = Column(Integer, default=0)
    failed_tests = Column(Integer, default=0)
    total_cost = Column(Float, default=0.0)
    avg_response_time_ms = Column(Float)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    run = relationship("EvaluationRun", back_populates="models")

    def __repr__(self):
        return f"<RunModel(model={self.model_name}, tests={self.total_tests}, passed={self.passed_tests})>"


class TestResult(Base):
    """Individual test case evaluation result."""
    __tablename__ = 'test_results'

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String(255), ForeignKey('evaluation_runs.run_id', ondelete='CASCADE'), nullable=False, index=True)
    test_case_id = Column(String(255), nullable=False)
    rule_id = Column(String(255), nullable=False, index=True)
    model_name = Column(String(255), nullable=False, index=True)

    # Test execution
    executed_at = Column(DateTime, nullable=False, index=True)
    passed = Column(Boolean, nullable=False, index=True)
    failure_reason = Column(Text)

    # LLM output
    generated_code = Column(Text)
    generated_explanation = Column(Text)
    raw_response = Column(Text)

    # Prompt tracking
    prompt_source = Column(String(255))
    prompt_hash = Column(String(64))

    # Metrics - Correctness
    functional_correctness = Column(Boolean)
    compiles = Column(Boolean)
    introduces_violations = Column(Boolean, default=False)

    # Metrics - Quality
    pylint_score = Column(Float)
    cyclomatic_complexity = Column(Integer)
    maintainability_index = Column(Float)
    style_violations = Column(Integer, default=0)

    # Metrics - Security
    security_issues = Column(Integer, default=0)
    high_severity_security = Column(Integer, default=0)

    # Metrics - Explainability
    has_explanation = Column(Boolean, default=False)
    explanation_quality_score = Column(Float)

    # Metrics - Performance
    response_time_ms = Column(Float, nullable=False)
    tokens_used = Column(Integer)
    estimated_cost = Column(Float)

    created_at = Column(DateTime, default=func.now())

    # Relationships
    run = relationship("EvaluationRun", back_populates="test_results")
    rule = relationship("Rule", foreign_keys=[rule_id], primaryjoin="TestResult.rule_id==Rule.rule_id")

    # Composite index for common queries
    __table_args__ = (
        Index('idx_test_results_composite', 'rule_id', 'model_name', 'executed_at'),
    )

    def __repr__(self):
        return f"<TestResult(rule={self.rule_id}, model={self.model_name}, passed={self.passed})>"


class Rule(Base):
    """Rule metadata cached from test suites."""
    __tablename__ = 'rules'

    rule_id = Column(String(255), primary_key=True)
    description = Column(Text)
    severity = Column(String(50), index=True)  # 'low', 'medium', 'high', 'critical'
    category = Column(String(255), index=True)
    migration_complexity = Column(String(50), index=True)  # 'trivial', 'low', 'medium', 'high', 'expert'
    migration_pattern = Column(Text)
    source_url = Column(Text)
    first_seen_at = Column(DateTime, default=func.now())
    last_seen_at = Column(DateTime, default=func.now())
    test_case_count = Column(Integer, default=0)

    def __repr__(self):
        return f"<Rule(rule_id={self.rule_id}, complexity={self.migration_complexity})>"


class RulePerformanceSummary(Base):
    """Aggregated performance metrics per rule and model."""
    __tablename__ = 'rule_performance_summary'

    id = Column(Integer, primary_key=True, autoincrement=True)
    rule_id = Column(String(255), nullable=False, index=True)
    model_name = Column(String(255), nullable=False, index=True)
    time_period = Column(String(50), nullable=False)  # 'all', '30d', '7d', '24h'

    # Counts
    total_tests = Column(Integer, nullable=False)
    passed_tests = Column(Integer, nullable=False)
    failed_tests = Column(Integer, nullable=False)
    pass_rate = Column(Float, nullable=False)

    # Averages
    avg_response_time_ms = Column(Float)
    avg_tokens_used = Column(Float)
    avg_cost = Column(Float)
    avg_quality_score = Column(Float)
    avg_explanation_score = Column(Float)

    # Trends
    pass_rate_trend = Column(Float)  # Change vs previous period
    cost_trend = Column(Float)

    last_updated_at = Column(DateTime, default=func.now())

    __table_args__ = (
        UniqueConstraint('rule_id', 'model_name', 'time_period', name='uq_perf_summary'),
        Index('idx_perf_summary_composite', 'rule_id', 'model_name', 'time_period'),
    )

    def __repr__(self):
        return f"<RulePerformanceSummary(rule={self.rule_id}, model={self.model_name}, pass_rate={self.pass_rate:.1%})>"


class CostTracking(Base):
    """Cost tracking per evaluation run and model."""
    __tablename__ = 'cost_tracking'

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String(255), ForeignKey('evaluation_runs.run_id', ondelete='CASCADE'), nullable=False)
    model_name = Column(String(255), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    tests_executed = Column(Integer, nullable=False)
    total_cost = Column(Float, nullable=False)
    total_tokens = Column(Integer)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    run = relationship("EvaluationRun", back_populates="cost_tracking")

    def __repr__(self):
        return f"<CostTracking(model={self.model_name}, cost=${self.total_cost:.4f}, tests={self.tests_executed})>"


class PerformanceAlert(Base):
    """Alerts for performance anomalies and regressions."""
    __tablename__ = 'performance_alerts'

    id = Column(Integer, primary_key=True, autoincrement=True)
    alert_type = Column(String(100), nullable=False)  # 'pass_rate_drop', 'cost_spike', 'latency_increase'
    severity = Column(String(50), nullable=False)  # 'info', 'warning', 'critical'
    rule_id = Column(String(255))
    model_name = Column(String(255))
    message = Column(Text, nullable=False)
    threshold_value = Column(Float)
    actual_value = Column(Float)
    detected_at = Column(DateTime, default=func.now(), index=True)
    acknowledged = Column(Boolean, default=False, index=True)
    acknowledged_at = Column(DateTime)
    acknowledged_by = Column(String(255))

    def __repr__(self):
        return f"<PerformanceAlert(type={self.alert_type}, severity={self.severity}, ack={self.acknowledged})>"
