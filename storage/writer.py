"""
Database writer utility for storing evaluation results.
"""
import hashlib
from datetime import datetime
from typing import Dict, Any, List, Optional
from uuid import uuid4

from .storage import Storage, get_storage


class DatabaseWriter:
    """
    Helper class to write evaluation results to database.

    Usage:
        writer = DatabaseWriter(storage_config)
        run_id = writer.start_run(name="Test Run", test_suite_name="quarkus")

        for result in results:
            writer.write_result(run_id, result)

        writer.complete_run(run_id)
        writer.close()
    """

    def __init__(self, storage_config: Dict[str, Any]):
        """
        Initialize database writer.

        Args:
            storage_config: Storage configuration from config.yaml
        """
        self.storage = get_storage(storage_config)
        self.current_run_id = None

    def start_run(
        self,
        name: Optional[str] = None,
        test_suite_name: str = "default",
        test_suite_version: str = "1.0.0",
        config_snapshot: Optional[str] = None,
        git_commit: Optional[str] = None,
        git_branch: Optional[str] = None
    ) -> str:
        """
        Start a new evaluation run.

        Args:
            name: Optional run name
            test_suite_name: Name of test suite
            test_suite_version: Version of test suite
            config_snapshot: JSON snapshot of config
            git_commit: Git commit SHA
            git_branch: Git branch name

        Returns:
            run_id
        """
        run_id = str(uuid4())

        self.storage.create_run(
            run_id=run_id,
            name=name,
            test_suite_name=test_suite_name,
            test_suite_version=test_suite_version,
            started_at=datetime.now(),
            status='running',
            config_snapshot=config_snapshot,
            git_commit=git_commit,
            git_branch=git_branch
        )

        self.current_run_id = run_id
        return run_id

    def complete_run(self, run_id: str, status: str = 'completed'):
        """
        Mark run as complete.

        Args:
            run_id: Run identifier
            status: 'completed' or 'failed'
        """
        self.storage.update_run(
            run_id=run_id,
            completed_at=datetime.now(),
            status=status
        )

    def write_result(self, run_id: str, result: Dict[str, Any]):
        """
        Write a single test result to database.

        Args:
            run_id: Run identifier
            result: EvaluationResult dictionary
        """
        # Extract metrics from nested structure
        metrics = result.get('metrics', {})

        # Compute prompt hash for deduplication
        prompt_hash = None
        if result.get('raw_response'):
            prompt_hash = hashlib.sha256(
                result.get('raw_response', '').encode()
            ).hexdigest()[:16]

        db_result = {
            'run_id': run_id,
            'test_case_id': result.get('test_case_id'),
            'rule_id': result.get('rule_id'),
            'model_name': result.get('model_name'),
            'executed_at': datetime.fromisoformat(result['timestamp']) if result.get('timestamp') else datetime.now(),
            'passed': result.get('passed', False),
            'failure_reason': result.get('failure_reason'),

            # LLM output
            'generated_code': result.get('generated_code'),
            'generated_explanation': result.get('generated_explanation'),
            'raw_response': result.get('raw_response'),

            # Prompt tracking
            'prompt_source': result.get('prompt_source'),
            'prompt_hash': prompt_hash,

            # Correctness metrics
            'functional_correctness': metrics.get('functional_correctness'),
            'compiles': metrics.get('compiles'),
            'introduces_violations': metrics.get('introduces_violations', False),

            # Quality metrics
            'pylint_score': metrics.get('pylint_score'),
            'cyclomatic_complexity': metrics.get('cyclomatic_complexity'),
            'maintainability_index': metrics.get('maintainability_index'),
            'style_violations': metrics.get('style_violations', 0),

            # Security metrics
            'security_issues': metrics.get('security_issues', 0),
            'high_severity_security': metrics.get('high_severity_security', 0),

            # Explainability
            'has_explanation': metrics.get('has_explanation', False),
            'explanation_quality_score': metrics.get('explanation_quality_score'),

            # Performance
            'response_time_ms': metrics.get('response_time_ms', 0),
            'tokens_used': metrics.get('tokens_used'),
            'estimated_cost': result.get('estimated_cost'),

            # Rule metadata (for caching in rules table)
            'rule_description': result.get('rule_description'),
            'rule_severity': result.get('rule_severity'),
            'rule_category': result.get('rule_category'),
            'migration_complexity': result.get('migration_complexity'),
        }

        self.storage.save_test_result(db_result)

    def write_results_batch(self, run_id: str, results: List[Dict[str, Any]]):
        """
        Write multiple results efficiently.

        Args:
            run_id: Run identifier
            results: List of EvaluationResult dictionaries
        """
        db_results = []
        for result in results:
            metrics = result.get('metrics', {})

            prompt_hash = None
            if result.get('raw_response'):
                prompt_hash = hashlib.sha256(
                    result.get('raw_response', '').encode()
                ).hexdigest()[:16]

            db_result = {
                'run_id': run_id,
                'test_case_id': result.get('test_case_id'),
                'rule_id': result.get('rule_id'),
                'model_name': result.get('model_name'),
                'executed_at': datetime.fromisoformat(result['timestamp']) if result.get('timestamp') else datetime.now(),
                'passed': result.get('passed', False),
                'failure_reason': result.get('failure_reason'),
                'generated_code': result.get('generated_code'),
                'generated_explanation': result.get('generated_explanation'),
                'raw_response': result.get('raw_response'),
                'prompt_source': result.get('prompt_source'),
                'prompt_hash': prompt_hash,
                'functional_correctness': metrics.get('functional_correctness'),
                'compiles': metrics.get('compiles'),
                'introduces_violations': metrics.get('introduces_violations', False),
                'pylint_score': metrics.get('pylint_score'),
                'cyclomatic_complexity': metrics.get('cyclomatic_complexity'),
                'maintainability_index': metrics.get('maintainability_index'),
                'style_violations': metrics.get('style_violations', 0),
                'security_issues': metrics.get('security_issues', 0),
                'high_severity_security': metrics.get('high_severity_security', 0),
                'has_explanation': metrics.get('has_explanation', False),
                'explanation_quality_score': metrics.get('explanation_quality_score'),
                'response_time_ms': metrics.get('response_time_ms', 0),
                'tokens_used': metrics.get('tokens_used'),
                'estimated_cost': result.get('estimated_cost'),
                'rule_description': result.get('rule_description'),
                'rule_severity': result.get('rule_severity'),
                'rule_category': result.get('rule_category'),
                'migration_complexity': result.get('migration_complexity'),
            }
            db_results.append(db_result)

        self.storage.save_test_results_batch(db_results)

    def close(self):
        """Clean up resources."""
        self.storage.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.current_run_id:
            status = 'failed' if exc_type else 'completed'
            self.complete_run(self.current_run_id, status)
        self.close()
