"""
Security evaluation.
Checks for security vulnerabilities and unsafe patterns.
"""
import subprocess
import tempfile
import json
from typing import Dict, Any

from .base import BaseEvaluator


class SecurityEvaluator(BaseEvaluator):
    """Evaluates security aspects of generated code."""

    def evaluate(
        self,
        original_code: str,
        generated_code: str,
        expected_code: str = None,
        language: str = "java",
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Evaluate security.

        Returns:
            - security_issues: int - Total security issues found
            - high_severity_security: int - High severity issues
            - issue_types: list - Types of security issues
        """
        if not self.enabled:
            return {}

        results = {
            "security_issues": 0,
            "high_severity_security": 0,
            "issue_types": []
        }

        tools = self.config.get("tools", [])

        if language == "python" and "bandit" in tools:
            bandit_results = self._run_bandit(generated_code)
            if bandit_results:
                results.update(bandit_results)

        elif language == "java":
            # Could integrate SpotBugs, Find Security Bugs, etc.
            pass

        return results

    def _run_bandit(self, code: str) -> Dict[str, Any]:
        """
        Run Bandit security linter for Python.

        Returns:
            Dictionary with security metrics
        """
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name

            result = subprocess.run(
                ["bandit", "-f", "json", temp_file],
                capture_output=True,
                timeout=30
            )

            if result.stdout:
                data = json.loads(result.stdout)
                results = data.get('results', [])

                high_severity = sum(
                    1 for r in results
                    if r.get('issue_severity') == 'HIGH'
                )

                issue_types = [r.get('test_id') for r in results]

                return {
                    "security_issues": len(results),
                    "high_severity_security": high_severity,
                    "issue_types": issue_types
                }

            return None

        except Exception as e:
            print(f"Bandit failed: {e}")
            return None
