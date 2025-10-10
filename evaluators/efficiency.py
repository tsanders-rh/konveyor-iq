"""
Efficiency evaluation.
Measures runtime performance and resource usage.
"""
import subprocess
import tempfile
import time
import psutil
from typing import Dict, Any

from .base import BaseEvaluator


class EfficiencyEvaluator(BaseEvaluator):
    """Evaluates runtime efficiency of generated code."""

    def evaluate(
        self,
        original_code: str,
        generated_code: str,
        expected_code: str = None,
        language: str = "java",
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Evaluate efficiency.

        Returns:
            - execution_time_ms: float
            - memory_usage_mb: float
        """
        if not self.enabled:
            return {}

        context = context or {}
        test_code = context.get("test_code")

        if not test_code:
            # Can't measure efficiency without test code
            return {}

        results = {}

        try:
            if language == "python":
                exec_time, memory = self._run_python_benchmark(
                    generated_code,
                    test_code
                )
                results["execution_time_ms"] = exec_time
                results["memory_usage_mb"] = memory

            elif language == "java":
                # Would need to compile and run Java code
                pass

        except Exception as e:
            print(f"Efficiency evaluation failed: {e}")

        return results

    def _run_python_benchmark(
        self,
        code: str,
        test_code: str
    ) -> tuple[float, float]:
        """
        Run Python code and measure performance.

        Args:
            code: Code to benchmark
            test_code: Test code that exercises the functions

        Returns:
            (execution_time_ms, memory_usage_mb)
        """
        full_code = f"{code}\n\n{test_code}"

        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(full_code)
            temp_file = f.name

        # Measure execution time and memory
        start_time = time.time()
        process = psutil.Popen(
            ["python", temp_file],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        # Monitor memory usage
        max_memory = 0
        try:
            while process.poll() is None:
                try:
                    mem_info = process.memory_info()
                    max_memory = max(max_memory, mem_info.rss)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    break
                time.sleep(0.01)

            process.wait(timeout=self.config.get("timeout_seconds", 30))
        except subprocess.TimeoutExpired:
            process.kill()
            raise

        end_time = time.time()

        execution_time_ms = (end_time - start_time) * 1000
        memory_usage_mb = max_memory / (1024 * 1024)

        return execution_time_ms, memory_usage_mb
