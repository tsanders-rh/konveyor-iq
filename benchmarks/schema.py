"""
Data models for test cases and evaluation results.
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class Severity(str, Enum):
    """Rule violation severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Language(str, Enum):
    """Supported programming languages."""
    JAVA = "java"
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    GO = "go"


class TestCase(BaseModel):
    """Individual test case for a rule violation."""
    id: str = Field(..., description="Unique test case identifier")
    code_snippet: str = Field(..., description="Original code with violation")
    expected_fix: Optional[str] = Field(None, description="Expected corrected code")
    context: str = Field(..., description="Migration or fix context")
    language: Language = Field(default=Language.JAVA)
    setup_code: Optional[str] = Field(None, description="Additional setup/import code")
    test_code: Optional[str] = Field(None, description="Unit test to verify correctness")
    expected_metrics: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Expected metric values"
    )


class Rule(BaseModel):
    """Static analysis rule definition."""
    rule_id: str = Field(..., description="Unique rule identifier")
    description: str = Field(..., description="What the rule checks for")
    severity: Severity = Field(default=Severity.MEDIUM)
    category: str = Field(..., description="Rule category (e.g., 'migration', 'security')")
    test_cases: List[TestCase] = Field(default_factory=list)
    migration_pattern: Optional[str] = Field(
        None,
        description="Expected transformation pattern"
    )
    source: Optional[str] = Field(
        None,
        description="URL to Konveyor ruleset source"
    )


class TestSuite(BaseModel):
    """Collection of rules and test cases."""
    name: str = Field(..., description="Test suite name")
    description: str = Field(..., description="Test suite description")
    version: str = Field(default="1.0.0")
    rules: List[Rule] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    prompt: Optional[str] = Field(
        None,
        description="Custom prompt template for this test suite (overrides config.yaml)"
    )


class EvaluationMetrics(BaseModel):
    """Metrics for a single evaluation."""
    # Functional correctness
    functional_correctness: bool = Field(..., description="Fix resolves violation")
    compiles: Optional[bool] = Field(None, description="Code compiles without errors")
    introduces_violations: bool = Field(
        False,
        description="Fix introduces new violations"
    )

    # Code quality
    pylint_score: Optional[float] = Field(None, ge=0, le=10)
    cyclomatic_complexity: Optional[int] = Field(None, ge=0)
    maintainability_index: Optional[float] = Field(None, ge=0, le=100)
    style_violations: int = Field(0, ge=0)

    # Security
    security_issues: int = Field(0, ge=0)
    high_severity_security: int = Field(0, ge=0)

    # Efficiency
    execution_time_ms: Optional[float] = Field(None, ge=0)
    memory_usage_mb: Optional[float] = Field(None, ge=0)

    # Explainability
    has_explanation: bool = Field(False)
    explanation_quality_score: Optional[float] = Field(None, ge=0, le=10)

    # Response time
    response_time_ms: float = Field(..., ge=0)
    tokens_used: Optional[int] = Field(None, ge=0)


class EvaluationResult(BaseModel):
    """Result of evaluating a single test case with a model."""
    test_case_id: str
    rule_id: str
    model_name: str
    timestamp: str

    # LLM output
    generated_code: str
    generated_explanation: Optional[str] = None
    raw_response: str

    # Metrics
    metrics: EvaluationMetrics

    # Success/failure
    passed: bool = Field(..., description="Overall pass/fail")
    failure_reason: Optional[str] = None

    # Cost tracking
    estimated_cost: Optional[float] = Field(None, description="Cost in USD")

    # Prompt tracking (for reproducibility)
    prompt_source: Optional[str] = Field(
        None,
        description="Source of prompt: 'custom' (test file override), 'config:<source>-to-<target>' (migration guidance), or 'default' (config.yaml)"
    )


class AggregatedResults(BaseModel):
    """Aggregated results across multiple evaluations."""
    model_name: str
    total_test_cases: int
    passed: int
    failed: int

    # Average metrics
    avg_response_time_ms: float
    avg_pylint_score: Optional[float] = None
    avg_complexity: Optional[float] = None

    # Success rates
    functional_correctness_rate: float = Field(ge=0, le=1)
    no_regression_rate: float = Field(ge=0, le=1)
    security_pass_rate: float = Field(ge=0, le=1)

    # Cost
    total_cost: Optional[float] = None

    # Per-rule breakdown
    per_rule_accuracy: Dict[str, float] = Field(default_factory=dict)
