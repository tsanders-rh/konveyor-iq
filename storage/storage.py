"""
Main storage interface and factory.
"""
from typing import Dict, Any, Optional
from .backend import StorageBackend, FileBackend, SQLiteBackend, PostgreSQLBackend


class Storage:
    """
    Main storage interface for Konveyor IQ.

    Delegates to specific backend implementations.
    """

    def __init__(self, backend: StorageBackend):
        self.backend = backend

    def create_run(self, **kwargs) -> str:
        """Create a new evaluation run."""
        return self.backend.create_run(**kwargs)

    def update_run(self, run_id: str, **kwargs):
        """Update an existing run."""
        self.backend.update_run(run_id, **kwargs)

    def save_test_result(self, result: Dict[str, Any]):
        """Save a single test result."""
        self.backend.save_test_result(result)

    def save_test_results_batch(self, results: list):
        """Save multiple test results efficiently."""
        self.backend.save_test_results_batch(results)

    def get_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Get run by ID."""
        return self.backend.get_run(run_id)

    def get_test_results(self, run_id: str, **filters):
        """Get test results for a run with optional filters."""
        return self.backend.get_test_results(run_id, **filters)

    def get_rule_performance(self, rule_id: str, model_name: Optional[str] = None,
                           time_period: str = 'all') -> Dict[str, Any]:
        """Get performance metrics for a rule."""
        return self.backend.get_rule_performance(rule_id, model_name, time_period)

    def close(self):
        """Clean up resources."""
        self.backend.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def get_storage(config: Dict[str, Any]) -> Storage:
    """
    Factory function to create storage instance from config.

    Args:
        config: Storage configuration dict with keys:
            - type: 'file', 'sqlite', or 'postgresql'
            - path: For file/sqlite backends
            - connection_string: For postgresql backend

    Returns:
        Storage instance with appropriate backend
    """
    storage_type = config.get('type', 'file')

    if storage_type == 'file':
        base_dir = config.get('path', 'results')
        backend = FileBackend(base_dir)

    elif storage_type == 'sqlite':
        db_path = config.get('path', 'konveyor_iq.db')
        backend = SQLiteBackend(db_path)

    elif storage_type == 'postgresql':
        connection_string = config.get('connection_string')
        if not connection_string:
            raise ValueError("PostgreSQL backend requires 'connection_string' in config")
        backend = PostgreSQLBackend(connection_string)

    else:
        raise ValueError(f"Unknown storage type: {storage_type}")

    return Storage(backend)
