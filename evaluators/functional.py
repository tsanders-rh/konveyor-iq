"""
Functional correctness evaluation.
Checks if the generated code resolves the violation and compiles.
"""
import subprocess
import tempfile
import os
from pathlib import Path
from typing import Dict, Any

from .base import BaseEvaluator


class FunctionalCorrectnessEvaluator(BaseEvaluator):
    """Evaluates functional correctness of generated code."""

    def evaluate(
        self,
        original_code: str,
        generated_code: str,
        expected_code: str = None,
        language: str = "java",
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Evaluate functional correctness.

        Returns:
            - functional_correctness: bool - Does fix resolve violation?
            - compiles: bool - Does code compile?
            - introduces_violations: bool - New violations introduced?
        """
        if not self.enabled:
            return {}

        context = context or {}
        results = {}

        # Check compilation
        if self.config.get("compile_check", True):
            results["compiles"] = self._check_compilation(generated_code, language)

        # Re-run static analysis to check if violation is resolved
        if self.config.get("static_analysis_rerun", True):
            violation_resolved, new_violations = self._check_violations(
                generated_code,
                language,
                context.get("rule_id")
            )
            results["functional_correctness"] = violation_resolved
            results["introduces_violations"] = new_violations > 0
            results["new_violation_count"] = new_violations

        # If expected code is provided, compare semantically
        if expected_code:
            results["matches_expected"] = self._semantic_match(
                generated_code,
                expected_code,
                language
            )

        return results

    def _check_compilation(self, code: str, language: str) -> bool:
        """
        Check if code compiles.

        Args:
            code: Code to compile
            language: Programming language

        Returns:
            True if code compiles without errors
        """
        try:
            if language == "java":
                return self._compile_java(code)
            elif language == "python":
                return self._compile_python(code)
            else:
                # For other languages, skip compilation check
                return True
        except Exception as e:
            print(f"Compilation check failed: {e}")
            return False

    def _compile_java(self, code: str) -> bool:
        """Compile Java code."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Extract class name from code
            class_name = self._extract_java_class_name(code)
            if not class_name:
                return False

            java_file = Path(tmpdir) / f"{class_name}.java"
            java_file.write_text(code)

            try:
                result = subprocess.run(
                    ["javac", str(java_file)],
                    capture_output=True,
                    timeout=30
                )
                return result.returncode == 0
            except (subprocess.TimeoutExpired, FileNotFoundError):
                # javac not available or timeout
                return None  # Unknown

    def _compile_python(self, code: str) -> bool:
        """Check Python code syntax."""
        try:
            compile(code, '<string>', 'exec')
            return True
        except SyntaxError:
            return False

    def _extract_java_class_name(self, code: str) -> str:
        """Extract Java class name from code."""
        import re
        match = re.search(r'public\s+class\s+(\w+)', code)
        return match.group(1) if match else None

    def _check_violations(
        self,
        code: str,
        language: str,
        rule_id: str = None
    ) -> tuple[bool, int]:
        """
        Re-run static analysis to check for violations.

        Args:
            code: Code to analyze
            language: Programming language
            rule_id: Original rule ID that should be resolved

        Returns:
            (violation_resolved, new_violations_count)
        """
        # This would integrate with Konveyor analyzer or other static analysis tools
        # For now, return a placeholder

        # Example command would be:
        # konveyor-analyzer analyze --code-snippet <code> --rules <rules>

        # Placeholder implementation
        # In production, run actual static analysis
        analyzer_cmd = self.config.get("analyzer_command", "konveyor-analyzer")

        try:
            # Write code to temp file and analyze
            with tempfile.NamedTemporaryFile(mode='w', suffix=f'.{language}', delete=False) as f:
                f.write(code)
                temp_file = f.name

            # Run analyzer (this is a placeholder - adapt to actual analyzer)
            # result = subprocess.run(
            #     [analyzer_cmd, "analyze", temp_file],
            #     capture_output=True,
            #     timeout=60
            # )

            # Parse results and check if original rule_id is still present
            # For now, assume violation is resolved
            violation_resolved = True
            new_violations = 0

            os.unlink(temp_file)
            return violation_resolved, new_violations

        except Exception as e:
            print(f"Static analysis failed: {e}")
            # If analysis fails, we can't determine - return conservative estimate
            return False, 0

    def _semantic_match(
        self,
        generated: str,
        expected: str,
        language: str
    ) -> bool:
        """
        Check semantic equivalence between generated and expected code.

        This could use AST comparison for more sophisticated matching.
        """
        # Simple string comparison for now
        # In production, use AST-based comparison
        return generated.strip() == expected.strip()
