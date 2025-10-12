#!/usr/bin/env python3
"""
Main evaluation script for Konveyor AI.

Usage:
    python evaluate.py --benchmark benchmarks/test_cases/java-ee-quarkus-migration.yaml
    python evaluate.py --config config.yaml --benchmark benchmarks/test_cases/
    python evaluate.py --benchmark test.yaml --parallel 4  # Use 4 parallel workers
"""
import argparse
import yaml
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

from benchmarks.schema import TestSuite, EvaluationResult, EvaluationMetrics
from benchmarks.rule_fetcher import get_rule_fetcher
from models import OpenAIModel, AnthropicModel, GoogleModel
from evaluators import (
    FunctionalCorrectnessEvaluator,
    CodeQualityEvaluator,
    SecurityEvaluator,
    EfficiencyEvaluator,
    ExplainabilityEvaluator,
)
from reporters import HTMLReporter, MarkdownReporter


class EvaluationEngine:
    """Main evaluation engine."""

    def __init__(self, config: Dict[str, Any], max_workers: int = 1, limit: int = None):
        """
        Initialize evaluation engine.

        Args:
            config: Configuration dictionary
            max_workers: Maximum number of parallel workers (1 = sequential)
            limit: Maximum number of test cases to evaluate (None = all)
        """
        self.config = config
        self.max_workers = max_workers
        self.limit = limit

        # Initialize models
        self.models = self._initialize_models()

        # Initialize evaluators
        self.evaluators = self._initialize_evaluators()

        # Load migration guidance from config
        self.migration_guidance = self._load_migration_guidance()

    def _load_migration_guidance(self) -> List[Dict[str, Any]]:
        """Load migration guidance from config file."""
        config_path = Path(__file__).parent / "config" / "migration_guidance.yaml"

        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                return config.get('migrations', [])
        except FileNotFoundError:
            print(f"Warning: Migration guidance config not found at {config_path}")
            return []
        except Exception as e:
            print(f"Warning: Failed to load migration guidance: {e}")
            return []

    def _find_guidance(self, source: str, target: str) -> Dict[str, Any]:
        """Find matching guidance entry for source/target pair."""
        if not source and not target:
            return None

        # Try exact match first
        for entry in self.migration_guidance:
            if entry.get('source') == source and entry.get('target') == target:
                return entry

        # Try target-only match if no source specified
        if target and not source:
            for entry in self.migration_guidance:
                if entry.get('target') == target and entry.get('source') is None:
                    return entry

        # Try fallback (null source and target)
        for entry in self.migration_guidance:
            if entry.get('source') is None and entry.get('target') is None:
                return entry

        return None

    def _build_guidance_string(self, guidance: Dict[str, Any]) -> str:
        """Build migration guidance string from guidance entry (for {migration_guidance} placeholder)."""
        parts = []

        # Add base guidance
        base_guidance = guidance.get('base_guidance', '').strip()
        if base_guidance:
            parts.append(base_guidance)
            parts.append("")

        # Add specific patterns
        specific_patterns = guidance.get('specific_patterns', [])
        for pattern in specific_patterns:
            pattern_name = pattern.get('name', '')
            pattern_guidance = pattern.get('guidance', '').strip()
            if pattern_name and pattern_guidance:
                parts.append(f"{pattern_name}:")
                parts.append(pattern_guidance)
                parts.append("")

        # Remove trailing empty line
        while parts and parts[-1] == "":
            parts.pop()

        return "\n".join(parts) if parts else ""

    def _initialize_models(self) -> List[Any]:
        """Initialize LLM models from config."""
        models = []

        for model_config in self.config.get("models", []):
            provider = model_config.get("provider")
            name = model_config.get("name")

            # Expand environment variables in API keys
            if "api_key" in model_config:
                api_key = model_config["api_key"]
                if api_key.startswith("${") and api_key.endswith("}"):
                    env_var = api_key[2:-1]
                    model_config["api_key"] = os.getenv(env_var)

            if provider == "openai":
                models.append(OpenAIModel(name, model_config))
            elif provider == "anthropic":
                models.append(AnthropicModel(name, model_config))
            elif provider == "google":
                models.append(GoogleModel(name, model_config))
            else:
                print(f"Warning: Unknown provider '{provider}' for model '{name}'")

        return models

    def _initialize_evaluators(self) -> Dict[str, Any]:
        """Initialize evaluators from config."""
        eval_config = self.config.get("evaluation_dimensions", {})

        evaluators = {}

        if eval_config.get("functional_correctness", {}).get("enabled", True):
            evaluators["functional"] = FunctionalCorrectnessEvaluator(
                eval_config["functional_correctness"]
            )

        if eval_config.get("code_quality", {}).get("enabled", True):
            evaluators["quality"] = CodeQualityEvaluator(
                eval_config["code_quality"]
            )

        if eval_config.get("security", {}).get("enabled", True):
            evaluators["security"] = SecurityEvaluator(
                eval_config["security"]
            )

        if eval_config.get("efficiency", {}).get("enabled", False):
            evaluators["efficiency"] = EfficiencyEvaluator(
                eval_config["efficiency"]
            )

        if eval_config.get("explainability", {}).get("enabled", True):
            evaluators["explainability"] = ExplainabilityEvaluator(
                eval_config["explainability"]
            )

        return evaluators

    def evaluate(self, test_suite: TestSuite) -> List[Dict[str, Any]]:
        """
        Run evaluation on test suite.

        Args:
            test_suite: Test suite to evaluate

        Returns:
            List of evaluation results
        """
        all_results = []

        # Calculate total evaluations
        total_test_cases = sum(len(rule.test_cases) for rule in test_suite.rules)
        total_evals = total_test_cases * len(self.models)
        completed_evals = 0
        completed_test_cases = 0

        print(f"Evaluating test suite: {test_suite.name}")
        print(f"Total rules: {len(test_suite.rules)}")
        print(f"Total models: {len(self.models)}")
        print(f"Total evaluations: {total_evals}")
        if self.limit:
            print(f"Limit: {self.limit} test case(s)")
        print(f"Parallelization: {self.max_workers} worker(s)")
        print()

        for rule in test_suite.rules:
            # Check if we've reached the limit
            if self.limit and completed_test_cases >= self.limit:
                print(f"\n✓ Reached test case limit ({self.limit})")
                break
            print(f"Rule: {rule.rule_id} ({len(rule.test_cases)} test cases)")

            for test_case in rule.test_cases:
                # Check if we've reached the limit
                if self.limit and completed_test_cases >= self.limit:
                    print(f"\n✓ Reached test case limit ({self.limit})")
                    break

                print(f"  Test case: {test_case.id}")

                # Prepare evaluation tasks
                tasks = []
                for model in self.models:
                    tasks.append((model, rule, test_case, test_suite))

                # Execute in parallel or sequential
                if self.max_workers == 1:
                    # Sequential execution - show live updates
                    for model, rule, test_case, test_suite in tasks:
                        print(f"    Evaluating with {model.name}...", end=" ")

                        result = self._evaluate_single(model, rule, test_case, test_suite)
                        all_results.append(result)

                        status = "✓ PASS" if result["passed"] else "✗ FAIL"
                        print(status)

                        completed_evals += 1
                else:
                    # Parallel execution - show progress, then summary
                    print(f"    Running {len(tasks)} model(s) in parallel...", end=" ", flush=True)

                    with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                        # Submit all tasks
                        future_to_model = {
                            executor.submit(
                                self._evaluate_single,
                                model,
                                rule,
                                test_case,
                                test_suite
                            ): model.name
                            for model, rule, test_case, test_suite in tasks
                        }

                        # Collect results as they complete
                        test_results = []
                        for future in as_completed(future_to_model):
                            result = future.result()
                            test_results.append(result)
                            all_results.append(result)
                            completed_evals += 1

                    # Show summary for this test case
                    print(f"Done [{completed_evals}/{total_evals}]")

                    # Sort results by model name for consistent display
                    test_results.sort(key=lambda x: x["model_name"])

                    for result in test_results:
                        status = "✓ PASS" if result["passed"] else "✗ FAIL"
                        model_name = result["model_name"]
                        print(f"      {model_name:25s} {status}")

                # Increment test case counter (after all models have evaluated this test case)
                completed_test_cases += 1

        return all_results

    def _evaluate_single(
        self,
        model: Any,
        rule: Any,
        test_case: Any,
        test_suite: TestSuite
    ) -> Dict[str, Any]:
        """
        Evaluate a single test case with a model.

        Args:
            model: LLM model
            rule: Rule being evaluated
            test_case: Test case
            test_suite: Test suite containing custom prompt (optional)

        Returns:
            Evaluation result dictionary
        """
        # Build prompt
        prompt, prompt_source = self._build_prompt(rule, test_case, test_suite)

        # Generate fix
        try:
            generation_result = model.generate_with_timing(prompt)

            if "error" in generation_result:
                return self._build_error_result(
                    model.name,
                    rule.rule_id,
                    test_case.id,
                    generation_result["error"]
                )

            # Extract code and explanation
            generated_code, explanation = model.extract_code_and_explanation(
                generation_result["response"]
            )

            # Run evaluators
            metrics = self._run_evaluators(
                test_case.code_snippet,
                generated_code,
                test_case.expected_fix,
                test_case.language.value,
                {
                    "rule_id": rule.rule_id,
                    "explanation": explanation,
                    "test_code": test_case.test_code
                }
            )

            # Add response time and tokens
            metrics["response_time_ms"] = generation_result["response_time_ms"]
            metrics["tokens_used"] = generation_result.get("tokens_used", 0)

            # Add human-readable compilation error explanation if compilation failed
            if not metrics.get("compiles", True) and "compilation_error" in metrics:
                metrics["compilation_error_explanation"] = self._explain_compilation_error(
                    metrics["compilation_error"]
                )

            # Determine pass/fail
            passed = self._determine_pass(metrics)
            failure_reason = None if passed else self._determine_failure_reason(metrics)

            return {
                "test_case_id": test_case.id,
                "rule_id": rule.rule_id,
                "model_name": model.name,
                "timestamp": datetime.now().isoformat(),
                "generated_code": generated_code,
                "generated_explanation": explanation,
                "expected_code": test_case.expected_fix if test_case.expected_fix else None,
                "original_code": test_case.code_snippet,
                "raw_response": generation_result["response"],
                "metrics": metrics,
                "passed": passed,
                "failure_reason": failure_reason,
                "estimated_cost": generation_result.get("cost", 0.0),
                "prompt_source": prompt_source
            }

        except Exception as e:
            return self._build_error_result(
                model.name,
                rule.rule_id,
                test_case.id,
                str(e)
            )

    def _build_prompt(self, rule: Any, test_case: Any, test_suite: TestSuite) -> tuple[str, str]:
        """Build prompt for model.

        Uses additive approach:
        1. Base template: test_suite.prompt (custom) OR config.yaml default
        2. Migration guidance: Injected via {migration_guidance} placeholder if labels present
        3. Other placeholders: Filled with actual values (code, rule_description, etc.)

        Returns:
            tuple: (prompt, prompt_source) where prompt_source is for tracking
        """
        prompt_source = "default"

        # Step 1: Select base template
        if test_suite.prompt:
            template = test_suite.prompt
            prompt_source = "custom"
        else:
            template = self.config.get("prompts", {}).get("default", "")
            prompt_source = "default"

        # Step 2: Build migration guidance string (if labels present)
        migration_guidance = ""
        migration_source = test_suite.metadata.get('migration_source')
        migration_target = test_suite.metadata.get('migration_target')

        if migration_source or migration_target:
            guidance = self._find_guidance(migration_source, migration_target)
            if guidance:
                migration_guidance = self._build_guidance_string(guidance)
                # Update prompt_source to indicate guidance was added
                source_part = migration_source or "any"
                target_part = migration_target or "any"
                if prompt_source == "custom":
                    prompt_source = f"custom+config:{source_part}-to-{target_part}"
                else:
                    prompt_source = f"default+config:{source_part}-to-{target_part}"

        # Step 3: Fetch Konveyor rule message if source is available
        konveyor_message = ""
        if hasattr(rule, 'source') and rule.source:
            fetcher = get_rule_fetcher()
            konveyor_rule = fetcher.fetch_rule(rule.source, rule.rule_id)
            if konveyor_rule and konveyor_rule.get("message"):
                konveyor_message = konveyor_rule["message"]

        # Step 4: Fill all placeholders
        prompt = template.format(
            migration_guidance=migration_guidance,
            rule_id=rule.rule_id,
            rule_description=rule.description,
            konveyor_message=konveyor_message,
            language=test_case.language.value,
            code_snippet=test_case.code_snippet,
            context=test_case.context
        )

        return prompt, prompt_source

    def _run_evaluators(
        self,
        original_code: str,
        generated_code: str,
        expected_code: str,
        language: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Run all enabled evaluators."""
        metrics = {}

        for name, evaluator in self.evaluators.items():
            if evaluator.is_enabled():
                try:
                    result = evaluator.evaluate(
                        original_code,
                        generated_code,
                        expected_code,
                        language,
                        context
                    )
                    metrics.update(result)
                except Exception as e:
                    print(f"    Warning: {name} evaluator failed: {e}")

        return metrics

    def _determine_pass(self, metrics: Dict[str, Any]) -> bool:
        """Determine if evaluation passed based on metrics."""
        # Must have functional correctness
        if not metrics.get("functional_correctness", False):
            return False

        # Must not introduce new violations
        if metrics.get("introduces_violations", True):
            return False

        # If compilation is checked, must compile
        if "compiles" in metrics and not metrics["compiles"]:
            return False

        # Check security issues
        if metrics.get("high_severity_security", 0) > 0:
            return False

        return True

    def _determine_failure_reason(self, metrics: Dict[str, Any]) -> str:
        """Determine reason for failure with detailed explanation."""
        if not metrics.get("functional_correctness", False):
            return "Does not resolve violation"

        if metrics.get("introduces_violations", False):
            new_count = metrics.get("new_violation_count", 0)
            return f"Introduces new violations ({new_count} new violation(s))"

        if "compiles" in metrics and not metrics["compiles"]:
            # Include compilation error details if available
            if "compilation_error" in metrics:
                error_msg = metrics["compilation_error"]
                # Truncate very long error messages for the summary
                if len(error_msg) > 200:
                    error_msg = error_msg[:200] + "..."
                return f"Compilation error: {error_msg}"
            return "Compilation error"

        if metrics.get("high_severity_security", 0) > 0:
            count = metrics.get("high_severity_security", 0)
            return f"High severity security issues ({count} issue(s))"

        return "Unknown failure"

    def _explain_compilation_error(self, error_msg: str) -> str:
        """Generate human-readable explanation of compilation error."""
        error_lower = error_msg.lower()

        # Missing symbol/package errors
        if "cannot find symbol" in error_lower or "package" in error_lower and "does not exist" in error_lower:
            if "package" in error_lower:
                return "❌ **Missing Dependency**: The code uses a package that isn't available in the classpath. This usually means a required library/JAR is missing from the dependencies."
            else:
                return "❌ **Missing Symbol**: The code references a class, method, or variable that doesn't exist. This could be due to a typo, missing import, or incorrect API usage."

        # Interface implementation errors
        if "is not abstract and does not override abstract method" in error_lower:
            return "❌ **Interface Implementation Error**: The class implements an interface but doesn't provide all required methods, or the method signature doesn't match. Make sure all interface methods are implemented with exact signatures."

        # Method signature mismatch
        if "cannot be applied to given types" in error_lower or "incompatible types" in error_lower:
            return "❌ **Type Mismatch**: The code is calling a method with the wrong parameter types, or assigning a value to a variable of an incompatible type. Check that method arguments and return types match their declarations."

        # Duplicate declarations
        if "already defined" in error_lower:
            return "❌ **Duplicate Declaration**: A variable, method, or class is declared more than once in the same scope. Remove the duplicate declaration."

        # Access modifiers
        if "has private access" in error_lower or "is not visible" in error_lower:
            return "❌ **Access Restriction**: The code is trying to access a private or protected member from outside its class. Use public methods or change the access modifier if appropriate."

        # Static context errors
        if "non-static" in error_lower and "cannot be referenced from a static context" in error_lower:
            return "❌ **Static Context Error**: Trying to access an instance member from a static context. Either make the member static or create an instance of the class first."

        # Return type errors
        if "missing return statement" in error_lower:
            return "❌ **Missing Return Statement**: A non-void method doesn't return a value in all code paths. Ensure all branches return the correct type."

        # Import errors (class not found)
        if "class file for" in error_lower and "not found" in error_lower:
            return "❌ **Class Not Found**: The compiler can't find a referenced class file. This usually indicates a missing dependency or incorrect classpath."

        # Generic fallback
        return "❌ **Compilation Failed**: The generated code contains syntax or semantic errors that prevent compilation. Review the error details below and the generated code."

    def _build_error_result(
        self,
        model_name: str,
        rule_id: str,
        test_case_id: str,
        error: str
    ) -> Dict[str, Any]:
        """Build error result."""
        return {
            "test_case_id": test_case_id,
            "rule_id": rule_id,
            "model_name": model_name,
            "timestamp": datetime.now().isoformat(),
            "generated_code": "",
            "generated_explanation": None,
            "expected_code": None,
            "original_code": None,
            "raw_response": "",
            "metrics": {"response_time_ms": 0},
            "passed": False,
            "failure_reason": f"Error: {error}",
            "estimated_cost": 0.0
        }


def load_test_suite(path: str) -> TestSuite:
    """Load test suite from YAML file."""
    with open(path, 'r') as f:
        data = yaml.safe_load(f)

    return TestSuite(**data)


def load_config(config_path: str) -> Dict[str, Any]:
    """Load configuration."""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Evaluate LLM models on Konveyor AI code fixes"
    )
    parser.add_argument(
        "--config",
        default="config.yaml",
        help="Path to configuration file"
    )
    parser.add_argument(
        "--benchmark",
        required=True,
        help="Path to benchmark YAML file or directory"
    )
    parser.add_argument(
        "--output",
        default="results",
        help="Output directory for results"
    )
    parser.add_argument(
        "--format",
        choices=["html", "markdown", "both"],
        default="both",
        help="Report format"
    )
    parser.add_argument(
        "--parallel",
        type=int,
        default=1,
        metavar="N",
        help="Number of parallel workers for evaluation (default: 1 = sequential)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        metavar="N",
        help="Limit evaluation to first N test cases (useful for quick testing)"
    )

    args = parser.parse_args()

    # Load config
    if not Path(args.config).exists():
        print(f"Error: Config file '{args.config}' not found")
        print("Create config.yaml from config.example.yaml")
        return 1

    config = load_config(args.config)

    # Load benchmark
    benchmark_path = Path(args.benchmark)
    if not benchmark_path.exists():
        print(f"Error: Benchmark '{args.benchmark}' not found")
        return 1

    test_suite = load_test_suite(str(benchmark_path))

    # Initialize engine
    engine = EvaluationEngine(config, max_workers=args.parallel, limit=args.limit)

    # Run evaluation
    print("=" * 60)
    print("Starting Evaluation")
    print("=" * 60)
    print()

    results = engine.evaluate(test_suite)

    # Save raw results
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = output_dir / f"results_{timestamp}.json"

    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)

    print()
    print(f"Raw results saved to: {results_file}")
    print(f"  → file://{results_file.absolute()}")

    # Generate reports
    report_config = {
        "test_suite": test_suite.name,
        "timestamp": timestamp
    }

    if args.format in ["markdown", "both"]:
        md_reporter = MarkdownReporter(str(output_dir))
        md_report = md_reporter.generate_report(results, report_config)
        md_path = Path(md_report).absolute()
        print(f"Markdown report: {md_report}")
        print(f"  → file://{md_path}")

    if args.format in ["html", "both"]:
        html_reporter = HTMLReporter(str(output_dir))
        html_report = html_reporter.generate_report(results, report_config)
        html_path = Path(html_report).absolute()
        print(f"HTML report: {html_report}")
        print(f"  → file://{html_path}")

    print()
    print("=" * 60)
    print("Evaluation Complete")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    exit(main())
