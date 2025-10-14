#!/usr/bin/env python3
"""
Database CLI for Konveyor IQ.

Provides commands for querying historical results, analyzing trends,
and managing the database.

Usage:
    python db_cli.py init --config config.yaml
    python db_cli.py query rules --failing --threshold 50
    python db_cli.py query trends --rule jakarta-package-00000 --days 30
    python db_cli.py query models --compare
    python db_cli.py export --run-id abc123 --format json
"""
import argparse
import json
import sys
import yaml
from pathlib import Path
from typing import Dict, Any

from storage import get_storage
from storage.analytics import Analytics
from storage.backend import SQLiteBackend, PostgreSQLBackend


def load_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    """Load configuration from YAML file."""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def init_database(args):
    """Initialize database schema."""
    config = load_config(args.config)
    storage_config = config.get('storage', {'type': 'sqlite', 'path': 'konveyor_iq.db'})

    if storage_config.get('type') == 'file':
        print("Error: Database initialization requires 'sqlite' or 'postgresql' storage type")
        print("Update your config.yaml to use a database backend")
        return 1

    print(f"Initializing database: {storage_config.get('type')}")

    try:
        storage = get_storage(storage_config)
        print("✓ Database initialized successfully")
        storage.close()
        return 0
    except Exception as e:
        print(f"✗ Error initializing database: {e}")
        return 1


def query_failing_rules(args):
    """Query rules with low pass rates."""
    config = load_config(args.config)
    storage_config = config.get('storage', {'type': 'sqlite', 'path': 'konveyor_iq.db'})

    storage = get_storage(storage_config)

    if isinstance(storage.backend, (SQLiteBackend, PostgreSQLBackend)):
        session = storage.backend._get_session()
        analytics = Analytics(session)

        failing_rules = analytics.get_failing_rules(
            threshold=args.threshold,
            min_tests=args.min_tests,
            days=args.days
        )

        if not failing_rules:
            print(f"No rules found with pass rate < {args.threshold}%")
            return 0

        print(f"\nRules with pass rate < {args.threshold}% (last {args.days} days):\n")
        print(f"{'Rule ID':<40} {'Complexity':<12} {'Pass Rate':<12} {'Tests'}")
        print("-" * 80)

        for rule in failing_rules:
            print(
                f"{rule['rule_id']:<40} "
                f"{rule['complexity'] or 'N/A':<12} "
                f"{rule['pass_rate']:>6.1f}%     "
                f"{rule['passed_tests']}/{rule['total_tests']}"
            )

        session.close()
    else:
        print("Error: This command requires SQLite or PostgreSQL backend")
        return 1

    storage.close()
    return 0


def query_trends(args):
    """Query performance trends over time."""
    config = load_config(args.config)
    storage_config = config.get('storage', {'type': 'sqlite', 'path': 'konveyor_iq.db'})

    storage = get_storage(storage_config)

    if isinstance(storage.backend, (SQLiteBackend, PostgreSQLBackend)):
        session = storage.backend._get_session()
        analytics = Analytics(session)

        trends = analytics.get_rule_performance_over_time(
            rule_id=args.rule,
            model_name=args.model,
            days=args.days
        )

        if not trends:
            print(f"No data found for rule: {args.rule}")
            return 0

        print(f"\nPerformance trends for {args.rule} (last {args.days} days):\n")
        print(f"{'Date':<12} {'Model':<30} {'Pass Rate':<12} {'Avg Time (ms)':<15} {'Tests'}")
        print("-" * 90)

        for trend in trends:
            print(
                f"{trend['date']:<12} "
                f"{trend['model_name']:<30} "
                f"{trend['pass_rate']:>6.1f}%     "
                f"{trend['avg_response_time_ms']:>10.0f}      "
                f"{trend['passed_tests']}/{trend['total_tests']}"
            )

        session.close()
    else:
        print("Error: This command requires SQLite or PostgreSQL backend")
        return 1

    storage.close()
    return 0


def query_models(args):
    """Compare model performance."""
    config = load_config(args.config)
    storage_config = config.get('storage', {'type': 'sqlite', 'path': 'konveyor_iq.db'})

    storage = get_storage(storage_config)

    if isinstance(storage.backend, (SQLiteBackend, PostgreSQLBackend)):
        session = storage.backend._get_session()
        analytics = Analytics(session)

        comparison = analytics.get_model_comparison(
            rule_id=args.rule,
            days=args.days
        )

        if not comparison:
            print("No model performance data found")
            return 0

        print(f"\nModel Performance Comparison (last {args.days} days):\n")
        print(f"{'Model':<30} {'Pass Rate':<12} {'Avg Time':<12} {'Total Cost':<12} {'Tests'}")
        print("-" * 85)

        for model in comparison:
            print(
                f"{model['model_name']:<30} "
                f"{model['pass_rate']:>6.1f}%     "
                f"{model['avg_response_time_ms']:>7.0f}ms    "
                f"${model['total_cost']:>7.4f}    "
                f"{model['passed_tests']}/{model['total_tests']}"
            )

        session.close()
    else:
        print("Error: This command requires SQLite or PostgreSQL backend")
        return 1

    storage.close()
    return 0


def query_complexity(args):
    """Show pass rates by complexity level."""
    config = load_config(args.config)
    storage_config = config.get('storage', {'type': 'sqlite', 'path': 'konveyor_iq.db'})

    storage = get_storage(storage_config)

    if isinstance(storage.backend, (SQLiteBackend, PostgreSQLBackend)):
        session = storage.backend._get_session()
        analytics = Analytics(session)

        breakdown = analytics.get_complexity_breakdown(
            model_name=args.model,
            days=args.days
        )

        if not breakdown:
            print("No complexity data found")
            return 0

        print(f"\nPass Rate by Complexity (last {args.days} days):\n")
        if args.model:
            print(f"Model: {args.model}\n")

        print(f"{'Complexity':<15} {'Pass Rate':<12} {'Avg Time (ms)':<15} {'Tests'}")
        print("-" * 60)

        # Sort by complexity order
        complexity_order = ['trivial', 'low', 'medium', 'high', 'expert']
        for complexity in complexity_order:
            if complexity in breakdown:
                data = breakdown[complexity]
                print(
                    f"{complexity.upper():<15} "
                    f"{data['pass_rate']:>6.1f}%     "
                    f"{data['avg_response_time_ms']:>10.0f}      "
                    f"{data['passed_tests']}/{data['total_tests']}"
                )

        session.close()
    else:
        print("Error: This command requires SQLite or PostgreSQL backend")
        return 1

    storage.close()
    return 0


def query_regressions(args):
    """Detect performance regressions."""
    config = load_config(args.config)
    storage_config = config.get('storage', {'type': 'sqlite', 'path': 'konveyor_iq.db'})

    storage = get_storage(storage_config)

    if isinstance(storage.backend, (SQLiteBackend, PostgreSQLBackend)):
        session = storage.backend._get_session()
        analytics = Analytics(session)

        regressions = analytics.detect_regressions(
            threshold=args.threshold,
            lookback_days=args.recent,
            comparison_days=args.historical
        )

        if not regressions:
            print(f"✓ No regressions detected (threshold: {args.threshold}%)")
            return 0

        print(f"\n⚠ Performance Regressions Detected (drop ≥ {args.threshold}%):\n")
        print(f"{'Rule ID':<40} {'Model':<25} {'Drop':<10} {'Historical → Recent'}")
        print("-" * 95)

        for reg in regressions:
            print(
                f"{reg['rule_id']:<40} "
                f"{reg['model_name']:<25} "
                f"{reg['drop']:>6.1f}%   "
                f"{reg['historical_pass_rate']:>6.1f}% → {reg['recent_pass_rate']:>6.1f}%"
            )

        session.close()
    else:
        print("Error: This command requires SQLite or PostgreSQL backend")
        return 1

    storage.close()
    return 0


def query_runs(args):
    """List recent evaluation runs."""
    config = load_config(args.config)
    storage_config = config.get('storage', {'type': 'sqlite', 'path': 'konveyor_iq.db'})

    storage = get_storage(storage_config)

    if isinstance(storage.backend, (SQLiteBackend, PostgreSQLBackend)):
        session = storage.backend._get_session()
        analytics = Analytics(session)

        runs = analytics.get_recent_runs(limit=args.limit)

        if not runs:
            print("No evaluation runs found")
            return 0

        print(f"\nRecent Evaluation Runs:\n")
        print(f"{'Run ID':<38} {'Name':<20} {'Started':<20} {'Status':<12} {'Pass Rate'}")
        print("-" * 110)

        for run in runs:
            name = run['name'] or run['test_suite']
            started = run['started_at'][:19] if run['started_at'] else 'N/A'
            print(
                f"{run['run_id']:<38} "
                f"{name[:19]:<20} "
                f"{started:<20} "
                f"{run['status']:<12} "
                f"{run['pass_rate']:>6.1f}% ({run['passed_tests']}/{run['total_tests']})"
            )

        session.close()
    else:
        print("Error: This command requires SQLite or PostgreSQL backend")
        return 1

    storage.close()
    return 0


def export_data(args):
    """Export data to JSON."""
    config = load_config(args.config)
    storage_config = config.get('storage', {'type': 'sqlite', 'path': 'konveyor_iq.db'})

    storage = get_storage(storage_config)

    if args.run_id:
        run = storage.get_run(args.run_id)
        results = storage.get_test_results(args.run_id)

        export_data = {
            'run': run,
            'results': results
        }

        output = json.dumps(export_data, indent=2)

        if args.output:
            with open(args.output, 'w') as f:
                f.write(output)
            print(f"✓ Exported to {args.output}")
        else:
            print(output)

    storage.close()
    return 0


def main():
    parser = argparse.ArgumentParser(description="Konveyor IQ Database CLI")
    parser.add_argument('--config', default='config.yaml', help='Config file path')

    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # Init command
    init_parser = subparsers.add_parser('init', help='Initialize database')

    # Query commands
    query_parser = subparsers.add_parser('query', help='Query database')
    query_subparsers = query_parser.add_subparsers(dest='query_type')

    # Query failing rules
    rules_parser = query_subparsers.add_parser('rules', help='Query failing rules')
    rules_parser.add_argument('--threshold', type=float, default=50.0, help='Pass rate threshold')
    rules_parser.add_argument('--min-tests', type=int, default=3, help='Minimum tests required')
    rules_parser.add_argument('--days', type=int, default=30, help='Days to look back')

    # Query trends
    trends_parser = query_subparsers.add_parser('trends', help='Query performance trends')
    trends_parser.add_argument('--rule', required=True, help='Rule ID')
    trends_parser.add_argument('--model', help='Model name filter')
    trends_parser.add_argument('--days', type=int, default=30, help='Days to look back')

    # Query models
    models_parser = query_subparsers.add_parser('models', help='Compare model performance')
    models_parser.add_argument('--rule', help='Filter by rule ID')
    models_parser.add_argument('--days', type=int, default=30, help='Days to look back')

    # Query complexity
    complexity_parser = query_subparsers.add_parser('complexity', help='Pass rates by complexity')
    complexity_parser.add_argument('--model', help='Filter by model')
    complexity_parser.add_argument('--days', type=int, default=30, help='Days to look back')

    # Query regressions
    reg_parser = query_subparsers.add_parser('regressions', help='Detect regressions')
    reg_parser.add_argument('--threshold', type=float, default=10.0, help='Drop threshold (%)')
    reg_parser.add_argument('--recent', type=int, default=7, help='Recent period (days)')
    reg_parser.add_argument('--historical', type=int, default=30, help='Historical period (days)')

    # Query runs
    runs_parser = query_subparsers.add_parser('runs', help='List recent runs')
    runs_parser.add_argument('--limit', type=int, default=10, help='Number of runs to show')

    # Export command
    export_parser = subparsers.add_parser('export', help='Export data')
    export_parser.add_argument('--run-id', required=True, help='Run ID to export')
    export_parser.add_argument('--output', help='Output file (default: stdout)')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    try:
        if args.command == 'init':
            return init_database(args)

        elif args.command == 'query':
            if args.query_type == 'rules':
                return query_failing_rules(args)
            elif args.query_type == 'trends':
                return query_trends(args)
            elif args.query_type == 'models':
                return query_models(args)
            elif args.query_type == 'complexity':
                return query_complexity(args)
            elif args.query_type == 'regressions':
                return query_regressions(args)
            elif args.query_type == 'runs':
                return query_runs(args)
            else:
                query_parser.print_help()
                return 1

        elif args.command == 'export':
            return export_data(args)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
