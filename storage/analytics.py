"""
Analytics and query module for historical performance analysis.
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy import func, desc, and_, Integer
from sqlalchemy.orm import Session

from .models import TestResult, Rule, EvaluationRun, RulePerformanceSummary


class Analytics:
    """Analytics engine for querying historical test results."""

    def __init__(self, session: Session):
        self.session = session

    def get_rule_performance_over_time(
        self,
        rule_id: str,
        model_name: Optional[str] = None,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Get rule performance trend over time.

        Args:
            rule_id: Rule identifier
            model_name: Optional model filter
            days: Number of days to look back

        Returns:
            List of daily performance metrics
        """
        cutoff_date = datetime.now() - timedelta(days=days)

        query = self.session.query(
            func.date(TestResult.executed_at).label('date'),
            TestResult.model_name,
            func.count(TestResult.id).label('total'),
            func.sum(func.cast(TestResult.passed, Integer)).label('passed'),
            func.avg(TestResult.response_time_ms).label('avg_response_time'),
            func.avg(TestResult.estimated_cost).label('avg_cost')
        ).filter(
            TestResult.rule_id == rule_id,
            TestResult.executed_at >= cutoff_date
        )

        if model_name:
            query = query.filter(TestResult.model_name == model_name)

        query = query.group_by(
            func.date(TestResult.executed_at),
            TestResult.model_name
        ).order_by(func.date(TestResult.executed_at))

        results = []
        for row in query.all():
            pass_rate = (row.passed / row.total * 100) if row.total > 0 else 0
            results.append({
                'date': row.date.isoformat() if hasattr(row.date, 'isoformat') else str(row.date),
                'model_name': row.model_name,
                'total_tests': row.total,
                'passed_tests': row.passed,
                'pass_rate': pass_rate,
                'avg_response_time_ms': float(row.avg_response_time) if row.avg_response_time else 0,
                'avg_cost': float(row.avg_cost) if row.avg_cost else 0
            })

        return results

    def get_model_comparison(
        self,
        rule_id: Optional[str] = None,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Compare model performance across all rules or specific rule.

        Args:
            rule_id: Optional rule filter
            days: Number of days to look back

        Returns:
            List of model performance summaries
        """
        cutoff_date = datetime.now() - timedelta(days=days)

        query = self.session.query(
            TestResult.model_name,
            func.count(TestResult.id).label('total'),
            func.sum(func.cast(TestResult.passed, Integer)).label('passed'),
            func.avg(TestResult.response_time_ms).label('avg_response_time'),
            func.sum(TestResult.estimated_cost).label('total_cost'),
            func.avg(TestResult.explanation_quality_score).label('avg_explanation_score')
        ).filter(
            TestResult.executed_at >= cutoff_date
        )

        if rule_id:
            query = query.filter(TestResult.rule_id == rule_id)

        query = query.group_by(TestResult.model_name)

        results = []
        for row in query.all():
            pass_rate = (row.passed / row.total * 100) if row.total > 0 else 0
            results.append({
                'model_name': row.model_name,
                'total_tests': row.total,
                'passed_tests': row.passed,
                'pass_rate': pass_rate,
                'avg_response_time_ms': float(row.avg_response_time) if row.avg_response_time else 0,
                'total_cost': float(row.total_cost) if row.total_cost else 0,
                'avg_explanation_score': float(row.avg_explanation_score) if row.avg_explanation_score else None
            })

        # Sort by pass rate descending
        results.sort(key=lambda x: x['pass_rate'], reverse=True)
        return results

    def get_failing_rules(
        self,
        threshold: float = 50.0,
        min_tests: int = 3,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Identify rules with low pass rates.

        Args:
            threshold: Pass rate threshold (%)
            min_tests: Minimum number of tests required
            days: Number of days to look back

        Returns:
            List of underperforming rules
        """
        cutoff_date = datetime.now() - timedelta(days=days)

        query = self.session.query(
            TestResult.rule_id,
            Rule.description,
            Rule.migration_complexity,
            func.count(TestResult.id).label('total'),
            func.sum(func.cast(TestResult.passed, Integer)).label('passed')
        ).join(
            Rule, TestResult.rule_id == Rule.rule_id
        ).filter(
            TestResult.executed_at >= cutoff_date
        ).group_by(
            TestResult.rule_id,
            Rule.description,
            Rule.migration_complexity
        ).having(
            func.count(TestResult.id) >= min_tests
        )

        results = []
        for row in query.all():
            pass_rate = (row.passed / row.total * 100) if row.total > 0 else 0
            if pass_rate < threshold:
                results.append({
                    'rule_id': row.rule_id,
                    'description': row.description,
                    'complexity': row.migration_complexity,
                    'total_tests': row.total,
                    'passed_tests': row.passed,
                    'pass_rate': pass_rate
                })

        # Sort by pass rate ascending (worst first)
        results.sort(key=lambda x: x['pass_rate'])
        return results

    def get_cost_analysis(
        self,
        group_by: str = 'model',
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Analyze cost trends.

        Args:
            group_by: 'model', 'rule', or 'date'
            days: Number of days to look back

        Returns:
            Cost breakdown
        """
        cutoff_date = datetime.now() - timedelta(days=days)

        if group_by == 'model':
            query = self.session.query(
                TestResult.model_name.label('group_key'),
                func.count(TestResult.id).label('total_tests'),
                func.sum(TestResult.estimated_cost).label('total_cost'),
                func.avg(TestResult.estimated_cost).label('avg_cost_per_test'),
                func.sum(TestResult.tokens_used).label('total_tokens')
            ).filter(
                TestResult.executed_at >= cutoff_date,
                TestResult.estimated_cost.isnot(None)
            ).group_by(TestResult.model_name)

        elif group_by == 'rule':
            query = self.session.query(
                TestResult.rule_id.label('group_key'),
                func.count(TestResult.id).label('total_tests'),
                func.sum(TestResult.estimated_cost).label('total_cost'),
                func.avg(TestResult.estimated_cost).label('avg_cost_per_test'),
                func.sum(TestResult.tokens_used).label('total_tokens')
            ).filter(
                TestResult.executed_at >= cutoff_date,
                TestResult.estimated_cost.isnot(None)
            ).group_by(TestResult.rule_id)

        elif group_by == 'date':
            query = self.session.query(
                func.date(TestResult.executed_at).label('group_key'),
                func.count(TestResult.id).label('total_tests'),
                func.sum(TestResult.estimated_cost).label('total_cost'),
                func.avg(TestResult.estimated_cost).label('avg_cost_per_test'),
                func.sum(TestResult.tokens_used).label('total_tokens')
            ).filter(
                TestResult.executed_at >= cutoff_date,
                TestResult.estimated_cost.isnot(None)
            ).group_by(func.date(TestResult.executed_at))

        else:
            raise ValueError(f"Invalid group_by value: {group_by}")

        results = []
        for row in query.all():
            group_key = row.group_key
            if hasattr(group_key, 'isoformat'):
                group_key = group_key.isoformat()

            results.append({
                group_by: str(group_key),
                'total_tests': row.total_tests,
                'total_cost': float(row.total_cost) if row.total_cost else 0,
                'avg_cost_per_test': float(row.avg_cost_per_test) if row.avg_cost_per_test else 0,
                'total_tokens': row.total_tokens if row.total_tokens else 0
            })

        return results

    def get_complexity_breakdown(
        self,
        model_name: Optional[str] = None,
        days: int = 30
    ) -> Dict[str, Dict[str, Any]]:
        """
        Get pass rates broken down by migration complexity.

        Args:
            model_name: Optional model filter
            days: Number of days to look back

        Returns:
            Dictionary keyed by complexity level
        """
        cutoff_date = datetime.now() - timedelta(days=days)

        query = self.session.query(
            Rule.migration_complexity,
            func.count(TestResult.id).label('total'),
            func.sum(func.cast(TestResult.passed, Integer)).label('passed'),
            func.avg(TestResult.response_time_ms).label('avg_response_time')
        ).join(
            Rule, TestResult.rule_id == Rule.rule_id
        ).filter(
            TestResult.executed_at >= cutoff_date,
            Rule.migration_complexity.isnot(None)
        )

        if model_name:
            query = query.filter(TestResult.model_name == model_name)

        query = query.group_by(Rule.migration_complexity)

        results = {}
        for row in query.all():
            pass_rate = (row.passed / row.total * 100) if row.total > 0 else 0
            results[row.migration_complexity] = {
                'total_tests': row.total,
                'passed_tests': row.passed,
                'pass_rate': pass_rate,
                'avg_response_time_ms': float(row.avg_response_time) if row.avg_response_time else 0
            }

        return results

    def detect_regressions(
        self,
        threshold: float = 10.0,
        lookback_days: int = 7,
        comparison_days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Detect performance regressions (rules that used to pass but now fail).

        Args:
            threshold: Minimum pass rate drop (%) to flag as regression
            lookback_days: Recent period to check
            comparison_days: Historical period to compare against

        Returns:
            List of potential regressions
        """
        recent_cutoff = datetime.now() - timedelta(days=lookback_days)
        historical_cutoff = datetime.now() - timedelta(days=comparison_days)

        # Recent performance
        recent_query = self.session.query(
            TestResult.rule_id,
            TestResult.model_name,
            func.count(TestResult.id).label('total'),
            func.sum(func.cast(TestResult.passed, Integer)).label('passed')
        ).filter(
            TestResult.executed_at >= recent_cutoff
        ).group_by(
            TestResult.rule_id,
            TestResult.model_name
        )

        recent_perf = {}
        for row in recent_query.all():
            key = (row.rule_id, row.model_name)
            pass_rate = (row.passed / row.total * 100) if row.total > 0 else 0
            recent_perf[key] = {
                'total': row.total,
                'passed': row.passed,
                'pass_rate': pass_rate
            }

        # Historical performance
        historical_query = self.session.query(
            TestResult.rule_id,
            TestResult.model_name,
            func.count(TestResult.id).label('total'),
            func.sum(func.cast(TestResult.passed, Integer)).label('passed')
        ).filter(
            TestResult.executed_at >= historical_cutoff,
            TestResult.executed_at < recent_cutoff
        ).group_by(
            TestResult.rule_id,
            TestResult.model_name
        )

        regressions = []
        for row in historical_query.all():
            key = (row.rule_id, row.model_name)
            historical_pass_rate = (row.passed / row.total * 100) if row.total > 0 else 0

            if key in recent_perf:
                recent_pass_rate = recent_perf[key]['pass_rate']
                drop = historical_pass_rate - recent_pass_rate

                if drop >= threshold:
                    regressions.append({
                        'rule_id': row.rule_id,
                        'model_name': row.model_name,
                        'historical_pass_rate': historical_pass_rate,
                        'recent_pass_rate': recent_pass_rate,
                        'drop': drop,
                        'historical_tests': row.total,
                        'recent_tests': recent_perf[key]['total']
                    })

        # Sort by severity (biggest drops first)
        regressions.sort(key=lambda x: x['drop'], reverse=True)
        return regressions

    def get_recent_runs(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent evaluation runs.

        Args:
            limit: Maximum number of runs to return

        Returns:
            List of recent runs
        """
        query = self.session.query(EvaluationRun).order_by(
            desc(EvaluationRun.started_at)
        ).limit(limit)

        results = []
        for run in query.all():
            # Get summary stats for this run
            test_count = self.session.query(func.count(TestResult.id)).filter(
                TestResult.run_id == run.run_id
            ).scalar()

            passed_count = self.session.query(func.count(TestResult.id)).filter(
                TestResult.run_id == run.run_id,
                TestResult.passed == True
            ).scalar()

            results.append({
                'run_id': run.run_id,
                'name': run.name,
                'test_suite': run.test_suite_name,
                'started_at': run.started_at.isoformat() if run.started_at else None,
                'completed_at': run.completed_at.isoformat() if run.completed_at else None,
                'status': run.status,
                'total_tests': test_count or 0,
                'passed_tests': passed_count or 0,
                'pass_rate': (passed_count / test_count * 100) if test_count else 0
            })

        return results
