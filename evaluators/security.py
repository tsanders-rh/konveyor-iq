"""
Security evaluation.
Checks for security vulnerabilities and unsafe patterns.
"""
import subprocess
import tempfile
import json
import re
import os
from typing import Dict, Any, List

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
            - issues: list - Detailed issue information
        """
        if not self.enabled:
            return {}

        results = {
            "security_issues": 0,
            "high_severity_security": 0,
            "issue_types": [],
            "issues": []
        }

        tools = self.config.get("tools", [])

        if language == "python" and "bandit" in tools:
            bandit_results = self._run_bandit(generated_code)
            if bandit_results:
                results.update(bandit_results)

        elif language == "java":
            # Try Semgrep first (if configured and available)
            if "semgrep" in tools:
                semgrep_results = self._run_semgrep(generated_code)
                if semgrep_results:
                    results.update(semgrep_results)
                    return results

            # Fallback to pattern-based security checks
            pattern_results = self._check_java_security_patterns(
                original_code, generated_code, context
            )
            if pattern_results:
                results.update(pattern_results)

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

    def _run_semgrep(self, code: str) -> Dict[str, Any]:
        """
        Run Semgrep security analysis for Java.

        Semgrep is a fast, customizable static analysis tool with
        excellent Java security rules.

        Returns:
            Dictionary with security metrics
        """
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.java', delete=False) as f:
                f.write(code)
                temp_file = f.name

            # Run with Java security ruleset
            result = subprocess.run(
                [
                    "semgrep",
                    "--config", "p/java-security",  # Pre-built Java security rules
                    "--json",
                    temp_file
                ],
                capture_output=True,
                timeout=60,
                text=True
            )

            os.unlink(temp_file)

            if result.stdout:
                data = json.loads(result.stdout)
                results = data.get('results', [])

                # Count high severity issues
                high_severity = sum(
                    1 for r in results
                    if r.get('extra', {}).get('severity') in ['ERROR', 'WARNING']
                )

                issues = [
                    {
                        "type": r.get('check_id', 'UNKNOWN'),
                        "severity": r.get('extra', {}).get('severity', 'INFO'),
                        "description": r.get('extra', {}).get('message', 'No description'),
                        "line": r.get('start', {}).get('line', 0)
                    }
                    for r in results
                ]

                return {
                    "security_issues": len(results),
                    "high_severity_security": high_severity,
                    "issue_types": [r.get('check_id') for r in results],
                    "issues": issues
                }

            return None

        except FileNotFoundError:
            # Semgrep not installed
            return None
        except Exception as e:
            print(f"Semgrep failed: {e}")
            return None

    def _check_java_security_patterns(
        self,
        original_code: str,
        generated_code: str,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Pattern-based security checks for Java code.

        Checks for common security anti-patterns and migration-specific
        security issues in Java EE → Quarkus migrations.

        Args:
            original_code: Original code before migration
            generated_code: Generated code after migration
            context: Additional context (rule_id, etc.)

        Returns:
            Dictionary with security metrics
        """
        security_issues = []

        # SQL Injection patterns
        # Check for string concatenation in SQL queries
        if re.search(r'(executeQuery|executeUpdate|execute)\s*\(\s*[^)]*\+', generated_code):
            security_issues.append({
                "type": "SQL_INJECTION",
                "severity": "HIGH",
                "description": "Potential SQL injection via string concatenation in execute*()"
            })

        # Check for concatenated query strings
        if re.search(r'(SELECT|INSERT|UPDATE|DELETE).*["\'].*\+.*["\']', generated_code, re.IGNORECASE):
            security_issues.append({
                "type": "SQL_INJECTION",
                "severity": "HIGH",
                "description": "Potential SQL injection via string concatenation in SQL query"
            })

        if re.search(r'createQuery\s*\(\s*[^)]*\+', generated_code):
            security_issues.append({
                "type": "SQL_INJECTION",
                "severity": "HIGH",
                "description": "Potential SQL injection via string concatenation in createQuery()"
            })

        # Hardcoded credentials
        if re.search(r'(password|secret|apikey|api_key|token)\s*=\s*["\'][^"\']+["\']', generated_code, re.IGNORECASE):
            security_issues.append({
                "type": "HARDCODED_CREDENTIALS",
                "severity": "HIGH",
                "description": "Hardcoded credentials detected in code"
            })

        # XXE vulnerabilities
        if 'DocumentBuilderFactory' in generated_code:
            if not re.search(r'setFeature.*FEATURE_SECURE_PROCESSING|disallow-doctype-decl', generated_code):
                security_issues.append({
                    "type": "XXE_VULNERABILITY",
                    "severity": "HIGH",
                    "description": "XML parser without XXE protection (missing setFeature configuration)"
                })

        # Insecure random
        if 'java.util.Random' in generated_code and 'SecureRandom' not in generated_code:
            if re.search(r'(token|password|key|salt|nonce)', generated_code, re.IGNORECASE):
                security_issues.append({
                    "type": "WEAK_RANDOM",
                    "severity": "HIGH",
                    "description": "Using weak Random for security-sensitive value instead of SecureRandom"
                })

        # Path traversal
        if re.search(r'new\s+File\s*\([^)]*\+[^)]*\)', generated_code):
            security_issues.append({
                "type": "PATH_TRAVERSAL",
                "severity": "HIGH",
                "description": "Potential path traversal via string concatenation in File constructor"
            })

        # Insecure deserialization
        if 'ObjectInputStream' in generated_code and 'readObject' in generated_code:
            if 'ValidatingObjectInputStream' not in generated_code:
                security_issues.append({
                    "type": "INSECURE_DESERIALIZATION",
                    "severity": "HIGH",
                    "description": "Unsafe deserialization without validation"
                })

        # === Migration-specific security checks ===

        # Missing @RolesAllowed after removing EJB security
        if original_code and '@RolesAllowed' in original_code:
            if '@RolesAllowed' not in generated_code and '@PermitAll' not in generated_code:
                security_issues.append({
                    "type": "MISSING_AUTHORIZATION",
                    "severity": "HIGH",
                    "description": "EJB @RolesAllowed security annotation lost in migration"
                })

        # Unprotected JAX-RS endpoints
        if '@Path' in generated_code or '@GET' in generated_code or '@POST' in generated_code:
            # Check if endpoint has any authorization
            if not any(annotation in generated_code for annotation in
                      ['@RolesAllowed', '@PermitAll', '@DenyAll', '@Authenticated']):
                security_issues.append({
                    "type": "UNPROTECTED_ENDPOINT",
                    "severity": "MEDIUM",
                    "description": "JAX-RS endpoint without authorization annotation"
                })

        # Missing @Transactional on methods that need it
        if original_code and '@TransactionAttribute' in original_code:
            if '@Transactional' not in generated_code:
                # Check if there are persistence operations
                if any(op in generated_code for op in ['persist(', 'merge(', 'remove(']):
                    security_issues.append({
                        "type": "MISSING_TRANSACTION",
                        "severity": "MEDIUM",
                        "description": "Persistence operations without @Transactional (data integrity risk)"
                    })

        # CSRF protection for state-changing endpoints
        if '@POST' in generated_code or '@PUT' in generated_code or '@DELETE' in generated_code:
            # Quarkus has built-in CSRF protection, but worth noting if disabled
            if 'csrf' in generated_code.lower() and 'disabled' in generated_code.lower():
                security_issues.append({
                    "type": "CSRF_DISABLED",
                    "severity": "MEDIUM",
                    "description": "CSRF protection appears to be disabled for state-changing endpoint"
                })

        # Insecure HTTP client configuration
        if 'RestClientBuilder' in generated_code or 'ClientBuilder' in generated_code:
            if 'hostnameVerifier' in generated_code.lower() or 'sslcontext' in generated_code.lower():
                security_issues.append({
                    "type": "INSECURE_HTTP_CLIENT",
                    "severity": "MEDIUM",
                    "description": "Custom SSL configuration detected - verify certificate validation is not disabled"
                })

        # Aggregate results
        high_severity = sum(1 for issue in security_issues if issue["severity"] == "HIGH")

        return {
            "security_issues": len(security_issues),
            "high_severity_security": high_severity,
            "issue_types": [issue["type"] for issue in security_issues],
            "issues": security_issues
        }
