# import operator
# from typing import Any, Callable

from app.models.schema import (
    ComparisonOperator,
    ComplianceStatus,
    EvidenceAsset,
    ExtractedRuleBase,
    RuleEvaluationResult,
)

#  Map our strictly typed Enums to Python's internal C-optimized math operators
# OPERATOR_MAP: dict[ComparisonOperator, Callable[[Any, Any], bool]] = {
#     ComparisonOperator.LT: operator.lt,
#     ComparisonOperator.LTE: operator.le,
#     ComparisonOperator.GT: operator.gt,
#     ComparisonOperator.GTE: operator.ge,
#     ComparisonOperator.EQ: operator.eq,
#     ComparisonOperator.NEQ: operator.ne,
#     ComparisonOperator.IN: lambda a, b: a in b if isinstance(b, (list, str, dict)) else False,
#     ComparisonOperator.NOT_IN: lambda a, b: a not in b if isinstance(b, (list, str, dict)) else False,
# }


def _safe_compare(actual: object, expected: object, op: ComparisonOperator) -> bool:
    """
    Safely executes the math comparison using strict type narrowing.
    Catches type mismatches so the application never crashes on bad JSON.
    """
    # 1. Handle Equality (Supported by all objects)
    if op == ComparisonOperator.EQ:
        return actual == expected
    if op == ComparisonOperator.NEQ:
        return actual != expected

        # The linter requires us to prove 'expected' is iterable before using 'in'
        # 2. Handle Membership (in / not in)
    if op in (ComparisonOperator.IN, ComparisonOperator.NOT_IN):
        # Case A: expected is a string (actual MUST also be a string)
        if isinstance(expected, str):
            if not isinstance(actual, str):
                return False
            if op == ComparisonOperator.IN:
                return actual in expected
            return actual not in expected

        # Case B: expected is a list or dict (actual can safely be any object)
        if isinstance(expected, (list, dict)):
            if op == ComparisonOperator.IN:
                return actual in expected
            return actual not in expected

        return False
        
    # 3. Handle Math Comparisons (<, <=, >, >=)
    # Type narrowing proves to the linter that these are numbers
    if isinstance(actual, (int, float)) and isinstance(expected, (int, float)):
        if op == ComparisonOperator.LT:
            return actual < expected
        if op == ComparisonOperator.LTE:
            return actual <= expected
        if op == ComparisonOperator.GT:
            return actual > expected
        if op == ComparisonOperator.GTE:
            return actual >= expected

    # Type narrowing proves to the linter that these are strings (e.g., for versions)
    if isinstance(actual, str) and isinstance(expected, str):
        if op == ComparisonOperator.LT:
            return actual < expected
        if op == ComparisonOperator.LTE:
            return actual <= expected
        if op == ComparisonOperator.GT:
            return actual > expected
        if op == ComparisonOperator.GTE:
            return actual >= expected

    # If types are mixed (e.g., checking if integer 92 < string "apple"), it fails safely
    return False


def evaluate_rule(rule: ExtractedRuleBase, asset: EvidenceAsset) -> RuleEvaluationResult:
    """
    Evaluates a single atomic rule (with optional pre-conditions) against a
    single infrastructure asset's metrics.
    """
    # 1. Initialize the baseline response payload
    result = RuleEvaluationResult(
        control_id=rule.control_id,
        target_metric=rule.target_metric,
        operator=rule.operator,
        threshold_value=rule.threshold_value,
        status=ComplianceStatus.UNKNOWN,
        audit_reasoning="Evaluation not completed.",
        source_clause=rule.source_clause,
    )

    # 2. Asset Type Verification (Does this rule even apply to this server?)
    if rule.target_asset_type != asset.asset_type:
        result.status = ComplianceStatus.NOT_APPLICABLE
        result.audit_reasoning = f"Rule targets '{rule.target_asset_type}', but asset is '{asset.asset_type}'."
        return result

    # 3. Pre-Condition Evaluation (The AST branching logic)
    if rule.pre_condition:
        pre_actual = asset.metrics.get(rule.pre_condition.target_metric)

        # If the pre-condition metric is entirely missing, we cannot proceed safely.
        if pre_actual is None:
            result.status = ComplianceStatus.UNKNOWN
            result.audit_reasoning = f"Pre-condition metric '{rule.pre_condition.target_metric}' missing from evidence."
            return result

        pre_passed = _safe_compare(
            actual=pre_actual, expected=rule.pre_condition.threshold_value, op=rule.pre_condition.operator
        )

        # If the pre-condition is false, bypass the main rule.
        if not pre_passed:
            result.status = ComplianceStatus.NOT_APPLICABLE
            result.audit_reasoning = (
                f"Pre-condition bypassed: {rule.pre_condition.target_metric} "
                f"({pre_actual}) {rule.pre_condition.operator} {rule.pre_condition.threshold_value}."
            )
            return result

    # 4. Main Rule Evaluation
    actual_value = asset.metrics.get(rule.target_metric)
    result.actual_value = actual_value

    if actual_value is None:
        result.status = ComplianceStatus.UNKNOWN
        result.audit_reasoning = f"Target metric '{rule.target_metric}' is missing from evidence payload."
        return result

    # 5. Deterministic Math & Audit Generation
    is_compliant = _safe_compare(actual=actual_value, expected=rule.threshold_value, op=rule.operator)

    if is_compliant:
        result.status = ComplianceStatus.COMPLIANT
        result.audit_reasoning = (
            f"Compliant: {rule.target_metric} is {actual_value}, "
            f"which satisfies {rule.operator} {rule.threshold_value}."
        )
    else:
        result.status = ComplianceStatus.NON_COMPLIANT
        result.audit_reasoning = (
            f"Non-Compliant: {rule.target_metric} is {actual_value}, "
            f"which fails the requirement of {rule.operator} {rule.threshold_value}."
        )

    return result
