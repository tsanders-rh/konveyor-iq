"""
Storage backend implementations.
"""
import json
import os
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from uuid import uuid4

from sqlalchemy import create_engine, desc, func, and_, or_
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from .models import (
    Base, EvaluationRun, RunModel, TestResult, Rule,
    RulePerformanceSummary, CostTracking, PerformanceAlert
)


class StorageBackend(ABC):
    """Abstract storage backend interface."""

    @abstractmethod
    def create_run(self, **kwargs) -> str:
        """Create a new evaluation run. Returns run_id."""
        pass

    @abstractmethod
    def update_run(self, run_id: str, **kwargs):
        """Update an existing run."""
        pass

    @abstractmethod
    def save_test_result(self, result: Dict[str, Any]):
        """Save a single test result."""
        pass

    @abstractmethod
    def save_test_results_batch(self, results: List[Dict[str, Any]]):
        """Save multiple test results efficiently."""
        pass

    @abstractmethod
    def get_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Get run by ID."""
        pass

    @abstractmethod
    def get_test_results(self, run_id: str, **filters) -> List[Dict[str, Any]]:
        """Get test results for a run with optional filters."""
        pass

    @abstractmethod
    def get_rule_performance(self, rule_id: str, model_name: Optional[str] = None,
                           time_period: str = 'all') -> Dict[str, Any]:
        """Get performance metrics for a rule."""
        pass

    @abstractmethod
    def close(self):
        """Clean up resources."""
        pass


class FileBackend(StorageBackend):
    """File-based storage backend (JSON files)."""

    def __init__(self, base_dir: str = "results"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def create_run(self, **kwargs) -> str:
        run_id = kwargs.get('run_id', str(uuid4()))
        run_data = {
            'run_id': run_id,
            'created_at': datetime.now().isoformat(),
            **kwargs
        }
        run_dir = self.base_dir / run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        with open(run_dir / 'run.json', 'w') as f:
            json.dump(run_data, f, indent=2)

        return run_id

    def update_run(self, run_id: str, **kwargs):
        run_dir = self.base_dir / run_id
        run_file = run_dir / 'run.json'

        if run_file.exists():
            with open(run_file, 'r') as f:
                run_data = json.load(f)
            run_data.update(kwargs)
            with open(run_file, 'w') as f:
                json.dump(run_data, f, indent=2)

    def save_test_result(self, result: Dict[str, Any]):
        run_id = result['run_id']
        run_dir = self.base_dir / run_id / 'results'
        run_dir.mkdir(parents=True, exist_ok=True)

        # Append to results file
        results_file = run_dir / 'test_results.jsonl'
        with open(results_file, 'a') as f:
            f.write(json.dumps(result) + '\n')

    def save_test_results_batch(self, results: List[Dict[str, Any]]):
        for result in results:
            self.save_test_result(result)

    def get_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        run_file = self.base_dir / run_id / 'run.json'
        if run_file.exists():
            with open(run_file, 'r') as f:
                return json.load(f)
        return None

    def get_test_results(self, run_id: str, **filters) -> List[Dict[str, Any]]:
        results_file = self.base_dir / run_id / 'results' / 'test_results.jsonl'
        if not results_file.exists():
            return []

        results = []
        with open(results_file, 'r') as f:
            for line in f:
                result = json.loads(line)
                # Apply filters
                if self._matches_filters(result, filters):
                    results.append(result)
        return results

    def get_rule_performance(self, rule_id: str, model_name: Optional[str] = None,
                           time_period: str = 'all') -> Dict[str, Any]:
        # Aggregate from all runs (simplified version)
        all_results = []
        for run_dir in self.base_dir.iterdir():
            if run_dir.is_dir():
                results = self.get_test_results(
                    run_dir.name,
                    rule_id=rule_id,
                    model_name=model_name
                )
                all_results.extend(results)

        if not all_results:
            return {'rule_id': rule_id, 'total_tests': 0}

        passed = sum(1 for r in all_results if r.get('passed'))
        total = len(all_results)

        return {
            'rule_id': rule_id,
            'model_name': model_name,
            'total_tests': total,
            'passed_tests': passed,
            'pass_rate': passed / total if total > 0 else 0,
            'avg_response_time_ms': sum(r.get('response_time_ms', 0) for r in all_results) / total,
        }

    def _matches_filters(self, result: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """Check if result matches all filters."""
        for key, value in filters.items():
            if result.get(key) != value:
                return False
        return True

    def close(self):
        pass


class SQLiteBackend(StorageBackend):
    """SQLite database backend."""

    def __init__(self, db_path: str = "konveyor_iq.db"):
        self.db_path = db_path

        # Use StaticPool for SQLite to avoid threading issues
        self.engine = create_engine(
            f'sqlite:///{db_path}',
            connect_args={'check_same_thread': False},
            poolclass=StaticPool
        )

        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def _get_session(self) -> Session:
        return self.Session()

    def create_run(self, **kwargs) -> str:
        session = self._get_session()
        try:
            run_id = kwargs.get('run_id', str(uuid4()))
            run = EvaluationRun(
                run_id=run_id,
                name=kwargs.get('name'),
                test_suite_name=kwargs.get('test_suite_name', 'default'),
                test_suite_version=kwargs.get('test_suite_version', '1.0.0'),
                started_at=kwargs.get('started_at', datetime.now()),
                status=kwargs.get('status', 'running'),
                config_snapshot=kwargs.get('config_snapshot'),
                git_commit=kwargs.get('git_commit'),
                git_branch=kwargs.get('git_branch')
            )
            session.add(run)
            session.commit()
            return run_id
        finally:
            session.close()

    def update_run(self, run_id: str, **kwargs):
        session = self._get_session()
        try:
            run = session.query(EvaluationRun).filter_by(run_id=run_id).first()
            if run:
                for key, value in kwargs.items():
                    if hasattr(run, key):
                        setattr(run, key, value)
                session.commit()
        finally:
            session.close()

    def save_test_result(self, result: Dict[str, Any]):
        session = self._get_session()
        try:
            test_result = TestResult(
                run_id=result['run_id'],
                test_case_id=result['test_case_id'],
                rule_id=result['rule_id'],
                model_name=result['model_name'],
                executed_at=result.get('executed_at', datetime.now()),
                passed=result['passed'],
                failure_reason=result.get('failure_reason'),
                generated_code=result.get('generated_code'),
                generated_explanation=result.get('generated_explanation'),
                raw_response=result.get('raw_response'),
                prompt_source=result.get('prompt_source'),
                prompt_hash=result.get('prompt_hash'),
                functional_correctness=result.get('functional_correctness'),
                compiles=result.get('compiles'),
                introduces_violations=result.get('introduces_violations', False),
                pylint_score=result.get('pylint_score'),
                cyclomatic_complexity=result.get('cyclomatic_complexity'),
                maintainability_index=result.get('maintainability_index'),
                style_violations=result.get('style_violations', 0),
                security_issues=result.get('security_issues', 0),
                high_severity_security=result.get('high_severity_security', 0),
                has_explanation=result.get('has_explanation', False),
                explanation_quality_score=result.get('explanation_quality_score'),
                response_time_ms=result.get('response_time_ms', 0),
                tokens_used=result.get('tokens_used'),
                estimated_cost=result.get('estimated_cost')
            )
            session.add(test_result)

            # Update or create rule metadata
            self._upsert_rule(session, result)

            session.commit()
        finally:
            session.close()

    def save_test_results_batch(self, results: List[Dict[str, Any]]):
        session = self._get_session()
        try:
            for result in results:
                test_result = TestResult(**self._map_result_to_model(result))
                session.add(test_result)
                self._upsert_rule(session, result)
            session.commit()
        finally:
            session.close()

    def _map_result_to_model(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Map dictionary to TestResult model fields."""
        return {
            'run_id': result['run_id'],
            'test_case_id': result['test_case_id'],
            'rule_id': result['rule_id'],
            'model_name': result['model_name'],
            'executed_at': result.get('executed_at', datetime.now()),
            'passed': result['passed'],
            'failure_reason': result.get('failure_reason'),
            'generated_code': result.get('generated_code'),
            'generated_explanation': result.get('generated_explanation'),
            'raw_response': result.get('raw_response'),
            'prompt_source': result.get('prompt_source'),
            'prompt_hash': result.get('prompt_hash'),
            'functional_correctness': result.get('functional_correctness'),
            'compiles': result.get('compiles'),
            'introduces_violations': result.get('introduces_violations', False),
            'pylint_score': result.get('pylint_score'),
            'cyclomatic_complexity': result.get('cyclomatic_complexity'),
            'maintainability_index': result.get('maintainability_index'),
            'style_violations': result.get('style_violations', 0),
            'security_issues': result.get('security_issues', 0),
            'high_severity_security': result.get('high_severity_security', 0),
            'has_explanation': result.get('has_explanation', False),
            'explanation_quality_score': result.get('explanation_quality_score'),
            'response_time_ms': result.get('response_time_ms', 0),
            'tokens_used': result.get('tokens_used'),
            'estimated_cost': result.get('estimated_cost')
        }

    def _upsert_rule(self, session: Session, result: Dict[str, Any]):
        """Update or insert rule metadata."""
        rule_id = result['rule_id']
        rule = session.query(Rule).filter_by(rule_id=rule_id).first()

        if not rule:
            rule = Rule(
                rule_id=rule_id,
                description=result.get('rule_description'),
                severity=result.get('rule_severity'),
                category=result.get('rule_category'),
                migration_complexity=result.get('migration_complexity'),
                migration_pattern=result.get('migration_pattern'),
                source_url=result.get('source_url'),
                test_case_count=1
            )
            session.add(rule)
        else:
            rule.last_seen_at = datetime.now()
            rule.test_case_count += 1

    def get_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        session = self._get_session()
        try:
            run = session.query(EvaluationRun).filter_by(run_id=run_id).first()
            if run:
                return {
                    'run_id': run.run_id,
                    'name': run.name,
                    'test_suite_name': run.test_suite_name,
                    'test_suite_version': run.test_suite_version,
                    'started_at': run.started_at.isoformat() if run.started_at else None,
                    'completed_at': run.completed_at.isoformat() if run.completed_at else None,
                    'status': run.status,
                    'git_commit': run.git_commit,
                    'git_branch': run.git_branch
                }
            return None
        finally:
            session.close()

    def get_test_results(self, run_id: str, **filters) -> List[Dict[str, Any]]:
        session = self._get_session()
        try:
            query = session.query(TestResult).filter_by(run_id=run_id)

            # Apply filters
            for key, value in filters.items():
                if hasattr(TestResult, key):
                    query = query.filter(getattr(TestResult, key) == value)

            results = []
            for result in query.all():
                results.append({
                    'test_case_id': result.test_case_id,
                    'rule_id': result.rule_id,
                    'model_name': result.model_name,
                    'passed': result.passed,
                    'failure_reason': result.failure_reason,
                    'response_time_ms': result.response_time_ms,
                    'estimated_cost': result.estimated_cost,
                    'executed_at': result.executed_at.isoformat() if result.executed_at else None
                })
            return results
        finally:
            session.close()

    def get_rule_performance(self, rule_id: str, model_name: Optional[str] = None,
                           time_period: str = 'all') -> Dict[str, Any]:
        session = self._get_session()
        try:
            query = session.query(TestResult).filter_by(rule_id=rule_id)

            if model_name:
                query = query.filter_by(model_name=model_name)

            # Apply time period filter
            if time_period != 'all':
                # TODO: Implement time period filtering
                pass

            results = query.all()

            if not results:
                return {'rule_id': rule_id, 'total_tests': 0}

            total = len(results)
            passed = sum(1 for r in results if r.passed)

            return {
                'rule_id': rule_id,
                'model_name': model_name,
                'total_tests': total,
                'passed_tests': passed,
                'pass_rate': passed / total if total > 0 else 0,
                'avg_response_time_ms': sum(r.response_time_ms for r in results) / total,
                'avg_cost': sum(r.estimated_cost or 0 for r in results) / total,
            }
        finally:
            session.close()

    def close(self):
        self.engine.dispose()


class PostgreSQLBackend(SQLiteBackend):
    """PostgreSQL database backend."""

    def __init__(self, connection_string: str):
        """
        Initialize PostgreSQL backend.

        Args:
            connection_string: PostgreSQL connection string
                Example: "postgresql://user:password@localhost:5432/konveyor_iq"
        """
        self.connection_string = connection_string
        self.engine = create_engine(connection_string)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
