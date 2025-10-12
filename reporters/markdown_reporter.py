"""
Markdown report generator.
"""
from typing import List, Dict, Any
from pathlib import Path
import json
from datetime import datetime


class MarkdownReporter:
    """Generate markdown evaluation reports."""

    def __init__(self, output_dir: str = "results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_report(
        self,
        results: List[Dict[str, Any]],
        config: Dict[str, Any]
    ) -> str:
        """
        Generate markdown report.

        Args:
            results: List of evaluation results
            config: Evaluation configuration

        Returns:
            Path to generated report
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.output_dir / f"evaluation_report_{timestamp}.md"

        content = self._build_report_content(results, config)

        report_file.write_text(content)
        return str(report_file)

    def _build_report_content(
        self,
        results: List[Dict[str, Any]],
        config: Dict[str, Any]
    ) -> str:
        """Build markdown report content."""

        # Aggregate results by model
        model_results = {}
        for result in results:
            model_name = result["model_name"]
            if model_name not in model_results:
                model_results[model_name] = []
            model_results[model_name].append(result)

        # Build report
        lines = [
            "# Konveyor AI Evaluation Report",
            "",
            f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            f"**Test Suite:** {config.get('test_suite', 'Unknown')}",
            f"**Total Test Cases:** {len(results)}",
            f"**Models Evaluated:** {len(model_results)}",
            "",
            "---",
            "",
        ]

        # Overall summary
        lines.extend(self._build_summary_section(model_results))

        # Per-model details
        for model_name, model_data in model_results.items():
            lines.extend(self._build_model_section(model_name, model_data))

        # Failure analysis
        lines.extend(self._build_failure_section(results))

        return "\n".join(lines)

    def _build_summary_section(
        self,
        model_results: Dict[str, List[Dict[str, Any]]]
    ) -> List[str]:
        """Build summary comparison table."""

        lines = [
            "## Summary",
            "",
            "| Model | Pass Rate | Avg Response Time | Avg Quality Score | Total Cost |",
            "|-------|-----------|-------------------|-------------------|------------|",
        ]

        for model_name, results in model_results.items():
            total = len(results)
            passed = sum(1 for r in results if r.get("passed", False))
            pass_rate = (passed / total * 100) if total > 0 else 0

            avg_response_time = sum(
                r["metrics"]["response_time_ms"] for r in results
            ) / total if total > 0 else 0

            # Calculate average quality score (if available)
            quality_scores = [
                r["metrics"].get("pylint_score")
                for r in results
                if r["metrics"].get("pylint_score") is not None
            ]
            avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0

            total_cost = sum(r.get("estimated_cost", 0) for r in results)

            lines.append(
                f"| {model_name} | {pass_rate:.1f}% | {avg_response_time:.0f}ms | "
                f"{avg_quality:.1f} | ${total_cost:.4f} |"
            )

        lines.extend(["", "---", ""])
        return lines

    def _build_model_section(
        self,
        model_name: str,
        results: List[Dict[str, Any]]
    ) -> List[str]:
        """Build detailed section for a model."""

        lines = [
            f"## {model_name}",
            "",
            f"**Total Test Cases:** {len(results)}",
            f"**Passed:** {sum(1 for r in results if r.get('passed', False))}",
            f"**Failed:** {sum(1 for r in results if not r.get('passed', False))}",
            "",
        ]

        # Metrics breakdown
        lines.append("### Metrics")
        lines.append("")

        # Calculate aggregated metrics
        total = len(results)

        functional_correct = sum(
            1 for r in results
            if r["metrics"].get("functional_correctness", False)
        )
        compiles = sum(
            1 for r in results
            if r["metrics"].get("compiles", False)
        )
        no_regression = sum(
            1 for r in results
            if not r["metrics"].get("introduces_violations", True)
        )

        lines.extend([
            f"- **Functional Correctness:** {functional_correct}/{total} ({functional_correct/total*100:.1f}%)",
            f"- **Compilation Success:** {compiles}/{total} ({compiles/total*100:.1f}%)",
            f"- **No Regression:** {no_regression}/{total} ({no_regression/total*100:.1f}%)",
            "",
        ])

        # Per-rule breakdown
        lines.extend(self._build_per_rule_table(results))

        lines.extend(["", "---", ""])
        return lines

    def _build_per_rule_table(
        self,
        results: List[Dict[str, Any]]
    ) -> List[str]:
        """Build per-rule accuracy table."""

        # Group by rule
        rule_results = {}
        for result in results:
            rule_id = result["rule_id"]
            if rule_id not in rule_results:
                rule_results[rule_id] = []
            rule_results[rule_id].append(result)

        lines = [
            "### Per-Rule Performance",
            "",
            "| Rule ID | Test Cases | Passed | Pass Rate |",
            "|---------|------------|--------|-----------|",
        ]

        for rule_id, rule_data in rule_results.items():
            total = len(rule_data)
            passed = sum(1 for r in rule_data if r.get("passed", False))
            pass_rate = (passed / total * 100) if total > 0 else 0

            lines.append(
                f"| {rule_id} | {total} | {passed} | {pass_rate:.1f}% |"
            )

        lines.append("")
        return lines

    def _build_failure_section(
        self,
        results: List[Dict[str, Any]],
        max_examples: int = 10
    ) -> List[str]:
        """Build failure analysis section."""

        failures = [r for r in results if not r.get("passed", False)]

        if not failures:
            return ["## Failure Analysis", "", "No failures detected!", ""]

        lines = [
            "## Failure Analysis",
            "",
            f"**Total Failures:** {len(failures)}",
            "",
            "### Example Failures",
            "",
        ]

        for i, failure in enumerate(failures[:max_examples], 1):
            lines.extend([
                f"#### Failure {i}: {failure['rule_id']} - {failure['test_case_id']}",
                "",
                f"**Reason:** {failure.get('failure_reason', 'Unknown')}",
                "",
            ])

            # Add compilation error details if available
            metrics = failure.get("metrics", {})
            if not metrics.get("compiles", True) and "compilation_error" in metrics:
                lines.extend([
                    "**Compilation Error:**",
                    "```",
                    metrics["compilation_error"],
                    "```",
                    "",
                ])

            lines.extend([
                "**Generated Code:**",
                "```",
                failure.get("generated_code", "N/A"),
                "```",
                "",
            ])

        return lines
