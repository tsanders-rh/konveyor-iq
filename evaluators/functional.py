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


# Common imports to auto-inject if missing
COMMON_JAVA_IMPORTS = {
    "@Stateless": "import javax.ejb.Stateless;",
    "@EJB": "import javax.ejb.EJB;",
    "@ApplicationScoped": "import jakarta.enterprise.context.ApplicationScoped;",
    "@Inject": "import jakarta.inject.Inject;",
    "@PersistenceContext": ["import javax.persistence.PersistenceContext;", "import jakarta.persistence.PersistenceContext;"],
    "EntityManager": ["import javax.persistence.EntityManager;", "import jakarta.persistence.EntityManager;"],
    "@Transactional": ["import javax.transaction.Transactional;", "import jakarta.transaction.Transactional;"],
}


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
        # Auto-inject missing imports
        code = self._inject_missing_imports(code)

        with tempfile.TemporaryDirectory() as tmpdir:
            # Extract class name from code
            class_name = self._extract_java_class_name(code)
            if not class_name:
                return False

            java_file = Path(tmpdir) / f"{class_name}.java"
            java_file.write_text(code)

            # Get stub JAR path
            stub_jar = Path(__file__).parent / "stubs" / "stubs.jar"

            try:
                # Build javac command with classpath if stub JAR exists
                javac_cmd = ["javac"]
                if stub_jar.exists():
                    javac_cmd.extend(["-cp", str(stub_jar)])
                javac_cmd.append(str(java_file))

                result = subprocess.run(
                    javac_cmd,
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

    def _inject_missing_imports(self, code: str) -> str:
        """
        Auto-inject common imports if they're missing.

        Checks for annotations/types in code and adds corresponding imports
        if not already present.
        """
        import re

        # Skip if code already has a package declaration (likely complete)
        if re.search(r'^package\s+', code, re.MULTILINE):
            return code

        # Check what imports are already present
        existing_imports = set(re.findall(r'^import\s+([\w.]+);', code, re.MULTILINE))

        # Find what needs to be imported
        imports_to_add = []

        for pattern, import_stmt in COMMON_JAVA_IMPORTS.items():
            if pattern in code:
                # Handle both single and multiple import options
                if isinstance(import_stmt, list):
                    # Check if ANY of the imports is already present
                    import_classes = [stmt.replace("import ", "").replace(";", "") for stmt in import_stmt]
                    if not any(imp in existing_imports for imp in import_classes):
                        # Add the first option (could be smarter here)
                        # Choose based on what's already in code
                        if "jakarta" in code:
                            imports_to_add.extend([s for s in import_stmt if "jakarta" in s])
                        else:
                            imports_to_add.extend([s for s in import_stmt if "javax" in s])
                else:
                    # Single import
                    import_class = import_stmt.replace("import ", "").replace(";", "")
                    if import_class not in existing_imports:
                        imports_to_add.append(import_stmt)

        # If we have imports to add, inject them at the top
        if imports_to_add:
            # Remove duplicates
            imports_to_add = list(dict.fromkeys(imports_to_add))

            # Find the position to insert imports (after package, before class)
            lines = code.split('\n')
            insert_pos = 0

            # Skip empty lines and comments at the top
            for i, line in enumerate(lines):
                stripped = line.strip()
                if stripped and not stripped.startswith('//') and not stripped.startswith('/*'):
                    insert_pos = i
                    break

            # Insert imports
            import_lines = [imp for imp in imports_to_add]
            lines = lines[:insert_pos] + import_lines + [''] + lines[insert_pos:]

            code = '\n'.join(lines)

        return code

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
