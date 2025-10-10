#!/usr/bin/env python3
"""
Main evaluation script for Konveyor AI.

Usage:
    python evaluate.py --benchmark benchmarks/test_cases/java-ee-quarkus-migration.yaml
    python evaluate.py --config config.yaml --benchmark benchmarks/test_cases/
"""
import argparse
import yaml
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import os

from benchmarks.schema import TestSuite, EvaluationResult, EvaluationMetrics
from models import OpenAIModel, AnthropicModel
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

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize evaluation engine.

        Args:
            config: Configuration dictionary
        """
        self.config = config

        # Initialize models
        self.models = self._initialize_models()

        # Initialize evaluators
        self.evaluators = self._initialize_evaluators()

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

        print(f"Evaluating test suite: {test_suite.name}")
        print(f"Total rules: {len(test_suite.rules)}")
        print(f"Total models: {len(self.models)}")
        print()

        for rule in test_suite.rules:
            print(f"Rule: {rule.rule_id} ({len(rule.test_cases)} test cases)")

            for test_case in rule.test_cases:
                print(f"  Test case: {test_case.id}")

                for model in self.models:
                    print(f"    Evaluating with {model.name}...", end=" ")

                    result = self._evaluate_single(
                        model,
                        rule,
                        test_case
                    )

                    all_results.append(result)

                    status = "✓ PASS" if result["passed"] else "✗ FAIL"
                    print(status)

        return all_results

    def _evaluate_single(
        self,
        model: Any,
        rule: Any,
        test_case: Any
    ) -> Dict[str, Any]:
        """
        Evaluate a single test case with a model.

        Args:
            model: LLM model
            rule: Rule being evaluated
            test_case: Test case

        Returns:
            Evaluation result dictionary
        """
        # Build prompt
        prompt = self._build_prompt(rule, test_case)

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
                "raw_response": generation_result["response"],
                "metrics": metrics,
                "passed": passed,
                "failure_reason": failure_reason,
                "estimated_cost": generation_result.get("cost", 0.0)
            }

        except Exception as e:
            return self._build_error_result(
                model.name,
                rule.rule_id,
                test_case.id,
                str(e)
            )

    def _build_prompt(self, rule: Any, test_case: Any) -> str:
        """Build prompt for model."""
        template = self.config.get("prompts", {}).get("default", "")

        return template.format(
            rule_id=rule.rule_id,
            rule_description=rule.description,
            language=test_case.language.value,
            code_snippet=test_case.code_snippet,
            context=test_case.context
        )

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
        """Determine reason for failure."""
        if not metrics.get("functional_correctness", False):
            return "Does not resolve violation"

        if metrics.get("introduces_violations", False):
            return "Introduces new violations"

        if "compiles" in metrics and not metrics["compiles"]:
            return "Compilation error"

        if metrics.get("high_severity_security", 0) > 0:
            return "High severity security issues"

        return "Unknown failure"

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
    engine = EvaluationEngine(config)

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

    # Generate reports
    report_config = {
        "test_suite": test_suite.name,
        "timestamp": timestamp
    }

    if args.format in ["markdown", "both"]:
        md_reporter = MarkdownReporter(str(output_dir))
        md_report = md_reporter.generate_report(results, report_config)
        print(f"Markdown report: {md_report}")

    if args.format in ["html", "both"]:
        html_reporter = HTMLReporter(str(output_dir))
        html_report = html_reporter.generate_report(results, report_config)
        print(f"HTML report: {html_report}")

    print()
    print("=" * 60)
    print("Evaluation Complete")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    exit(main())
