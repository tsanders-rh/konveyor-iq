"""
Storage layer for Konveyor IQ evaluation results.

Supports multiple backends:
- File-based (JSON) - default, no dependencies
- SQLite - local database, no setup required
- PostgreSQL - production database, requires setup
"""

from .models import (
    EvaluationRun,
    RunModel,
    TestResult,
    Rule,
    RulePerformanceSummary,
    CostTracking,
    PerformanceAlert
)
from .storage import Storage, get_storage
from .backend import FileBackend, SQLiteBackend, PostgreSQLBackend

__all__ = [
    'EvaluationRun',
    'RunModel',
    'TestResult',
    'Rule',
    'RulePerformanceSummary',
    'CostTracking',
    'PerformanceAlert',
    'Storage',
    'get_storage',
    'FileBackend',
    'SQLiteBackend',
    'PostgreSQLBackend',
]
