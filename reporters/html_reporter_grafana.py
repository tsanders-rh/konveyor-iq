"""
Grafana-style HTML report generator with dark theme and modern visualizations.
"""
from typing import List, Dict, Any
from pathlib import Path
from datetime import datetime
import json


class HTMLReporterGrafana:
    """Generate Grafana-style dark-themed HTML evaluation reports."""

    def __init__(self, output_dir: str = "results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_report(
        self,
        results: List[Dict[str, Any]],
        config: Dict[str, Any]
    ) -> str:
        """
        Generate Grafana-style HTML report.

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
        """Build Grafana-style HTML report content."""

        # Aggregate data
        model_stats = self._aggregate_by_model(results)
        rule_stats = self._aggregate_by_rule(results)

        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Konveyor AI Evaluation Report</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: #111217;
            color: #d8d9da;
        }}

        .header {{
            background: #1e1e1e;
            padding: 15px 20px;
            border-bottom: 1px solid #2d2d2d;
        }}

        .header h1 {{
            font-size: 20px;
            font-weight: 500;
            color: #ffffff;
        }}

        .metadata {{
            background: #1e1e1e;
            padding: 10px 20px;
            border-bottom: 1px solid #2d2d2d;
            font-size: 13px;
            color: #9fa1a4;
        }}

        .metadata span {{
            margin-right: 25px;
        }}

        .dashboard {{
            padding: 20px;
        }}

        .row {{
            display: grid;
            gap: 15px;
            margin-bottom: 15px;
        }}

        .row-1 {{
            grid-template-columns: 1fr 1fr;
        }}

        .row-2 {{
            grid-template-columns: 1fr;
        }}

        .row-3 {{
            grid-template-columns: 1fr 1fr 1fr;
        }}

        .row-4 {{
            grid-template-columns: 1fr 1fr;
        }}

        .panel {{
            background: #181b1f;
            border: 1px solid #2d2d2d;
            border-radius: 2px;
            padding: 15px;
        }}

        .panel-title {{
            font-size: 14px;
            font-weight: 500;
            margin-bottom: 15px;
            color: #d8d9da;
        }}

        .stat-value {{
            font-size: 48px;
            font-weight: 300;
            margin-bottom: 10px;
            text-align: center;
        }}

        .stat-label {{
            font-size: 12px;
            color: #9fa1a4;
            text-align: center;
        }}

        .green {{ color: #73bf69; }}
        .yellow {{ color: #f2cc0c; }}
        .orange {{ color: #ff780a; }}
        .red {{ color: #f2495c; }}

        .stat-bg-green {{ background: rgba(115, 191, 105, 0.15); }}
        .stat-bg-yellow {{ background: rgba(242, 204, 12, 0.15); }}
        .stat-bg-orange {{ background: rgba(255, 120, 10, 0.15); }}
        .stat-bg-red {{ background: rgba(242, 73, 92, 0.15); }}

        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
        }}

        th {{
            background: #212124;
            padding: 8px;
            text-align: left;
            font-weight: 500;
            border-bottom: 1px solid #2d2d2d;
            color: #d8d9da;
        }}

        td {{
            padding: 8px;
            border-bottom: 1px solid #2d2d2d;
        }}

        tr:hover {{
            background: #212124;
        }}

        .badge {{
            display: inline-block;
            padding: 2px 8px;
            border-radius: 3px;
            font-size: 11px;
            font-weight: 500;
        }}

        .badge-green {{ background: rgba(115, 191, 105, 0.3); color: #73bf69; }}
        .badge-yellow {{ background: rgba(242, 204, 12, 0.3); color: #f2cc0c; }}
        .badge-orange {{ background: rgba(255, 120, 10, 0.3); color: #ff780a; }}
        .badge-red {{ background: rgba(242, 73, 92, 0.3); color: #f2495c; }}

        .chart-container {{
            position: relative;
            height: 250px;
        }}

        .chart-container-sm {{
            position: relative;
            height: 150px;
        }}

        .chart-container-lg {{
            position: relative;
            height: 350px;
        }}

        .test-details {{
            background: #212124;
            border: 1px solid #2d2d2d;
            border-radius: 3px;
            padding: 15px;
            margin: 10px 0;
            cursor: pointer;
        }}

        .test-details:hover {{
            background: #282a2e;
        }}

        .test-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        .test-title {{
            font-weight: 500;
            font-size: 14px;
        }}

        .test-content {{
            display: none;
            margin-top: 15px;
            padding-top: 15px;
            border-top: 1px solid #2d2d2d;
        }}

        .test-content.expanded {{
            display: block;
        }}

        .code-block {{
            background: #0d1117;
            border: 1px solid #2d2d2d;
            border-radius: 4px;
            padding: 12px;
            overflow-x: auto;
            margin: 10px 0;
        }}

        .code-block pre {{
            margin: 0;
            font-family: 'Courier New', monospace;
            font-size: 12px;
            color: #c9d1d9;
            white-space: pre-wrap;
        }}

        .code-header {{
            font-size: 12px;
            color: #9fa1a4;
            margin-bottom: 8px;
            font-weight: 500;
        }}

        .expand-icon {{
            transition: transform 0.3s;
            color: #9fa1a4;
        }}

        .expand-icon.expanded {{
            transform: rotate(180deg);
        }}

        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 10px;
            margin: 15px 0;
        }}

        .metric-item {{
            background: #0d1117;
            padding: 10px;
            border-radius: 4px;
            border: 1px solid #2d2d2d;
        }}

        .metric-item-label {{
            font-size: 11px;
            color: #9fa1a4;
            margin-bottom: 5px;
        }}

        .metric-item-value {{
            font-size: 16px;
            font-weight: 500;
        }}

        .filter-btn {{
            background: #212124;
            border: 1px solid #2d2d2d;
            color: #d8d9da;
            padding: 6px 12px;
            margin: 5px;
            border-radius: 3px;
            cursor: pointer;
            font-size: 13px;
        }}

        .filter-btn:hover {{
            background: #282a2e;
        }}

        .filter-btn.active {{
            background: #3d5afe;
            border-color: #3d5afe;
            color: white;
        }}
    </style>
</head>
<body>
    <div class="header">
        <div style="display: flex; align-items: center; justify-content: space-between;">
            <svg width="120" height="46" viewBox="0 0 575.19 221.79" xmlns="http://www.w3.org/2000/svg">
                <g transform="translate(-9.3672,-9.1211)">
                    <path d="m174.6 82.258h38.348v14.941h-38.348z"/>
                    <path d="m246.31 82.258h38.348v14.941h-38.348z"/>
                    <path d="m209.96 14.031h38.348v14.941h-38.348z"/>
                </g>
                <path d="m247.85 78.121h15.727c1.418 0 2.5586 1.1367 2.5586 2.5547s-1.1406 2.5586-2.5586 2.5586h-15.727c-1.418 0-2.5586-1.1406-2.5586-2.5586s1.1406-2.5547 2.5586-2.5547m-70.941 0h15.727c1.4141 0 2.5586 1.1367 2.5586 2.5547s-1.1445 2.5586-2.5586 2.5586h-15.727c-1.4141 0-2.5586-1.1406-2.5586-2.5586s1.1445-2.5547 2.5586-2.5547m47.938-8.7539c-0.8789 0-1.5859 0.70703-1.5859 1.582v61.738c0 0.87891 0.70703 1.5859 1.5859 1.5859h61.734c0.8789 0 1.582-0.71094 1.582-1.5859v-61.738c0-0.875-0.70313-1.582-1.582-1.582zm-70.945 0c-0.875 0-1.5781 0.70703-1.5781 1.582v61.738c0 0.87891 0.70312 1.5859 1.5781 1.5859h61.742c0.875 0 1.5781-0.71094 1.5781-1.5859v-61.738c0-0.875-0.70312-1.582-1.5781-1.582zm58.477-60.613h15.727c1.418 0 2.5586 1.1367 2.5586 2.5547s-1.1406 2.5586-2.5586 2.5586h-15.727c-1.418 0-2.5547-1.1406-2.5547-2.5586s1.1367-2.5547 2.5547-2.5547m-23.004-8.7539c-0.87891 0-1.5859 0.70703-1.5859 1.582v61.738c0 0.875 0.70703 1.5781 1.5859 1.5781h61.738c0.875 0 1.582-0.70312 1.582-1.5781v-61.738c0-0.875-0.70703-1.582-1.582-1.582z" fill="#b09454"/>
                <g transform="translate(-9.3672,-9.1211)" fill="#ffffff">
                    <path d="m110.98 164c13.109 0 23.523 10.414 23.523 23.523 0 13.113-10.414 23.523-23.523 23.523s-23.523-10.41-23.523-23.523c0-13.109 10.414-23.523 23.523-23.523m0-19.871c-23.848 0-43.395 19.547-43.395 43.395 0 23.852 19.547 43.395 43.395 43.395 23.852 0 43.398-19.543 43.398-43.395 0-23.848-19.547-43.395-43.398-43.395"/>
                    <path d="m9.3672 224.48v-73.914h20.301v28.109l22.488-28.109h22.902l-26.859 33.105 28.734 40.809h-23.32l-18.324-27.172-5.6211 5.832v21.34z"/>
                    <path d="m181.01 188.14v36.332h-20.301v-73.914h15.824l29.672 37.582v-37.582h20.301v73.914h-16.137z"/>
                    <path d="m253.47 150.56 14.469 48.41 14.266-48.41h21.34l-27.172 73.914h-16.863l-27.484-73.914z"/>
                    <path d="m361.84 206.78v17.695h-52.676v-73.914h51.742v17.699h-31.441v10.41h26.859v16.449h-26.859v11.66z"/>
                    <path d="m386.3 150.56 13.223 31.961 13.531-31.961h22.07l-25.504 49.449v24.465h-20.195v-24.672l-25.09-49.242z"/>
                    <path d="m541.04 184.09h12.805c1.25 0 2.3945-0.69532 3.4375-2.082 1.1094-1.3906 1.6641-3.332 1.6641-5.832 0-2.5664-0.625-4.5117-1.875-5.8281-1.2461-1.3867-2.4961-2.082-3.7461-2.082h-12.285zm-20.301 40.391v-73.914h33.938c3.6094 0 6.9414 0.76562 9.9961 2.293 3.0547 1.457 5.6562 3.3984 7.8086 5.8281 2.2188 2.3594 3.9531 5.1016 5.2031 8.2227 1.25 3.0547 1.875 6.1445 1.875 9.2656 0 4.3047-0.9375 8.3281-2.8125 12.078-1.8711 3.6797-4.4766 6.6953-7.8086 9.0586l15.617 27.168h-22.902l-13.012-22.695h-7.6016v22.695z"/>
                    <path d="m471.77 164c13.109 0 23.523 10.414 23.523 23.523 0 13.113-10.414 23.523-23.523 23.523s-23.523-10.41-23.523-23.523c0-13.109 10.414-23.523 23.523-23.523m0-19.871c-23.848 0-43.395 19.547-43.395 43.395 0 23.852 19.547 43.395 43.395 43.395 23.852 0 43.398-19.543 43.398-43.395 0-23.848-19.547-43.395-43.398-43.395"/>
                </g>
            </svg>
            <h1>AI Evaluation Report</h1>
        </div>
    </div>

    <div class="metadata">
        <span><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</span>
        <span><strong>Test Suite:</strong> {config.get('test_suite', 'Unknown')}</span>
        <span><strong>Total Evaluations:</strong> {len(results)}</span>
        <span><strong>Models:</strong> {len(model_stats)}</span>
    </div>

    <div class="dashboard">
        <!-- Row 1: Summary Stats -->
        <div class="row row-3">
            {self._build_summary_stats(results, model_stats)}
        </div>

        <!-- Row 1.5: Top Performing Models -->
        <div class="row row-2">
            <div class="panel">
                <div class="panel-title">🏆 Top Performing Models</div>
                {self._build_top_performers_section(model_stats)}
            </div>
        </div>

        <!-- Row 2: Model Performance Comparison -->
        <div class="row row-2">
            <div class="panel">
                <div class="panel-title">Model Pass Rate Comparison</div>
                <div class="chart-container">
                    <canvas id="modelPassRateChart"></canvas>
                </div>
            </div>
        </div>

        <!-- Row 3: Performance by Rule -->
        <div class="row row-2">
            <div class="panel">
                <div class="panel-title">Performance by Rule</div>
                <div style="margin-bottom: 15px;">
                    <label for="rule-selector" style="font-weight: 500; margin-right: 10px; color: #d8d9da;">Select Rule:</label>
                    <select id="rule-selector" style="padding: 8px 12px; font-size: 14px; border: 1px solid #2d2d2d; border-radius: 4px; min-width: 300px; background: #212124; color: #d8d9da;">
                        <option value="all">All Rules - Summary</option>
                    </select>
                </div>
                <div class="chart-container">
                    <canvas id="rulePerformanceChart"></canvas>
                </div>
            </div>
        </div>

        <!-- Row 4: Cost and Response Time -->
        <div class="row row-4">
            <div class="panel">
                <div class="panel-title">Response Time Distribution</div>
                <div class="chart-container">
                    <canvas id="responseTimeChart"></canvas>
                </div>
            </div>

            <div class="panel">
                <div class="panel-title">Cost by Model</div>
                <div class="chart-container">
                    <canvas id="costChart"></canvas>
                </div>
            </div>
        </div>

        <!-- Row 5: Detailed Results Table -->
        <div class="row row-2">
            <div class="panel">
                <div class="panel-title">Model Summary</div>
                {self._build_model_summary_table(model_stats)}
            </div>
        </div>

        <!-- Row 6: All Test Results -->
        <div class="row row-2">
            <div class="panel">
                <div class="panel-title">Test Results</div>
                <div style="margin-bottom: 15px;">
                    <button class="filter-btn active" onclick="filterTests('all')">All ({len(results)})</button>
                    <button class="filter-btn" onclick="filterTests('passed')">Passed ({sum(1 for r in results if r.get('passed', False))})</button>
                    <button class="filter-btn" onclick="filterTests('failed')">Failed ({sum(1 for r in results if not r.get('passed', False))})</button>
                </div>
                <div id="test-results">
                    {self._build_test_results(results)}
                </div>
            </div>
        </div>
    </div>

    <script>
        {self._build_charts_script(results, model_stats, rule_stats)}
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
                    "response_times": [],
                    "costs": [],
                    "complexities": [],
                    "pylint_scores": [],
                    "maintainability_scores": [],
                    "security_issues": [],
                    "explanation_scores": [],
                    "comment_densities": []
                }

            stats = model_stats[model_name]
            stats["total"] += 1

            if result.get("passed", False):
                stats["passed"] += 1
            else:
                stats["failed"] += 1

            # Track compilation success
            if result.get("metrics", {}).get("compiles", False):
                stats["compiled"] += 1

            stats["response_times"].append(result.get("metrics", {}).get("response_time_ms", 0))
            stats["costs"].append(result.get("estimated_cost", 0))

            # Collect quality metrics
            metrics = result.get("metrics", {})
            if metrics.get("cyclomatic_complexity") is not None:
                stats["complexities"].append(metrics["cyclomatic_complexity"])
            if metrics.get("pylint_score") is not None:
                stats["pylint_scores"].append(metrics["pylint_score"])
            if metrics.get("maintainability_index") is not None:
                stats["maintainability_scores"].append(metrics["maintainability_index"])

            # Collect security metrics
            if metrics.get("security_issues") is not None:
                stats["security_issues"].append(metrics["security_issues"])

            # Collect explainability metrics
            if metrics.get("explanation_quality_score") is not None:
                stats["explanation_scores"].append(metrics["explanation_quality_score"])
            if metrics.get("comment_density") is not None:
                stats["comment_densities"].append(metrics["comment_density"])

        return model_stats

    def _aggregate_by_rule(
        self,
        results: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """Aggregate results by rule."""

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

        return rule_stats

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
            avg_security_issues = sum(stats["security_issues"]) / len(stats["security_issues"]) if stats["security_issues"] else None
            avg_explanation_score = sum(stats["explanation_scores"]) / len(stats["explanation_scores"]) if stats["explanation_scores"] else None
            avg_comment_density = sum(stats["comment_densities"]) / len(stats["comment_densities"]) if stats["comment_densities"] else None

            # Calculate composite score (0-100)
            # Weighted scoring: pass_rate (40%), compile_rate (15%), quality (15%), security (15%), explainability (10%), speed (2.5%), cost (2.5%)
            score = 0

            # Pass rate (most important)
            score += pass_rate * 0.4

            # Compilation rate
            score += compile_rate * 0.15

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
                score += (quality_score / quality_count) * 0.15

            # Security metrics (lower issues is better)
            if avg_security_issues is not None:
                # Assume 0 issues = 100 score, 5+ issues = 0 score
                security_score = max(0, 100 - (avg_security_issues * 20))
                score += security_score * 0.15

            # Explainability metrics (average of available metrics)
            explainability_score = 0
            explainability_count = 0

            if avg_explanation_score is not None:
                # Higher is better, scale 0-10 to 0-100
                explainability_score += avg_explanation_score * 10
                explainability_count += 1

            if avg_comment_density is not None:
                # Ideal range 10-30%, convert to 0-100 score
                percentage = avg_comment_density * 100
                if 10 <= percentage <= 30:
                    density_score = 100
                elif percentage > 30:
                    # Penalize over-commenting: 30% = 100, 60% = 0
                    density_score = max(0, 100 - (percentage - 30) * 3.33)
                elif percentage > 0:
                    # Penalize under-commenting: 10% = 100, 0% = 0
                    density_score = percentage * 10
                else:
                    density_score = 0
                explainability_score += density_score
                explainability_count += 1

            if explainability_count > 0:
                score += (explainability_score / explainability_count) * 0.1

            # Response time (lower is better, normalize to 0-100)
            # Assume 10000ms is max acceptable response time
            time_score = max(0, 100 - (avg_response_time / 100))
            score += time_score * 0.025

            # Cost (lower is better, normalize to 0-100)
            # Assume $1.00 total is max acceptable cost
            cost_score = max(0, 100 - (total_cost * 100)) if total_cost > 0 else 100
            score += cost_score * 0.025

            rankings.append({
                "model_name": model_name,
                "score": score,
                "pass_rate": pass_rate,
                "compile_rate": compile_rate,
                "avg_response_time": avg_response_time,
                "total_cost": total_cost,
                "avg_complexity": avg_complexity,
                "avg_maintainability": avg_maintainability,
                "avg_security_issues": avg_security_issues,
                "avg_explanation_score": avg_explanation_score,
                "avg_comment_density": avg_comment_density,
                "tests_passed": stats["passed"],
                "tests_total": stats["total"]
            })

        # Sort by score descending
        rankings.sort(key=lambda x: x["score"], reverse=True)
        return rankings

    def _build_top_performers_section(self, model_stats: Dict[str, Dict[str, Any]]) -> str:
        """Build top performing models section with Grafana dark theme."""
        rankings = self._rank_models(model_stats)

        if not rankings:
            return "<p>No rankings available.</p>"

        html = '<div style="margin: 20px 0;">'

        # Show podium for top 3
        for i, ranking in enumerate(rankings[:3]):
            rank = i + 1
            medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉"
            # Grafana color scheme
            border_color = "#f2cc0c" if rank == 1 else "#9fa1a4" if rank == 2 else "#ff780a"

            html += f'''
            <div style="background: #1e1e1e; border: 2px solid {border_color}; border-radius: 4px; padding: 20px; margin: 15px 0;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <span style="font-size: 32px; margin-right: 10px;">{medal}</span>
                        <span style="font-size: 24px; font-weight: bold; color: #d8d9da;">{ranking["model_name"]}</span>
                    </div>
                    <div style="text-align: right;">
                        <div style="font-size: 36px; font-weight: bold; color: {border_color};">{ranking["score"]:.1f}</div>
                        <div style="font-size: 12px; color: #9fa1a4;">Overall Score</div>
                    </div>
                </div>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; margin-top: 15px; padding-top: 15px; border-top: 1px solid #2d2d2d;">
                    <div>
                        <div style="font-size: 12px; color: #9fa1a4;">Pass Rate</div>
                        <div style="font-size: 20px; font-weight: bold; color: #73bf69;">{ranking["pass_rate"]:.1f}%</div>
                        <div style="font-size: 11px; color: #6e7074;">{ranking["tests_passed"]}/{ranking["tests_total"]} passed</div>
                    </div>
                    <div>
                        <div style="font-size: 12px; color: #9fa1a4;">Compilation Rate</div>
                        <div style="font-size: 20px; font-weight: bold; color: #73bf69;">{ranking["compile_rate"]:.1f}%</div>
                    </div>
                    <div>
                        <div style="font-size: 12px; color: #9fa1a4;">Avg Response Time</div>
                        <div style="font-size: 20px; font-weight: bold; color: #729fcf;">{ranking["avg_response_time"]:.0f}ms</div>
                    </div>
                    <div>
                        <div style="font-size: 12px; color: #9fa1a4;">Total Cost</div>
                        <div style="font-size: 20px; font-weight: bold; color: #ff780a;">${ranking["total_cost"]:.4f}</div>
                    </div>
            '''

            # Add quality metrics if available
            if ranking["avg_complexity"] is not None:
                html += f'''
                    <div>
                        <div style="font-size: 12px; color: #9fa1a4;">Avg Complexity</div>
                        <div style="font-size: 20px; font-weight: bold; color: #b09bf5;">{ranking["avg_complexity"]:.1f}</div>
                    </div>
                '''

            if ranking["avg_maintainability"] is not None:
                html += f'''
                    <div>
                        <div style="font-size: 12px; color: #9fa1a4;">Maintainability</div>
                        <div style="font-size: 20px; font-weight: bold; color: #56d9fe;">{ranking["avg_maintainability"]:.1f}/100</div>
                    </div>
                '''

            # Add security metrics if available
            if ranking["avg_security_issues"] is not None:
                security_color = "#73bf69" if ranking["avg_security_issues"] == 0 else "#ff780a" if ranking["avg_security_issues"] < 2 else "#f2495c"
                html += f'''
                    <div>
                        <div style="font-size: 12px; color: #9fa1a4;">Avg Security Issues</div>
                        <div style="font-size: 20px; font-weight: bold; color: {security_color};">{ranking["avg_security_issues"]:.1f}</div>
                    </div>
                '''

            # Add explainability metrics if available
            if ranking["avg_explanation_score"] is not None:
                expl_color = "#73bf69" if ranking["avg_explanation_score"] >= 7.0 else "#ff780a" if ranking["avg_explanation_score"] >= 5.0 else "#f2495c"
                html += f'''
                    <div>
                        <div style="font-size: 12px; color: #9fa1a4;">Explanation Quality</div>
                        <div style="font-size: 20px; font-weight: bold; color: {expl_color};">{ranking["avg_explanation_score"]:.1f}/10</div>
                    </div>
                '''

            if ranking["avg_comment_density"] is not None:
                percentage = ranking["avg_comment_density"] * 100
                comment_color = "#73bf69" if 10 <= percentage <= 30 else "#ff780a"
                html += f'''
                    <div>
                        <div style="font-size: 12px; color: #9fa1a4;">Comment Density</div>
                        <div style="font-size: 20px; font-weight: bold; color: {comment_color};">{percentage:.1f}%</div>
                    </div>
                '''

            html += '''
                </div>
            </div>
            '''

        # Show remaining models in a compact table
        if len(rankings) > 3:
            html += '<div style="margin-top: 20px;"><h3 style="color: #9fa1a4; font-size: 18px;">Other Models</h3>'
            html += '<table style="width: 100%; border-collapse: collapse;">'
            html += '''
            <thead>
                <tr style="background: #212124;">
                    <th style="padding: 10px; text-align: left; color: #d8d9da; border-bottom: 1px solid #2d2d2d;">Rank</th>
                    <th style="padding: 10px; text-align: left; color: #d8d9da; border-bottom: 1px solid #2d2d2d;">Model</th>
                    <th style="padding: 10px; text-align: right; color: #d8d9da; border-bottom: 1px solid #2d2d2d;">Score</th>
                    <th style="padding: 10px; text-align: right; color: #d8d9da; border-bottom: 1px solid #2d2d2d;">Pass Rate</th>
                    <th style="padding: 10px; text-align: right; color: #d8d9da; border-bottom: 1px solid #2d2d2d;">Compile Rate</th>
                    <th style="padding: 10px; text-align: right; color: #d8d9da; border-bottom: 1px solid #2d2d2d;">Avg Response</th>
                    <th style="padding: 10px; text-align: right; color: #d8d9da; border-bottom: 1px solid #2d2d2d;">Cost</th>
                </tr>
            </thead>
            <tbody>
            '''

            for i, ranking in enumerate(rankings[3:], start=4):
                html += f'''
                <tr style="border-bottom: 1px solid #2d2d2d;">
                    <td style="padding: 10px; color: #d8d9da;">#{i}</td>
                    <td style="padding: 10px; font-weight: 500; color: #d8d9da;">{ranking["model_name"]}</td>
                    <td style="padding: 10px; text-align: right; font-weight: bold; color: #d8d9da;">{ranking["score"]:.1f}</td>
                    <td style="padding: 10px; text-align: right; color: #d8d9da;">{ranking["pass_rate"]:.1f}%</td>
                    <td style="padding: 10px; text-align: right; color: #d8d9da;">{ranking["compile_rate"]:.1f}%</td>
                    <td style="padding: 10px; text-align: right; color: #d8d9da;">{ranking["avg_response_time"]:.0f}ms</td>
                    <td style="padding: 10px; text-align: right; color: #d8d9da;">${ranking["total_cost"]:.4f}</td>
                </tr>
                '''

            html += '</tbody></table></div>'

        html += '</div>'
        return html

    def _build_summary_stats(
        self,
        results: List[Dict[str, Any]],
        model_stats: Dict[str, Dict[str, Any]]
    ) -> str:
        """Build summary stat panels."""

        total_tests = len(results)
        total_passed = sum(1 for r in results if r.get("passed", False))
        total_cost = sum(r.get("estimated_cost", 0) for r in results)

        pass_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0

        # Determine colors
        pass_color = "green" if pass_rate >= 85 else "yellow" if pass_rate >= 70 else "orange" if pass_rate >= 50 else "red"
        cost_color = "green" if total_cost < 1.0 else "yellow" if total_cost < 5.0 else "orange" if total_cost < 10.0 else "red"

        return f"""
        <div class="panel stat-bg-{pass_color}">
            <div class="panel-title">Pass Rate</div>
            <div class="stat-value {pass_color}">{pass_rate:.1f}%</div>
            <div class="stat-label">{total_passed} of {total_tests} tests passed</div>
        </div>

        <div class="panel">
            <div class="panel-title">Total Tests</div>
            <div class="stat-value">{total_tests}</div>
            <div class="stat-label">{len(model_stats)} models evaluated</div>
        </div>

        <div class="panel stat-bg-{cost_color}">
            <div class="panel-title">Total Cost</div>
            <div class="stat-value {cost_color}">${total_cost:.3f}</div>
            <div class="stat-label">API costs for all evaluations</div>
        </div>
        """

    def _build_model_summary_table(
        self,
        model_stats: Dict[str, Dict[str, Any]]
    ) -> str:
        """Build model summary table."""

        rows = []

        for model_name, stats in model_stats.items():
            pass_rate = (stats["passed"] / stats["total"] * 100) if stats["total"] > 0 else 0
            avg_response = sum(stats["response_times"]) / len(stats["response_times"]) if stats["response_times"] else 0
            total_cost = sum(stats["costs"])

            pass_color = "green" if pass_rate >= 85 else "yellow" if pass_rate >= 70 else "orange" if pass_rate >= 50 else "red"

            rows.append(f"""
                <tr>
                    <td>{model_name}</td>
                    <td>{stats["total"]}</td>
                    <td><span class="badge badge-{pass_color}">{stats["passed"]}</span></td>
                    <td><span class="badge badge-red">{stats["failed"]}</span></td>
                    <td><span class="{pass_color}">{pass_rate:.1f}%</span></td>
                    <td>{avg_response:.0f}ms</td>
                    <td>${total_cost:.4f}</td>
                </tr>
            """)

        return f"""
        <table>
            <thead>
                <tr>
                    <th>Model</th>
                    <th>Total</th>
                    <th>Passed</th>
                    <th>Failed</th>
                    <th>Pass Rate</th>
                    <th>Avg Response</th>
                    <th>Total Cost</th>
                </tr>
            </thead>
            <tbody>
                {''.join(rows)}
            </tbody>
        </table>
        """

    def _build_test_results(self, results: List[Dict[str, Any]]) -> str:
        """Build collapsible test results."""

        html = ""

        for i, result in enumerate(results):
            passed = result.get("passed", False)
            status_class = "passed" if passed else "failed"
            status_icon = "✓" if passed else "✗"
            status_color = "green" if passed else "red"

            failure_reason = result.get("failure_reason", "Test failed") if not passed else "Test passed"

            html += f"""
            <div class="test-details" data-status="{status_class}" onclick="toggleTest({i})">
                <div class="test-header">
                    <div class="test-title">
                        <span class="{status_color}">{status_icon}</span>
                        {result.get("model_name", "Unknown")} -
                        {result.get("rule_id", "Unknown")} -
                        {result.get("test_case_id", "Unknown")}
                    </div>
                    <div>
                        <span class="badge badge-{status_color}">{status_class.upper()}</span>
                        <span class="expand-icon" id="test-icon-{i}">▼</span>
                    </div>
                </div>

                <div style="margin-top: 5px; font-size: 12px; color: #9fa1a4;">
                    {failure_reason}
                </div>

                <div class="test-content" id="test-content-{i}">
                    <div class="metrics-grid">
                        {self._build_metrics_grid(result.get("metrics", {}))}
                        <div class="metric-item">
                            <div class="metric-item-label">Cost</div>
                            <div class="metric-item-value">${result.get("estimated_cost", 0):.4f}</div>
                        </div>
                    </div>

                    <div class="code-header">Generated Code</div>
                    <div class="code-block">
                        <pre>{self._escape_html(result.get("generated_code", "N/A"))}</pre>
                    </div>

                    {self._build_expected_code_section(result)}
                    {self._build_explanation_section(result)}
                    {self._build_security_issues_section(result.get("metrics", {}))}
                </div>
            </div>
            """

        return html

    def _build_metrics_grid(self, metrics: Dict[str, Any]) -> str:
        """Build metrics grid."""

        html = ""

        # Response time
        response_time = metrics.get("response_time_ms", 0)
        html += f"""
        <div class="metric-item">
            <div class="metric-item-label">Response Time</div>
            <div class="metric-item-value">{response_time:.0f}ms</div>
        </div>
        """

        # Compilation
        if "compiles" in metrics:
            compiles = metrics["compiles"]
            color = "green" if compiles else "red"
            value = "✓" if compiles else "✗"
            html += f"""
            <div class="metric-item">
                <div class="metric-item-label">Compiles</div>
                <div class="metric-item-value {color}">{value}</div>
            </div>
            """

        # Functional correctness
        if "functional_correctness" in metrics:
            correct = metrics["functional_correctness"]
            color = "green" if correct else "red"
            value = "✓" if correct else "✗"
            html += f"""
            <div class="metric-item">
                <div class="metric-item-label">Functional</div>
                <div class="metric-item-value {color}">{value}</div>
            </div>
            """

        # Security issues
        if "security_issues" in metrics:
            issues = metrics["security_issues"]
            color = "green" if issues == 0 else "orange" if issues < 3 else "red"
            html += f"""
            <div class="metric-item">
                <div class="metric-item-label">Security Issues</div>
                <div class="metric-item-value {color}">{issues}</div>
            </div>
            """

        return html

    def _build_expected_code_section(self, result: Dict[str, Any]) -> str:
        """Build expected code section if available."""

        expected = result.get("expected_code")
        if not expected:
            return ""

        return f"""
        <div class="code-header">Expected Code</div>
        <div class="code-block">
            <pre>{self._escape_html(expected)}</pre>
        </div>
        """

    def _build_explanation_section(self, result: Dict[str, Any]) -> str:
        """Build explanation section if available."""

        explanation = result.get("generated_explanation")
        if not explanation:
            return ""

        return f"""
        <div class="code-header">Explanation</div>
        <div class="code-block">
            <pre>{self._escape_html(explanation)}</pre>
        </div>
        """

    def _build_security_issues_section(self, metrics: Dict[str, Any]) -> str:
        """Build security issues display section (Grafana dark theme)."""
        security_issues = metrics.get("security_issues", 0)
        issues = metrics.get("issues", [])

        if security_issues == 0 or not issues:
            return ""

        # Build issues list
        issues_html = []
        for issue in issues:
            severity = issue.get("severity", "UNKNOWN")
            issue_type = issue.get("type", "UNKNOWN")
            description = issue.get("description", "No description")
            line = issue.get("line")

            # Color code by severity (Grafana-style)
            if severity == "HIGH":
                severity_color = "#f2495c"  # Red
                severity_bg = "rgba(242, 73, 92, 0.15)"
            elif severity == "MEDIUM":
                severity_color = "#ff780a"  # Orange
                severity_bg = "rgba(255, 120, 10, 0.15)"
            else:
                severity_color = "#f2cc0c"  # Yellow
                severity_bg = "rgba(242, 204, 12, 0.15)"

            line_info = f" (Line {line})" if line else ""

            issues_html.append(f'''
            <div style="margin: 10px 0; padding: 12px; background: {severity_bg}; border-left: 3px solid {severity_color}; border-radius: 4px; border: 1px solid #2d2d2d;">
                <div style="display: flex; align-items: center; margin-bottom: 5px;">
                    <span style="background: {severity_color}; color: #0d1117; padding: 2px 8px; border-radius: 3px; font-size: 11px; font-weight: bold; margin-right: 10px;">{severity}</span>
                    <span style="font-weight: bold; color: {severity_color};">{issue_type}</span>
                    <span style="color: #9fa1a4; font-size: 12px; margin-left: auto;">{line_info}</span>
                </div>
                <div style="color: #d8d9da; font-size: 13px;">{self._escape_html(description)}</div>
            </div>
            ''')

        return f'''
        <div style="margin-top: 15px; padding: 15px; background: rgba(242, 73, 92, 0.1); border-left: 4px solid #f2495c; border-radius: 4px; border: 1px solid #2d2d2d;">
            <div class="code-header" style="color: #f2495c; font-weight: 600;">🔒 Security Issues Found ({security_issues})</div>
            {''.join(issues_html)}
        </div>
        '''

    def _build_charts_script(
        self,
        results: List[Dict[str, Any]],
        model_stats: Dict[str, Dict[str, Any]],
        rule_stats: Dict[str, Dict[str, Any]]
    ) -> str:
        """Build JavaScript for charts."""

        # Model pass rate data
        models = list(model_stats.keys())
        pass_rates = [
            (stats["passed"] / stats["total"] * 100) if stats["total"] > 0 else 0
            for stats in model_stats.values()
        ]

        # Rule performance data
        rules = sorted(rule_stats.keys())
        rule_pass_rates = {}
        for model in models:
            rule_pass_rates[model] = []
            for rule in rules:
                if model in rule_stats.get(rule, {}):
                    stats = rule_stats[rule][model]
                    rate = (stats["passed"] / stats["total"] * 100) if stats["total"] > 0 else 0
                    rule_pass_rates[model].append(rate)
                else:
                    rule_pass_rates[model].append(0)

        # Response time data
        response_times = {model: stats["response_times"] for model, stats in model_stats.items()}

        # Cost data
        costs = [sum(stats["costs"]) for stats in model_stats.values()]

        return f"""
        // Model pass rate chart
        const modelPassRateCtx = document.getElementById('modelPassRateChart').getContext('2d');
        new Chart(modelPassRateCtx, {{
            type: 'bar',
            data: {{
                labels: {json.dumps(models)},
                datasets: [{{
                    label: 'Pass Rate',
                    data: {json.dumps(pass_rates)},
                    backgroundColor: 'rgba(115, 191, 105, 0.6)',
                    borderColor: 'rgba(115, 191, 105, 1)',
                    borderWidth: 1
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{ display: false }},
                    tooltip: {{
                        callbacks: {{
                            label: function(context) {{
                                return context.parsed.y.toFixed(1) + '%';
                            }}
                        }}
                    }}
                }},
                scales: {{
                    y: {{
                        beginAtZero: true,
                        max: 100,
                        ticks: {{
                            callback: function(value) {{
                                return value + '%';
                            }},
                            color: '#9fa1a4'
                        }},
                        grid: {{ color: '#2d2d2d' }}
                    }},
                    x: {{
                        ticks: {{ color: '#9fa1a4' }},
                        grid: {{ color: '#2d2d2d' }}
                    }}
                }}
            }}
        }});

        // Rule performance chart with dropdown selector
        {self._build_per_rule_chart_data(results, models)}

        // Response time chart
        const responseTimeCtx = document.getElementById('responseTimeChart').getContext('2d');
        new Chart(responseTimeCtx, {{
            type: 'line',
            data: {{
                labels: Array.from({{ length: Math.max(...{json.dumps([len(times) for times in response_times.values()])}) }}, (_, i) => i + 1),
                datasets: {json.dumps([
                    {
                        "label": model,
                        "data": times,
                        "borderColor": f"rgba({115 if i == 0 else 242 if i == 1 else 114}, {191 if i == 0 else 204 if i == 1 else 159}, {105 if i == 0 else 12 if i == 1 else 207}, 1)",
                        "backgroundColor": f"rgba({115 if i == 0 else 242 if i == 1 else 114}, {191 if i == 0 else 204 if i == 1 else 159}, {105 if i == 0 else 12 if i == 1 else 207}, 0.1)",
                        "tension": 0.4,
                        "fill": True
                    }
                    for i, (model, times) in enumerate(response_times.items())
                ])}
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{
                        position: 'top',
                        labels: {{ color: '#d8d9da', padding: 15 }}
                    }}
                }},
                scales: {{
                    y: {{
                        beginAtZero: true,
                        ticks: {{
                            callback: function(value) {{
                                return value + 'ms';
                            }},
                            color: '#9fa1a4'
                        }},
                        grid: {{ color: '#2d2d2d' }}
                    }},
                    x: {{
                        ticks: {{ color: '#9fa1a4' }},
                        grid: {{ color: '#2d2d2d' }}
                    }}
                }}
            }}
        }});

        // Cost chart
        const costCtx = document.getElementById('costChart').getContext('2d');
        new Chart(costCtx, {{
            type: 'bar',
            data: {{
                labels: {json.dumps(models)},
                datasets: [{{
                    label: 'Total Cost',
                    data: {json.dumps(costs)},
                    backgroundColor: 'rgba(255, 120, 10, 0.6)',
                    borderColor: 'rgba(255, 120, 10, 1)',
                    borderWidth: 1
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{ display: false }},
                    tooltip: {{
                        callbacks: {{
                            label: function(context) {{
                                return '$' + context.parsed.y.toFixed(4);
                            }}
                        }}
                    }}
                }},
                scales: {{
                    y: {{
                        beginAtZero: true,
                        ticks: {{
                            callback: function(value) {{
                                return '$' + value.toFixed(3);
                            }},
                            color: '#9fa1a4'
                        }},
                        grid: {{ color: '#2d2d2d' }}
                    }},
                    x: {{
                        ticks: {{ color: '#9fa1a4' }},
                        grid: {{ color: '#2d2d2d' }}
                    }}
                }}
            }}
        }});
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

        # Calculate average pass rate per rule (across all models)
        rule_avg_pass_rates = {}
        for rule_id in sorted_rules:
            total_tests = 0
            total_passed = 0
            for model in models:
                if model in rule_stats[rule_id]:
                    total_tests += rule_stats[rule_id][model]["total"]
                    total_passed += rule_stats[rule_id][model]["passed"]
            avg_pass_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
            rule_avg_pass_rates[rule_id] = avg_pass_rate

        # Sort rules by pass rate (ascending) to identify worst performers
        sorted_by_performance = sorted(rule_avg_pass_rates.items(), key=lambda x: x[1])

        # For "all rules" view, show top 10 worst performing rules
        worst_10_rules = [rule_id for rule_id, _ in sorted_by_performance[:10]]

        # Build "all" view with worst 10 rules
        all_traces = []
        for model in models:
            rule_ids = []
            pass_rates = []

            for rule_id in worst_10_rules:
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

        # For individual rules, show model performance
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
        var ruleAvgPassRates = {json.dumps(rule_avg_pass_rates)};

        // Populate dropdown
        var selector = document.getElementById('rule-selector');
        ruleIds.forEach(function(ruleId) {{
            var option = document.createElement('option');
            option.value = ruleId;
            var avgRate = ruleAvgPassRates[ruleId].toFixed(1);
            option.textContent = ruleId + ' (' + avgRate + '% avg pass rate)';
            selector.appendChild(option);
        }});

        // Initial chart layout
        var rulePerformanceLayout = {{
            title: {{
                text: 'Pass Rate by Rule (Top 10 Worst Performing)',
                font: {{ color: '#d8d9da' }}
            }},
            xaxis: {{
                title: {{ text: 'Rule ID', font: {{ color: '#d8d9da' }} }},
                tickangle: -45,
                tickfont: {{ color: '#9fa1a4' }},
                gridcolor: '#2d2d2d'
            }},
            yaxis: {{
                title: {{ text: 'Pass Rate (%)', font: {{ color: '#d8d9da' }} }},
                range: [0, 100],
                tickfont: {{ color: '#9fa1a4' }},
                gridcolor: '#2d2d2d'
            }},
            barmode: 'group',
            plot_bgcolor: '#181b1f',
            paper_bgcolor: '#181b1f',
            legend: {{
                font: {{ color: '#d8d9da' }}
            }}
        }};

        // Chart.js colors for models
        const modelColors = [
            {{ bg: 'rgba(115, 191, 105, 0.6)', border: 'rgba(115, 191, 105, 1)' }},  // Green
            {{ bg: 'rgba(242, 204, 12, 0.6)', border: 'rgba(242, 204, 12, 1)' }},    // Yellow
            {{ bg: 'rgba(114, 159, 207, 0.6)', border: 'rgba(114, 159, 207, 1)' }}   // Blue
        ];

        // Function to update chart based on selection
        function updateRuleChart(selectedRule) {{
            var data = allRuleData[selectedRule];

            if (selectedRule === 'all') {{
                rulePerformanceLayout.title.text = 'Pass Rate by Rule (Top 10 Worst Performing)';
                rulePerformanceLayout.xaxis.title.text = 'Rule ID';
                rulePerformanceLayout.barmode = 'group';
                rulePerformanceLayout.showlegend = true;
            }} else {{
                var avgRate = ruleAvgPassRates[selectedRule].toFixed(1);
                rulePerformanceLayout.title.text = selectedRule + ' - Pass Rate by Model (Avg: ' + avgRate + '%)';
                rulePerformanceLayout.xaxis.title.text = 'Model';
                rulePerformanceLayout.barmode = 'group';
                rulePerformanceLayout.showlegend = false;
            }}

            // Convert to Chart.js format
            const ctx = document.getElementById('rulePerformanceChart').getContext('2d');

            // Destroy existing chart if it exists
            if (window.ruleChart) {{
                window.ruleChart.destroy();
            }}

            // Extract labels and datasets
            let labels = [];
            let datasets = [];

            if (selectedRule === 'all') {{
                // Multiple models, multiple rules
                labels = data[0].x;
                datasets = data.map((trace, idx) => ({{
                    label: trace.name,
                    data: trace.y,
                    backgroundColor: modelColors[idx % modelColors.length].bg,
                    borderColor: modelColors[idx % modelColors.length].border,
                    borderWidth: 1
                }}));
            }} else {{
                // Multiple models, single rule
                labels = data.map(trace => trace.x[0]);
                datasets = [{{
                    label: 'Pass Rate',
                    data: data.map(trace => trace.y[0]),
                    backgroundColor: modelColors.map(c => c.bg),
                    borderColor: modelColors.map(c => c.border),
                    borderWidth: 1
                }}];
            }}

            window.ruleChart = new Chart(ctx, {{
                type: 'bar',
                data: {{
                    labels: labels,
                    datasets: datasets
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{
                        legend: {{
                            display: selectedRule === 'all',
                            position: 'top',
                            labels: {{ color: '#d8d9da', padding: 15 }}
                        }},
                        tooltip: {{
                            callbacks: {{
                                label: function(context) {{
                                    return (context.dataset.label || '') + ': ' + context.parsed.y.toFixed(1) + '%';
                                }}
                            }}
                        }}
                    }},
                    scales: {{
                        y: {{
                            beginAtZero: true,
                            max: 100,
                            ticks: {{
                                callback: function(value) {{
                                    return value + '%';
                                }},
                                color: '#9fa1a4'
                            }},
                            grid: {{ color: '#2d2d2d' }}
                        }},
                        x: {{
                            ticks: {{
                                color: '#9fa1a4',
                                maxRotation: 45,
                                minRotation: 45
                            }},
                            grid: {{ color: '#2d2d2d' }}
                        }}
                    }}
                }}
            }});
        }}

        // Add change event listener
        selector.addEventListener('change', function() {{
            updateRuleChart(this.value);
        }});

        // Initial render with worst 10 rules
        updateRuleChart('all');
        """

    def _build_interaction_script(self) -> str:
        """Build JavaScript for interactions."""

        return """
        // Toggle test details
        function toggleTest(index) {
            const content = document.getElementById('test-content-' + index);
            const icon = document.getElementById('test-icon-' + index);

            content.classList.toggle('expanded');
            icon.classList.toggle('expanded');
        }

        // Filter tests
        function filterTests(status) {
            const tests = document.querySelectorAll('.test-details');
            const buttons = document.querySelectorAll('.filter-btn');

            // Update active button
            buttons.forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');

            // Filter tests
            tests.forEach(test => {
                if (status === 'all' || test.dataset.status === status) {
                    test.style.display = 'block';
                } else {
                    test.style.display = 'none';
                }
            });
        }
        """

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
