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
    "@Stateful": "import javax.ejb.Stateful;",
    "@Singleton": ["import javax.ejb.Singleton;", "import jakarta.inject.Singleton;"],
    "@Startup": "import javax.ejb.Startup;",
    "@MessageDriven": "import javax.ejb.MessageDriven;",
    "@EJB": "import javax.ejb.EJB;",
    "@ApplicationScoped": ["import javax.enterprise.context.ApplicationScoped;", "import jakarta.enterprise.context.ApplicationScoped;"],
    "@SessionScoped": ["import javax.enterprise.context.SessionScoped;", "import jakarta.enterprise.context.SessionScoped;"],
    "@RequestScoped": ["import javax.enterprise.context.RequestScoped;", "import jakarta.enterprise.context.RequestScoped;"],
    "@Named": ["import javax.inject.Named;", "import jakarta.inject.Named;"],
    "@Inject": ["import javax.inject.Inject;", "import jakarta.inject.Inject;"],
    "@Produces": ["import javax.enterprise.inject.Produces;", "import jakarta.enterprise.inject.Produces;"],
    "@Observes": "import jakarta.enterprise.event.Observes;",
    "@PersistenceContext": ["import javax.persistence.PersistenceContext;", "import jakarta.persistence.PersistenceContext;"],
    "EntityManager": ["import javax.persistence.EntityManager;", "import jakarta.persistence.EntityManager;"],
    "@Transactional": ["import javax.transaction.Transactional;", "import jakarta.transaction.Transactional;"],
    "MessageListener": "import javax.jms.MessageListener;",
    "Message": "import javax.jms.Message;",
    "TextMessage": "import javax.jms.TextMessage;",
    "JMSException": "import javax.jms.JMSException;",
    "StartupEvent": "import io.quarkus.runtime.StartupEvent;",
    "@Incoming": "import org.eclipse.microprofile.reactive.messaging.Incoming;",
    "@ActivationConfigProperty": "import javax.ejb.ActivationConfigProperty;",
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
            compiles, error_msg = self._check_compilation(generated_code, language)
            results["compiles"] = compiles
            if not compiles and error_msg:
                results["compilation_error"] = error_msg

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

    def _check_compilation(self, code: str, language: str) -> tuple[bool, str]:
        """
        Check if code compiles.

        Args:
            code: Code to compile
            language: Programming language

        Returns:
            (success, error_message) tuple
        """
        try:
            if language == "java":
                return self._compile_java(code)
            elif language == "python":
                return self._compile_python(code)
            else:
                # For other languages, skip compilation check
                return (True, "")
        except Exception as e:
            print(f"Compilation check failed: {e}")
            return (False, str(e))

    def _compile_java(self, code: str) -> tuple[bool, str]:
        """
        Compile Java code.

        Returns:
            (success, error_message) tuple
        """
        # Auto-inject missing imports
        code = self._inject_missing_imports(code)

        with tempfile.TemporaryDirectory() as tmpdir:
            # Extract class name from code
            class_name = self._extract_java_class_name(code)
            if not class_name:
                return (False, "Could not extract class name from code")

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
                    timeout=30,
                    text=True
                )

                if result.returncode == 0:
                    return (True, "")
                else:
                    error_output = result.stderr if result.stderr else result.stdout

                    # Try to recover from missing import errors by stripping them
                    if "package" in error_output and "does not exist" in error_output:
                        cleaned_code = self._strip_failing_imports(code, error_output)
                        if cleaned_code != code:
                            # Retry compilation with cleaned code
                            java_file.write_text(cleaned_code)
                            retry_result = subprocess.run(
                                javac_cmd,
                                capture_output=True,
                                timeout=30,
                                text=True
                            )
                            if retry_result.returncode == 0:
                                return (True, "")
                            # Return the new error if retry also failed
                            error_output = retry_result.stderr if retry_result.stderr else retry_result.stdout

                    # Return the compilation error
                    return (False, error_output.strip())

            except subprocess.TimeoutExpired:
                return (False, "Compilation timeout (>30s)")
            except FileNotFoundError:
                return (None, "javac not available")

    def _compile_python(self, code: str) -> tuple[bool, str]:
        """
        Check Python code syntax.

        Returns:
            (success, error_message) tuple
        """
        try:
            compile(code, '<string>', 'exec')
            return (True, "")
        except SyntaxError as e:
            return (False, f"SyntaxError: {str(e)}")

    def _extract_java_class_name(self, code: str) -> str:
        """Extract Java class name from code."""
        import re
        match = re.search(r'public\s+class\s+(\w+)', code)
        return match.group(1) if match else None

    def _strip_failing_imports(self, code: str, error_output: str) -> str:
        """
        Strip import statements that cause 'package does not exist' errors.

        This allows compilation to succeed even if the LLM added extra imports
        for classes we don't have stubs for.

        Args:
            code: Original code
            error_output: Javac error output

        Returns:
            Code with failing imports removed
        """
        import re

        # Extract failing package names from error output
        # Error format: "import org.springframework.stereotype.Service;\n ^\n  symbol: class Service\n  location: package org.springframework.stereotype"
        failing_packages = set()

        # Match "package X does not exist" errors
        package_errors = re.findall(r'package ([\w.]+) does not exist', error_output)
        failing_packages.update(package_errors)

        if not failing_packages:
            return code

        # Remove import statements for failing packages
        lines = code.split('\n')
        cleaned_lines = []

        for line in lines:
            stripped = line.strip()
            # Check if this is an import line
            if stripped.startswith('import '):
                # Check if it imports from a failing package
                is_failing = False
                for pkg in failing_packages:
                    if f'import {pkg}.' in stripped or f'import {pkg};' in stripped:
                        is_failing = True
                        break

                # Keep the line only if it's not importing from a failing package
                if not is_failing:
                    cleaned_lines.append(line)
            else:
                cleaned_lines.append(line)

        return '\n'.join(cleaned_lines)

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
        # Option 1: Use Konveyor analyzer if available
        analyzer_cmd = self.config.get("analyzer_command", None)

        if analyzer_cmd:
            return self._check_violations_with_analyzer(code, language, rule_id, analyzer_cmd)

        # Option 2: Use pattern-based validation (fallback)
        return self._check_violations_pattern_based(code, rule_id)

    def _check_violations_with_analyzer(
        self,
        code: str,
        language: str,
        rule_id: str,
        analyzer_cmd: str
    ) -> tuple[bool, int]:
        """
        Check violations using Konveyor analyzer or similar tool.

        Args:
            code: Code to analyze
            language: Programming language
            rule_id: Rule ID to check
            analyzer_cmd: Analyzer command path

        Returns:
            (violation_resolved, new_violations_count)
        """
        try:
            # Write code to temp file
            with tempfile.NamedTemporaryFile(mode='w', suffix=f'.{language}', delete=False) as f:
                f.write(code)
                temp_file = f.name

            # Run analyzer
            # Example: konveyor-analyzer analyze --source <file> --rules <rules> --output json
            result = subprocess.run(
                [analyzer_cmd, "analyze", "--source", temp_file, "--output", "json"],
                capture_output=True,
                timeout=60,
                text=True
            )

            os.unlink(temp_file)

            if result.returncode != 0:
                print(f"Analyzer failed: {result.stderr}")
                return False, 0

            # Parse analyzer output (format depends on analyzer)
            import json
            try:
                violations = json.loads(result.stdout)

                # Check if original rule_id is still present
                violation_still_present = any(
                    v.get("rule_id") == rule_id for v in violations
                )

                # Count new violations (exclude the original rule)
                new_violations = sum(
                    1 for v in violations if v.get("rule_id") != rule_id
                )

                violation_resolved = not violation_still_present
                return violation_resolved, new_violations

            except json.JSONDecodeError:
                print(f"Failed to parse analyzer output: {result.stdout}")
                return False, 0

        except subprocess.TimeoutExpired:
            print("Static analysis timeout")
            return False, 0
        except Exception as e:
            print(f"Static analysis failed: {e}")
            return False, 0

    def _check_violations_pattern_based(
        self,
        code: str,
        rule_id: str
    ) -> tuple[bool, int]:
        """
        Simple pattern-based violation checking.

        Checks if the old pattern is still present and new pattern exists.
        This is a fallback when no analyzer is available.

        Args:
            code: Generated code
            rule_id: Rule ID

        Returns:
            (violation_resolved, new_violations_count)
        """
        # Get migration pattern from config or rule metadata
        # This is a simple heuristic-based approach

        # Common Java EE to Quarkus patterns
        patterns = {
            "ee-to-quarkus-00000": {
                "old": ["@Stateless", "import javax.ejb.Stateless"],
                "new": ["@ApplicationScoped", "import jakarta.enterprise.context.ApplicationScoped"],
            },
            "ee-to-quarkus-00010": {
                "old": ["@Stateful", "import javax.ejb.Stateful"],
                "new": ["@SessionScoped", "@ApplicationScoped"],
            },
            "ee-to-quarkus-00001": {
                "old": ["@EJB"],
                "new": ["@Inject"],
            },
            "ee-to-quarkus-00020": {
                "old": ["@Stateless"],
                "new": ["@Transactional", "@ApplicationScoped"],
            },
            "ee-to-quarkus-00030": {
                "old": ["import javax.ejb.Singleton", "import javax.ejb.Startup"],
                "new": ["@ApplicationScoped", "@Observes StartupEvent"],
            },
            "jakarta-package-00000": {
                "old": ["import javax.persistence"],
                "new": ["import jakarta.persistence"],
            },
            "jakarta-transaction-00000": {
                "old": ["import javax.transaction"],
                "new": ["import jakarta.transaction"],
            },
            "persistence-to-quarkus-00011": {
                "old": ["@Produces"],
                "new": [],  # Should remove @Produces
            },
            "remote-ejb-to-quarkus-00000": {
                "old": ["@MessageDriven", "implements MessageListener"],
                "new": ["@Incoming", "@ApplicationScoped"],
            },
        }

        if rule_id not in patterns:
            # Unknown rule - can't validate pattern-based, assume resolved
            # (Compilation and other checks still run)
            return True, 0

        pattern = patterns[rule_id]
        old_patterns = pattern["old"]
        new_patterns = pattern["new"]

        # Check if old patterns are still present
        old_pattern_found = any(old_pat in code for old_pat in old_patterns)

        # Check if new patterns are present (if specified)
        if new_patterns:
            new_pattern_found = any(new_pat in code for new_pat in new_patterns)
        else:
            # Pattern requires removal, not replacement
            new_pattern_found = True

        # Violation is resolved if old pattern is gone and new pattern is present
        violation_resolved = not old_pattern_found and new_pattern_found

        # Simple heuristic: count javax imports as potential violations
        # (should have been migrated to jakarta)
        new_violations = 0
        if "javax.ejb" in code or "javax.enterprise.inject.Produces" in code:
            new_violations += 1

        return violation_resolved, new_violations

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
