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

    </div>

    <script>
        {self._build_charts_script(results, model_stats)}
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
