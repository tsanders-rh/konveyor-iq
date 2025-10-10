"""
Code quality evaluation.
Measures readability, style, and complexity metrics.
"""
import subprocess
import tempfile
import json
from pathlib import Path
from typing import Dict, Any

from .base import BaseEvaluator


class CodeQualityEvaluator(BaseEvaluator):
    """Evaluates code quality metrics."""

    def evaluate(
        self,
        original_code: str,
        generated_code: str,
        expected_code: str = None,
        language: str = "java",
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Evaluate code quality.

        Returns:
            - pylint_score: float (0-10)
            - cyclomatic_complexity: int
            - maintainability_index: float (0-100)
            - style_violations: int
        """
        if not self.enabled:
            return {}

        results = {}
        tools = self.config.get("tools", [])

        if language == "python":
            if "pylint" in tools:
                results["pylint_score"] = self._run_pylint(generated_code)

            if "radon" in tools:
                complexity = self._run_radon_complexity(generated_code)
                maintainability = self._run_radon_maintainability(generated_code)
                results["cyclomatic_complexity"] = complexity
                results["maintainability_index"] = maintainability

            if "black" in tools:
                results["style_violations"] = self._check_black(generated_code)

        elif language == "java":
            # Could integrate checkstyle, PMD, etc.
            results["cyclomatic_complexity"] = self._analyze_java_complexity(generated_code)

        return results

    def _run_pylint(self, code: str) -> float:
        """
        Run pylint and return score.

        Returns:
            Score from 0-10
        """
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name

            result = subprocess.run(
                ["pylint", "--output-format=json", temp_file],
                capture_output=True,
                timeout=30
            )

            # Parse JSON output
            if result.stdout:
                data = json.loads(result.stdout)
                # Pylint score is typically in stderr as "Your code has been rated at X/10"
                # Or we can calculate from messages
                # For simplicity, extract from stderr
                pass

            # Parse score from stderr
            stderr = result.stderr.decode()
            import re
            match = re.search(r'rated at ([\d.]+)/10', stderr)
            if match:
                return float(match.group(1))

            return None

        except Exception as e:
            print(f"Pylint failed: {e}")
            return None

    def _run_radon_complexity(self, code: str) -> int:
        """
        Calculate cyclomatic complexity using radon.

        Returns:
            Average cyclomatic complexity
        """
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name

            result = subprocess.run(
                ["radon", "cc", "-j", temp_file],
                capture_output=True,
                timeout=30
            )

            if result.stdout:
                data = json.loads(result.stdout)
                # Calculate average complexity
                complexities = []
                for file_data in data.values():
                    for func in file_data:
                        complexities.append(func.get('complexity', 0))

                if complexities:
                    return int(sum(complexities) / len(complexities))

            return None

        except Exception as e:
            print(f"Radon complexity failed: {e}")
            return None

    def _run_radon_maintainability(self, code: str) -> float:
        """
        Calculate maintainability index using radon.

        Returns:
            Maintainability index (0-100)
        """
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name

            result = subprocess.run(
                ["radon", "mi", "-j", temp_file],
                capture_output=True,
                timeout=30
            )

            if result.stdout:
                data = json.loads(result.stdout)
                # Extract MI score
                for file_data in data.values():
                    return file_data.get('mi', None)

            return None

        except Exception as e:
            print(f"Radon maintainability failed: {e}")
            return None

    def _check_black(self, code: str) -> int:
        """
        Check code formatting with black.

        Returns:
            Number of style violations (0 if properly formatted)
        """
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name

            result = subprocess.run(
                ["black", "--check", "--diff", temp_file],
                capture_output=True,
                timeout=30
            )

            # black returns 0 if no changes needed, 1 if reformatting needed
            return 0 if result.returncode == 0 else 1

        except Exception as e:
            print(f"Black check failed: {e}")
            return None

    def _analyze_java_complexity(self, code: str) -> int:
        """
        Analyze Java code complexity.
        This is a placeholder - integrate with actual Java analysis tools.
        """
        # Could use PMD, Checkstyle, or other Java tools
        # For now, simple heuristic based on control structures
        control_keywords = ['if', 'for', 'while', 'case', 'catch']
        complexity = 1  # Base complexity

        for keyword in control_keywords:
            complexity += code.count(keyword)

        return complexity
