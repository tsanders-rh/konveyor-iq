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
        .diff-legend {{
            font-size: 11px;
            color: #666;
            margin: 5px 0;
            padding: 5px;
            background: #f9f9f9;
            border-radius: 3px;
        }}
        .diff-legend span {{
            margin-right: 15px;
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

        <h2>🏆 Top Performing Models</h2>
        {self._build_top_performers_section(model_stats)}

        <h2>Model Comparison</h2>
        <div class="chart" id="comparison-chart"></div>

        <h2>Response Time Distribution</h2>
        <div class="chart" id="response-time-chart"></div>

        <h2>Per-Rule Performance</h2>
        <div style="margin-bottom: 15px;">
            <label for="rule-selector" style="font-weight: 600; margin-right: 10px;">Select Rule:</label>
            <select id="rule-selector" style="padding: 8px 12px; font-size: 14px; border: 1px solid #ddd; border-radius: 4px; min-width: 300px;">
                <option value="all">All Rules</option>
            </select>
        </div>
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
                    "compiled": 0,
                    "results": [],
                    "response_times": [],
                    "costs": [],
                    "complexities": [],
                    "pylint_scores": [],
                    "maintainability_scores": []
                }

            stats = model_stats[model_name]
            stats["total"] += 1
            stats["results"].append(result)

            if result.get("passed", False):
                stats["passed"] += 1
            else:
                stats["failed"] += 1

            # Track compilation success
            if result.get("metrics", {}).get("compiles", False):
                stats["compiled"] += 1

            stats["response_times"].append(result["metrics"]["response_time_ms"])
            stats["costs"].append(result.get("estimated_cost", 0))

            # Collect quality metrics
            metrics = result.get("metrics", {})
            if metrics.get("cyclomatic_complexity") is not None:
                stats["complexities"].append(metrics["cyclomatic_complexity"])
            if metrics.get("pylint_score") is not None:
                stats["pylint_scores"].append(metrics["pylint_score"])
            if metrics.get("maintainability_index") is not None:
                stats["maintainability_scores"].append(metrics["maintainability_index"])

        return model_stats

    def _rank_models(self, model_stats: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Rank models based on multiple performance criteria.

        Returns:
            List of model rankings with scores
        """
        rankings = []

        for model_name, stats in model_stats.items():
            # Calculate metrics
            pass_rate = (stats["passed"] / stats["total"] * 100) if stats["total"] > 0 else 0
            compile_rate = (stats["compiled"] / stats["total"] * 100) if stats["total"] > 0 else 0
            avg_response_time = sum(stats["response_times"]) / len(stats["response_times"]) if stats["response_times"] else 0
            total_cost = sum(stats["costs"])
            avg_complexity = sum(stats["complexities"]) / len(stats["complexities"]) if stats["complexities"] else None
            avg_maintainability = sum(stats["maintainability_scores"]) / len(stats["maintainability_scores"]) if stats["maintainability_scores"] else None

            # Calculate composite score (0-100)
            # Weighted scoring: pass_rate (50%), compile_rate (20%), quality (20%), speed (5%), cost (5%)
            score = 0

            # Pass rate (most important)
            score += pass_rate * 0.5

            # Compilation rate
            score += compile_rate * 0.2

            # Quality metrics (average of available metrics)
            quality_score = 0
            quality_count = 0

            if avg_complexity is not None:
                # Lower is better, normalize to 0-100 (complexity 1-30 range)
                complexity_score = max(0, 100 - (avg_complexity - 1) * 3.33)
                quality_score += complexity_score
                quality_count += 1

            if avg_maintainability is not None:
                # Higher is better, already 0-100
                quality_score += avg_maintainability
                quality_count += 1

            if quality_count > 0:
                score += (quality_score / quality_count) * 0.2

            # Response time (lower is better, normalize to 0-100)
            # Assume 10000ms is max acceptable response time
            time_score = max(0, 100 - (avg_response_time / 100))
            score += time_score * 0.05

            # Cost (lower is better, normalize to 0-100)
            # Assume $1.00 total is max acceptable cost
            cost_score = max(0, 100 - (total_cost * 100)) if total_cost > 0 else 100
            score += cost_score * 0.05

            rankings.append({
                "model_name": model_name,
                "score": score,
                "pass_rate": pass_rate,
                "compile_rate": compile_rate,
                "avg_response_time": avg_response_time,
                "total_cost": total_cost,
                "avg_complexity": avg_complexity,
                "avg_maintainability": avg_maintainability,
                "tests_passed": stats["passed"],
                "tests_total": stats["total"]
            })

        # Sort by score descending
        rankings.sort(key=lambda x: x["score"], reverse=True)
        return rankings

    def _build_top_performers_section(self, model_stats: Dict[str, Dict[str, Any]]) -> str:
        """Build top performing models section."""
        rankings = self._rank_models(model_stats)

        if not rankings:
            return "<p>No rankings available.</p>"

        html = '<div style="margin: 20px 0;">'

        # Show podium for top 3
        for i, ranking in enumerate(rankings[:3]):
            rank = i + 1
            medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉"
            border_color = "#FFD700" if rank == 1 else "#C0C0C0" if rank == 2 else "#CD7F32"

            html += f'''
            <div style="background: #fff; border: 2px solid {border_color}; border-radius: 8px; padding: 20px; margin: 15px 0; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <span style="font-size: 32px; margin-right: 10px;">{medal}</span>
                        <span style="font-size: 24px; font-weight: bold; color: #333;">{ranking["model_name"]}</span>
                    </div>
                    <div style="text-align: right;">
                        <div style="font-size: 36px; font-weight: bold; color: {border_color};">{ranking["score"]:.1f}</div>
                        <div style="font-size: 12px; color: #666;">Overall Score</div>
                    </div>
                </div>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; margin-top: 15px; padding-top: 15px; border-top: 1px solid #eee;">
                    <div>
                        <div style="font-size: 12px; color: #666;">Pass Rate</div>
                        <div style="font-size: 20px; font-weight: bold; color: #4CAF50;">{ranking["pass_rate"]:.1f}%</div>
                        <div style="font-size: 11px; color: #999;">{ranking["tests_passed"]}/{ranking["tests_total"]} passed</div>
                    </div>
                    <div>
                        <div style="font-size: 12px; color: #666;">Compilation Rate</div>
                        <div style="font-size: 20px; font-weight: bold; color: #4CAF50;">{ranking["compile_rate"]:.1f}%</div>
                    </div>
                    <div>
                        <div style="font-size: 12px; color: #666;">Avg Response Time</div>
                        <div style="font-size: 20px; font-weight: bold; color: #2196F3;">{ranking["avg_response_time"]:.0f}ms</div>
                    </div>
                    <div>
                        <div style="font-size: 12px; color: #666;">Total Cost</div>
                        <div style="font-size: 20px; font-weight: bold; color: #FF9800;">${ranking["total_cost"]:.4f}</div>
                    </div>
            '''

            # Add quality metrics if available
            if ranking["avg_complexity"] is not None:
                html += f'''
                    <div>
                        <div style="font-size: 12px; color: #666;">Avg Complexity</div>
                        <div style="font-size: 20px; font-weight: bold; color: #9C27B0;">{ranking["avg_complexity"]:.1f}</div>
                    </div>
                '''

            if ranking["avg_maintainability"] is not None:
                html += f'''
                    <div>
                        <div style="font-size: 12px; color: #666;">Maintainability</div>
                        <div style="font-size: 20px; font-weight: bold; color: #009688;">{ranking["avg_maintainability"]:.1f}/100</div>
                    </div>
                '''

            html += '''
                </div>
            </div>
            '''

        # Show remaining models in a compact list
        if len(rankings) > 3:
            html += '<div style="margin-top: 20px;"><h3 style="color: #666; font-size: 18px;">Other Models</h3>'
            html += '<table style="width: 100%; border-collapse: collapse;">'
            html += '''
            <thead>
                <tr style="background: #f5f5f5;">
                    <th style="padding: 10px; text-align: left;">Rank</th>
                    <th style="padding: 10px; text-align: left;">Model</th>
                    <th style="padding: 10px; text-align: right;">Score</th>
                    <th style="padding: 10px; text-align: right;">Pass Rate</th>
                    <th style="padding: 10px; text-align: right;">Avg Response</th>
                    <th style="padding: 10px; text-align: right;">Cost</th>
                </tr>
            </thead>
            <tbody>
            '''

            for i, ranking in enumerate(rankings[3:], start=4):
                html += f'''
                <tr style="border-bottom: 1px solid #eee;">
                    <td style="padding: 10px;">#{i}</td>
                    <td style="padding: 10px; font-weight: 500;">{ranking["model_name"]}</td>
                    <td style="padding: 10px; text-align: right; font-weight: bold;">{ranking["score"]:.1f}</td>
                    <td style="padding: 10px; text-align: right;">{ranking["pass_rate"]:.1f}%</td>
                    <td style="padding: 10px; text-align: right;">{ranking["avg_response_time"]:.0f}ms</td>
                    <td style="padding: 10px; text-align: right;">${ranking["total_cost"]:.4f}</td>
                </tr>
                '''

            html += '</tbody></table></div>'

        html += '</div>'
        return html

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

        // Per-rule performance
        {self._build_per_rule_chart_data(results, models)}
        """

    def _build_per_rule_chart_data(self, results: List[Dict[str, Any]], models: List[str]) -> str:
        """Build JavaScript data for per-rule performance chart with rule selector."""

        # Aggregate results by rule
        rule_stats = {}
        for result in results:
            rule_id = result.get("rule_id", "Unknown")
            model_name = result.get("model_name", "Unknown")

            if rule_id not in rule_stats:
                rule_stats[rule_id] = {}

            if model_name not in rule_stats[rule_id]:
                rule_stats[rule_id][model_name] = {"total": 0, "passed": 0}

            rule_stats[rule_id][model_name]["total"] += 1
            if result.get("passed", False):
                rule_stats[rule_id][model_name]["passed"] += 1

        # Build data structure: map of rule_id -> traces for that rule
        rule_data_map = {}
        sorted_rules = sorted(rule_stats.keys())

        # For "all rules" view
        all_traces = []
        for model in models:
            rule_ids = []
            pass_rates = []

            for rule_id in sorted_rules:
                rule_ids.append(rule_id)
                stats = rule_stats[rule_id].get(model, {"total": 0, "passed": 0})
                pass_rate = (stats["passed"] / stats["total"] * 100) if stats["total"] > 0 else 0
                pass_rates.append(pass_rate)

            all_traces.append({
                "x": rule_ids,
                "y": pass_rates,
                "type": "bar",
                "name": model
            })

        rule_data_map["all"] = all_traces

        # For individual rules
        for rule_id in sorted_rules:
            rule_traces = []
            for model in models:
                stats = rule_stats[rule_id].get(model, {"total": 0, "passed": 0})
                pass_rate = (stats["passed"] / stats["total"] * 100) if stats["total"] > 0 else 0

                rule_traces.append({
                    "x": [model],
                    "y": [pass_rate],
                    "type": "bar",
                    "name": model,
                    "showlegend": False
                })

            rule_data_map[rule_id] = rule_traces

        return f"""
        // Store all rule performance data
        var allRuleData = {json.dumps(rule_data_map)};
        var ruleIds = {json.dumps(sorted_rules)};

        // Populate dropdown
        var selector = document.getElementById('rule-selector');
        ruleIds.forEach(function(ruleId) {{
            var option = document.createElement('option');
            option.value = ruleId;
            option.textContent = ruleId;
            selector.appendChild(option);
        }});

        // Initial chart layout
        var rulePerformanceLayout = {{
            title: 'Pass Rate by Rule (All Rules)',
            xaxis: {{title: 'Rule ID'}},
            yaxis: {{title: 'Pass Rate (%)', range: [0, 100]}},
            barmode: 'group'
        }};

        // Function to update chart based on selection
        function updateRuleChart(selectedRule) {{
            var data = allRuleData[selectedRule];

            if (selectedRule === 'all') {{
                rulePerformanceLayout.title = 'Pass Rate by Rule (All Rules)';
                rulePerformanceLayout.xaxis.title = 'Rule ID';
                rulePerformanceLayout.barmode = 'group';
                rulePerformanceLayout.showlegend = true;
            }} else {{
                rulePerformanceLayout.title = 'Pass Rate for ' + selectedRule;
                rulePerformanceLayout.xaxis.title = 'Model';
                rulePerformanceLayout.barmode = 'group';
                rulePerformanceLayout.showlegend = false;
            }}

            Plotly.newPlot('rule-performance-chart', data, rulePerformanceLayout);
        }}

        // Add change event listener
        selector.addEventListener('change', function() {{
            updateRuleChart(this.value);
        }});

        // Initial render with all rules
        updateRuleChart('all');
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
                    {self._build_failure_explanation(result)}
                    <div class="code-comparison">
                        <div class="code-block">
                            <h4>Generated Code</h4>
                            {'<div class="diff-legend">Legend: <span style="background: #ffebee; padding: 2px 4px;">🔴 Incorrect/Different Line</span> <span style="background: #fff3e0; padding: 2px 4px;">⚠️ Extra Line</span></div>' if result.get("expected_code") and not result.get("passed") else ''}
                            <pre>{self._generate_code_diff_html(result.get("generated_code", ""), result.get("expected_code", "")) if result.get("expected_code") and not result.get("passed") else self._escape_html(result.get("generated_code", "N/A"))}</pre>
                        </div>
                        <div class="code-block">
                            <h4>{'Expected Code' if result.get("expected_code") and not result.get("passed") else 'Explanation'}</h4>
                            <pre>{self._escape_html(result.get("expected_code") or result.get("generated_explanation", "No explanation provided"))}</pre>
                        </div>
                    </div>
                    {self._build_compilation_error_section(result.get("metrics", {}))}
                    {self._build_quality_metrics_section(result.get("metrics", {}))}
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
                    {self._build_failure_explanation(failure)}
                    <div class="code-comparison">
                        <div class="code-block">
                            <h4>Generated Code</h4>
                            {'<div class="diff-legend">Legend: <span style="background: #ffebee; padding: 2px 4px;">🔴 Incorrect/Different Line</span> <span style="background: #fff3e0; padding: 2px 4px;">⚠️ Extra Line</span></div>' if failure.get("expected_code") else ''}
                            <pre>{self._generate_code_diff_html(failure.get("generated_code", ""), failure.get("expected_code", ""))}</pre>
                        </div>
                        <div class="code-block">
                            <h4>{'Expected Code' if failure.get("expected_code") else 'Explanation'}</h4>
                            <pre>{self._escape_html(failure.get("expected_code") or failure.get("generated_explanation", "No explanation provided"))}</pre>
                        </div>
                    </div>
                    {self._build_compilation_error_section(failure.get("metrics", {}))}
                    {self._build_quality_metrics_section(failure.get("metrics", {}))}
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

    def _build_failure_explanation(self, result: Dict[str, Any]) -> str:
        """Build detailed failure explanation based on metrics and failure reason."""
        if result.get("passed", False):
            return ""

        metrics = result.get("metrics", {})
        failure_reason = result.get("failure_reason", "Unknown failure")

        explanation_parts = []

        # Main failure reason
        explanation_parts.append(f"<strong>Primary Issue:</strong> {failure_reason}")

        # Detailed breakdown based on metrics
        if not metrics.get("compiles", True):
            explanation_parts.append("<strong>Compilation:</strong> The generated code failed to compile. This indicates syntax errors or missing dependencies.")

        if not metrics.get("functional_correctness", True):
            explanation_parts.append("<strong>Functional Correctness:</strong> The code does not resolve the original static analysis violation.")

        if metrics.get("introduces_violations", False):
            violation_count = metrics.get("new_violation_count", 0)
            explanation_parts.append(f"<strong>New Violations:</strong> The generated code introduces {violation_count} new static analysis violation(s).")

        if metrics.get("high_severity_security", 0) > 0:
            security_count = metrics.get("high_severity_security", 0)
            explanation_parts.append(f"<strong>Security Issues:</strong> {security_count} high-severity security issue(s) detected in the generated code.")

        if not metrics.get("matches_expected", True) and "matches_expected" in metrics:
            explanation_parts.append("<strong>Expected Output:</strong> The generated code does not match the expected fix pattern.")

        # Add quality concerns if relevant
        if metrics.get("cyclomatic_complexity", 0) > 20:
            explanation_parts.append(f"<strong>Code Complexity:</strong> High cyclomatic complexity ({metrics['cyclomatic_complexity']}) may indicate overly complex code.")

        if len(explanation_parts) > 1:  # More than just the primary issue
            html = '<div style="margin-top: 15px; padding: 15px; background: #ffebee; border-left: 4px solid #f44336; border-radius: 4px;">'
            html += '<h4 style="margin: 0 0 10px 0; color: #c62828;">🔍 Failure Explanation</h4>'
            html += '<div style="line-height: 1.8;">'
            for part in explanation_parts:
                html += f'<div style="margin: 5px 0;">• {part}</div>'
            html += '</div></div>'
            return html

        return ""

    def _build_compilation_error_section(self, metrics: Dict[str, Any]) -> str:
        """Build compilation error display section."""
        compilation_error = metrics.get("compilation_error", "")

        if not compilation_error:
            return ""

        return f'''
        <div style="margin-top: 15px; padding: 15px; background: #fff3e0; border-left: 4px solid #ff9800; border-radius: 4px;">
            <h4 style="margin: 0 0 10px 0; color: #e65100;">⚠️ Compilation Error</h4>
            <pre style="background: #fff; padding: 10px; border-radius: 3px; overflow-x: auto; font-size: 11px; margin: 0;">{self._escape_html(compilation_error)}</pre>
        </div>
        '''

    def _build_quality_metrics_section(self, metrics: Dict[str, Any]) -> str:
        """Build quality metrics display section."""
        has_quality_metrics = any([
            metrics.get("cyclomatic_complexity") is not None,
            metrics.get("pylint_score") is not None,
            metrics.get("maintainability_index") is not None,
            metrics.get("style_violations") is not None
        ])

        if not has_quality_metrics:
            return ""

        quality_html = '<div style="margin-top: 15px; padding: 15px; background: #e8f5e9; border-left: 4px solid #4CAF50; border-radius: 4px;">'
        quality_html += '<h4 style="margin: 0 0 10px 0; color: #2e7d32;">📊 Code Quality Metrics</h4>'
        quality_html += '<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px;">'

        if metrics.get("cyclomatic_complexity") is not None:
            complexity = metrics["cyclomatic_complexity"]
            color = "#4CAF50" if complexity <= 10 else "#ff9800" if complexity <= 20 else "#f44336"
            quality_html += f'''
            <div style="background: #fff; padding: 10px; border-radius: 4px;">
                <div style="font-size: 12px; color: #666;">Cyclomatic Complexity</div>
                <div style="font-size: 20px; font-weight: bold; color: {color};">{complexity}</div>
            </div>
            '''

        if metrics.get("pylint_score") is not None:
            score = metrics["pylint_score"]
            color = "#4CAF50" if score >= 7.0 else "#ff9800" if score >= 5.0 else "#f44336"
            quality_html += f'''
            <div style="background: #fff; padding: 10px; border-radius: 4px;">
                <div style="font-size: 12px; color: #666;">Pylint Score</div>
                <div style="font-size: 20px; font-weight: bold; color: {color};">{score:.1f}/10</div>
            </div>
            '''

        if metrics.get("maintainability_index") is not None:
            mi = metrics["maintainability_index"]
            color = "#4CAF50" if mi >= 65 else "#ff9800" if mi >= 40 else "#f44336"
            quality_html += f'''
            <div style="background: #fff; padding: 10px; border-radius: 4px;">
                <div style="font-size: 12px; color: #666;">Maintainability Index</div>
                <div style="font-size: 20px; font-weight: bold; color: {color};">{mi:.1f}/100</div>
            </div>
            '''

        if metrics.get("style_violations") is not None:
            violations = metrics["style_violations"]
            color = "#4CAF50" if violations == 0 else "#ff9800"
            quality_html += f'''
            <div style="background: #fff; padding: 10px; border-radius: 4px;">
                <div style="font-size: 12px; color: #666;">Style Violations</div>
                <div style="font-size: 20px; font-weight: bold; color: {color};">{violations}</div>
            </div>
            '''

        quality_html += '</div></div>'
        return quality_html

    def _build_metric_details(self, metrics: Dict[str, Any]) -> str:
        """Build additional metric details for failure card."""
        details = []

        if metrics.get("compiles") is not None:
            details.append(f"Compiles: {'✓' if metrics['compiles'] else '✗'}")

        if metrics.get("functional_correctness") is not None:
            details.append(f"Functional: {'✓' if metrics['functional_correctness'] else '✗'}")

        if metrics.get("introduces_violations"):
            details.append(f"⚠️ Introduces {metrics.get('new_violation_count', 0)} new violations")

        # Quality metrics
        if metrics.get("cyclomatic_complexity") is not None:
            details.append(f"Complexity: {metrics['cyclomatic_complexity']}")

        if metrics.get("pylint_score") is not None:
            details.append(f"Pylint: {metrics['pylint_score']:.1f}/10")

        if metrics.get("maintainability_index") is not None:
            details.append(f"Maintainability: {metrics['maintainability_index']:.1f}/100")

        if metrics.get("style_violations") is not None and metrics['style_violations'] > 0:
            details.append(f"Style Issues: {metrics['style_violations']}")

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

    def _generate_code_diff_html(self, generated: str, expected: str) -> str:
        """
        Generate HTML showing code with highlighted differences.

        Args:
            generated: Generated code
            expected: Expected code

        Returns:
            HTML with highlighted differences
        """
        if not generated or not expected:
            return self._escape_html(generated or "N/A")

        gen_lines = generated.strip().split('\n')
        exp_lines = expected.strip().split('\n')

        # Simple line-by-line comparison
        html_lines = []
        max_lines = max(len(gen_lines), len(exp_lines))

        for i in range(max_lines):
            gen_line = gen_lines[i] if i < len(gen_lines) else None
            exp_line = exp_lines[i] if i < len(exp_lines) else None

            if gen_line is None:
                # Missing line in generated code
                html_lines.append(f'<span style="background-color: #ffebee; display: block; margin: 0; padding: 2px 0;">{self._escape_html("")}</span>')
            elif exp_line is None:
                # Extra line in generated code
                html_lines.append(f'<span style="background-color: #fff3e0; display: block; margin: 0; padding: 2px 0;">{self._escape_html(gen_line)}</span>')
            elif gen_line.strip() != exp_line.strip():
                # Different line
                html_lines.append(f'<span style="background-color: #ffebee; display: block; margin: 0; padding: 2px 0;">{self._escape_html(gen_line)}</span>')
            else:
                # Matching line
                html_lines.append(self._escape_html(gen_line))

        return '\n'.join(html_lines)

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
