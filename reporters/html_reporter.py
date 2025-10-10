"""
HTML report generator with interactive visualizations.
"""
from typing import List, Dict, Any
from pathlib import Path
from datetime import datetime
import json


class HTMLReporter:
    """Generate interactive HTML evaluation reports."""

    def __init__(self, output_dir: str = "results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_report(
        self,
        results: List[Dict[str, Any]],
        config: Dict[str, Any]
    ) -> str:
        """
        Generate HTML report with charts.

        Args:
            results: Evaluation results
            config: Configuration

        Returns:
            Path to generated HTML file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.output_dir / f"evaluation_report_{timestamp}.html"

        html_content = self._build_html(results, config)

        report_file.write_text(html_content)
        return str(report_file)

    def _build_html(
        self,
        results: List[Dict[str, Any]],
        config: Dict[str, Any]
    ) -> str:
        """Build HTML report content."""

        # Aggregate data
        model_stats = self._aggregate_by_model(results)

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Konveyor AI Evaluation Report</title>
    <script src="https://cdn.plot.ly/plotly-2.26.0.min.js"></script>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            border-bottom: 3px solid #4CAF50;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #555;
            margin-top: 30px;
        }}
        .metadata {{
            background: #f9f9f9;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
        }}
        .chart {{
            margin: 30px 0;
            padding: 20px;
            background: #fafafa;
            border-radius: 5px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background: #4CAF50;
            color: white;
            font-weight: 600;
        }}
        tr:hover {{
            background: #f5f5f5;
        }}
        .pass {{
            color: #4CAF50;
            font-weight: bold;
        }}
        .fail {{
            color: #f44336;
            font-weight: bold;
        }}
        .metric-card {{
            display: inline-block;
            background: #fff;
            border: 1px solid #ddd;
            border-radius: 5px;
            padding: 20px;
            margin: 10px;
            min-width: 200px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }}
        .metric-value {{
            font-size: 32px;
            font-weight: bold;
            color: #4CAF50;
        }}
        .metric-label {{
            color: #777;
            font-size: 14px;
            margin-top: 5px;
        }}
        .failure-card {{
            background: #fff;
            border: 1px solid #f44336;
            border-left: 4px solid #f44336;
            border-radius: 5px;
            padding: 20px;
            margin: 15px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .success-card {{
            background: #fff;
            border: 1px solid #4CAF50;
            border-left: 4px solid #4CAF50;
            border-radius: 5px;
            padding: 20px;
            margin: 15px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .test-card {{
            background: #fff;
            border: 1px solid #ddd;
            border-left: 4px solid #ddd;
            border-radius: 5px;
            padding: 20px;
            margin: 15px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .test-card.passed {{
            border-color: #4CAF50;
            border-left-color: #4CAF50;
        }}
        .test-card.failed {{
            border-color: #f44336;
            border-left-color: #f44336;
        }}
        .failure-header {{
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }}
        .failure-header:hover {{
            background: #f9f9f9;
            margin: -5px;
            padding: 5px;
            border-radius: 3px;
        }}
        .failure-title {{
            font-weight: bold;
            color: #333;
        }}
        .failure-reason {{
            color: #f44336;
            font-size: 14px;
            margin: 5px 0;
        }}
        .failure-details {{
            display: none;
            margin-top: 15px;
            padding-top: 15px;
            border-top: 1px solid #eee;
        }}
        .failure-details.expanded {{
            display: block;
        }}
        .code-comparison {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            margin: 15px 0;
        }}
        .code-block {{
            background: #f5f5f5;
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 10px;
            overflow-x: auto;
        }}
        .code-block h4 {{
            margin: 0 0 10px 0;
            font-size: 14px;
            color: #666;
        }}
        .code-block pre {{
            margin: 0;
            font-family: 'Courier New', monospace;
            font-size: 12px;
            white-space: pre-wrap;
        }}
        .expand-icon {{
            transition: transform 0.3s;
        }}
        .expand-icon.expanded {{
            transform: rotate(180deg);
        }}
        .filter-buttons {{
            margin: 20px 0;
        }}
        .filter-btn {{
            background: #f0f0f0;
            border: 1px solid #ddd;
            padding: 8px 16px;
            margin: 5px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
        }}
        .filter-btn.active {{
            background: #4CAF50;
            color: white;
            border-color: #4CAF50;
        }}
        .badge {{
            display: inline-block;
            padding: 4px 8px;
            border-radius: 3px;
            font-size: 12px;
            font-weight: bold;
            margin-left: 10px;
        }}
        .badge-error {{
            background: #f44336;
            color: white;
        }}
        .badge-regression {{
            background: #ff9800;
            color: white;
        }}
        .badge-compilation {{
            background: #9c27b0;
            color: white;
        }}
        .badge-security {{
            background: #e91e63;
            color: white;
        }}
        .badge-success {{
            background: #4CAF50;
            color: white;
        }}
        .success-message {{
            color: #4CAF50;
            font-size: 14px;
            margin: 5px 0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Konveyor AI Evaluation Report</h1>

        <div class="metadata">
            <strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br>
            <strong>Test Suite:</strong> {config.get('test_suite', 'Unknown')}<br>
            <strong>Total Test Cases:</strong> {len(results)}<br>
            <strong>Models Evaluated:</strong> {len(model_stats)}
        </div>

        <h2>Overall Summary</h2>
        <div id="metrics-cards">
            {self._build_metric_cards(model_stats)}
        </div>

        <h2>Model Comparison</h2>
        <div class="chart" id="comparison-chart"></div>

        <h2>Response Time Distribution</h2>
        <div class="chart" id="response-time-chart"></div>

        <h2>Per-Rule Performance</h2>
        <div class="chart" id="rule-performance-chart"></div>

        <h2>Detailed Results</h2>
        {self._build_results_table(model_stats)}

        <h2>All Test Results</h2>
        {self._build_all_results_section(results)}

        <h2>Failure Analysis</h2>
        {self._build_failure_section(results)}

    </div>

    <script>
        {self._build_charts_script(results, model_stats)}
        {self._build_interaction_script()}
    </script>
</body>
</html>
        """

        return html

    def _aggregate_by_model(
        self,
        results: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """Aggregate results by model."""

        model_stats = {}

        for result in results:
            model_name = result["model_name"]

            if model_name not in model_stats:
                model_stats[model_name] = {
                    "total": 0,
                    "passed": 0,
                    "failed": 0,
                    "results": [],
                    "response_times": [],
                    "costs": []
                }

            stats = model_stats[model_name]
            stats["total"] += 1
            stats["results"].append(result)

            if result.get("passed", False):
                stats["passed"] += 1
            else:
                stats["failed"] += 1

            stats["response_times"].append(result["metrics"]["response_time_ms"])
            stats["costs"].append(result.get("estimated_cost", 0))

        return model_stats

    def _build_metric_cards(
        self,
        model_stats: Dict[str, Dict[str, Any]]
    ) -> str:
        """Build metric summary cards."""

        total_tests = sum(s["total"] for s in model_stats.values())
        total_passed = sum(s["passed"] for s in model_stats.values())
        total_cost = sum(sum(s["costs"]) for s in model_stats.values())

        pass_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0

        return f"""
        <div class="metric-card">
            <div class="metric-value">{total_tests}</div>
            <div class="metric-label">Total Tests</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">{pass_rate:.1f}%</div>
            <div class="metric-label">Overall Pass Rate</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">${total_cost:.3f}</div>
            <div class="metric-label">Total Cost</div>
        </div>
        """

    def _build_results_table(
        self,
        model_stats: Dict[str, Dict[str, Any]]
    ) -> str:
        """Build detailed results table."""

        rows = []

        for model_name, stats in model_stats.items():
            pass_rate = (stats["passed"] / stats["total"] * 100) if stats["total"] > 0 else 0
            avg_response = sum(stats["response_times"]) / len(stats["response_times"]) if stats["response_times"] else 0
            total_cost = sum(stats["costs"])

            rows.append(f"""
                <tr>
                    <td>{model_name}</td>
                    <td>{stats["total"]}</td>
                    <td class="pass">{stats["passed"]}</td>
                    <td class="fail">{stats["failed"]}</td>
                    <td>{pass_rate:.1f}%</td>
                    <td>{avg_response:.0f}ms</td>
                    <td>${total_cost:.4f}</td>
                </tr>
            """)

        return f"""
        <table>
            <thead>
                <tr>
                    <th>Model</th>
                    <th>Total Tests</th>
                    <th>Passed</th>
                    <th>Failed</th>
                    <th>Pass Rate</th>
                    <th>Avg Response Time</th>
                    <th>Total Cost</th>
                </tr>
            </thead>
            <tbody>
                {''.join(rows)}
            </tbody>
        </table>
        """

    def _build_charts_script(
        self,
        results: List[Dict[str, Any]],
        model_stats: Dict[str, Dict[str, Any]]
    ) -> str:
        """Build JavaScript for interactive charts."""

        # Comparison chart data
        models = list(model_stats.keys())
        pass_rates = [
            (stats["passed"] / stats["total"] * 100) if stats["total"] > 0 else 0
            for stats in model_stats.values()
        ]

        # Response time data
        response_time_data = {
            model: stats["response_times"]
            for model, stats in model_stats.items()
        }

        return f"""
        // Model comparison chart
        var comparisonData = [{{
            x: {json.dumps(models)},
            y: {json.dumps(pass_rates)},
            type: 'bar',
            marker: {{color: '#4CAF50'}}
        }}];

        var comparisonLayout = {{
            title: 'Pass Rate by Model',
            xaxis: {{title: 'Model'}},
            yaxis: {{title: 'Pass Rate (%)', range: [0, 100]}}
        }};

        Plotly.newPlot('comparison-chart', comparisonData, comparisonLayout);

        // Response time distribution
        var responseTimeData = {json.dumps([
            {
                "x": times,
                "type": "box",
                "name": model
            }
            for model, times in response_time_data.items()
        ])};

        var responseTimeLayout = {{
            title: 'Response Time Distribution',
            yaxis: {{title: 'Response Time (ms)'}}
        }};

        Plotly.newPlot('response-time-chart', responseTimeData, responseTimeLayout);

        // Per-rule performance (placeholder)
        // Add per-rule chart implementation here
        """

    def _build_all_results_section(self, results: List[Dict[str, Any]]) -> str:
        """Build section showing all test results (both passing and failing)."""

        if not results:
            return "<p>No test results available.</p>"

        passed_count = sum(1 for r in results if r.get("passed", False))
        failed_count = len(results) - passed_count

        # Build filter buttons
        filter_html = '<div class="filter-buttons">'
        filter_html += f'<button class="result-filter-btn active" onclick="filterResults(\'all\')">All ({len(results)})</button>'
        filter_html += f'<button class="result-filter-btn" onclick="filterResults(\'passed\')">Passed ({passed_count})</button>'
        filter_html += f'<button class="result-filter-btn" onclick="filterResults(\'failed\')">Failed ({failed_count})</button>'
        filter_html += '</div>'

        # Build result cards
        cards_html = '<div id="all-results">'

        for i, result in enumerate(results):
            passed = result.get("passed", False)
            status = "passed" if passed else "failed"
            card_class = f"test-card {status}"

            status_icon = "✓" if passed else "✗"
            status_class = "success-message" if passed else "failure-reason"
            status_text = "Test passed" if passed else result.get("failure_reason", "Test failed")

            cards_html += f'''
            <div class="{card_class}" data-status="{status}">
                <div class="failure-header" onclick="toggleResult({i})">
                    <div>
                        <span class="failure-title">
                            {result.get("model_name", "Unknown")} -
                            {result.get("rule_id", "Unknown")} -
                            {result.get("test_case_id", "Unknown")}
                        </span>
                        <span class="badge {'badge-success' if passed else 'badge-error'}">{status.upper()}</span>
                    </div>
                    <span class="expand-icon" id="result-icon-{i}">▼</span>
                </div>
                <div class="{status_class}">
                    {status_icon} {status_text}
                </div>
                <div class="failure-details" id="result-details-{i}">
                    <div class="code-comparison">
                        <div class="code-block">
                            <h4>Generated Code</h4>
                            <pre>{self._escape_html(result.get("generated_code", "N/A"))}</pre>
                        </div>
                        <div class="code-block">
                            <h4>Explanation</h4>
                            <pre>{self._escape_html(result.get("generated_explanation", "No explanation provided"))}</pre>
                        </div>
                    </div>
                    <div style="margin-top: 15px; padding: 10px; background: #f9f9f9; border-radius: 4px;">
                        <strong>Metrics:</strong><br>
                        Response Time: {result.get("metrics", {}).get("response_time_ms", 0):.0f}ms |
                        Cost: ${result.get("estimated_cost", 0):.4f}
                        {self._build_metric_details(result.get("metrics", {}))}
                    </div>
                </div>
            </div>
            '''

        cards_html += '</div>'

        return filter_html + cards_html

    def _build_failure_section(self, results: List[Dict[str, Any]]) -> str:
        """Build interactive failure analysis section."""

        failures = [r for r in results if not r.get("passed", False)]

        if not failures:
            return """
            <p style="color: #4CAF50; font-size: 18px; text-align: center; padding: 40px;">
                🎉 No failures detected! All test cases passed.
            </p>
            """

        # Categorize failures
        failure_categories = self._categorize_failures(failures)

        # Build filter buttons
        filter_html = '<div class="filter-buttons">'
        filter_html += '<button class="filter-btn active" onclick="filterFailures(\'all\')">All ({0})</button>'.format(len(failures))

        for category, count in failure_categories.items():
            filter_html += f'<button class="filter-btn" onclick="filterFailures(\'{category}\')">{category.title()} ({count})</button>'

        filter_html += '</div>'

        # Build failure cards
        cards_html = '<div id="failure-cards">'

        for i, failure in enumerate(failures):
            category = self._get_failure_category(failure)
            badge_class = f"badge-{category}"

            cards_html += f'''
            <div class="failure-card" data-category="{category}">
                <div class="failure-header" onclick="toggleFailure({i})">
                    <div>
                        <span class="failure-title">
                            {failure.get("model_name", "Unknown")} -
                            {failure.get("rule_id", "Unknown")} -
                            {failure.get("test_case_id", "Unknown")}
                        </span>
                        <span class="badge {badge_class}">{category.upper()}</span>
                    </div>
                    <span class="expand-icon" id="icon-{i}">▼</span>
                </div>
                <div class="failure-reason">
                    ❌ {failure.get("failure_reason", "Unknown failure")}
                </div>
                <div class="failure-details" id="details-{i}">
                    <div class="code-comparison">
                        <div class="code-block">
                            <h4>Generated Code</h4>
                            <pre>{self._escape_html(failure.get("generated_code", "N/A"))}</pre>
                        </div>
                        <div class="code-block">
                            <h4>Explanation</h4>
                            <pre>{self._escape_html(failure.get("generated_explanation", "No explanation provided"))}</pre>
                        </div>
                    </div>
                    <div style="margin-top: 15px; padding: 10px; background: #f9f9f9; border-radius: 4px;">
                        <strong>Metrics:</strong><br>
                        Response Time: {failure.get("metrics", {}).get("response_time_ms", 0):.0f}ms |
                        Cost: ${failure.get("estimated_cost", 0):.4f}
                        {self._build_metric_details(failure.get("metrics", {}))}
                    </div>
                </div>
            </div>
            '''

        cards_html += '</div>'

        return filter_html + cards_html

    def _categorize_failures(self, failures: List[Dict[str, Any]]) -> Dict[str, int]:
        """Categorize failures by type."""
        categories = {}

        for failure in failures:
            category = self._get_failure_category(failure)
            categories[category] = categories.get(category, 0) + 1

        return categories

    def _get_failure_category(self, failure: Dict[str, Any]) -> str:
        """Determine failure category from failure reason."""
        reason = failure.get("failure_reason", "").lower()

        if "compil" in reason:
            return "compilation"
        elif "regression" in reason or "introduc" in reason:
            return "regression"
        elif "security" in reason:
            return "security"
        elif "resolve" in reason or "violation" in reason:
            return "error"
        else:
            return "error"

    def _build_metric_details(self, metrics: Dict[str, Any]) -> str:
        """Build additional metric details for failure card."""
        details = []

        if metrics.get("compiles") is not None:
            details.append(f"Compiles: {'✓' if metrics['compiles'] else '✗'}")

        if metrics.get("functional_correctness") is not None:
            details.append(f"Functional: {'✓' if metrics['functional_correctness'] else '✗'}")

        if metrics.get("introduces_violations"):
            details.append(f"⚠️ Introduces {metrics.get('new_violation_count', 0)} new violations")

        if details:
            return " | " + " | ".join(details)
        return ""

    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters."""
        if not text:
            return ""
        return (text
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;")
                .replace("'", "&#39;"))

    def _build_interaction_script(self) -> str:
        """Build JavaScript for interactive features."""
        return """
        // Toggle failure details
        function toggleFailure(index) {
            const details = document.getElementById('details-' + index);
            const icon = document.getElementById('icon-' + index);

            details.classList.toggle('expanded');
            icon.classList.toggle('expanded');
        }

        // Filter failures by category
        function filterFailures(category) {
            const cards = document.querySelectorAll('.failure-card');
            const buttons = document.querySelectorAll('.filter-btn');

            // Update active button
            buttons.forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');

            // Filter cards
            cards.forEach(card => {
                if (category === 'all' || card.dataset.category === category) {
                    card.style.display = 'block';
                } else {
                    card.style.display = 'none';
                }
            });
        }

        // Toggle all results
        function toggleResult(index) {
            const details = document.getElementById('result-details-' + index);
            const icon = document.getElementById('result-icon-' + index);

            details.classList.toggle('expanded');
            icon.classList.toggle('expanded');
        }

        // Filter all results by status
        function filterResults(status) {
            const cards = document.querySelectorAll('.test-card');
            const buttons = document.querySelectorAll('.result-filter-btn');

            // Update active button
            buttons.forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');

            // Filter cards
            cards.forEach(card => {
                if (status === 'all' || card.dataset.status === status) {
                    card.style.display = 'block';
                } else {
                    card.style.display = 'none';
                }
            });
        }
        """
