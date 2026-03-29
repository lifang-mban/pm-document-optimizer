"""Binary evals for product requirements documents (problem-solution fit, metrics, scope)."""

from __future__ import annotations

import re

from pm_eval.checks_common import check_acceptance_criteria_actionable, check_no_placeholders
from pm_eval.core import CheckResult, lower, word_count_in_section


def check_prd_identifier(text: str) -> CheckResult:
    ok = bool(
        re.search(r"\bPRD[- ][A-Z0-9]{2,}\b", text, re.IGNORECASE)
        or re.search(r"\b(product requirements|requirements doc)\b", lower(text))
    )
    return CheckResult(
        id="prd_identifier",
        pass_=ok,
        detail="PRD or product requirements labeled (e.g. PRD-DATA-001)." if ok else "Add PRD-style id or explicit product requirements title.",
    )


def check_problem_statement_substance(text: str) -> CheckResult:
    wc = word_count_in_section(text, r"^#{1,6}\s*(problem|background|context|current state)\b")
    ok = wc >= 35
    return CheckResult(
        id="problem_statement_substance",
        pass_=ok,
        detail=f"Problem/background section ~{wc} words (need >= 35)." if ok else "Expand problem: who suffers, current pain, why now.",
    )


def check_solution_approach(text: str) -> CheckResult:
    wc = word_count_in_section(text, r"^#{1,6}\s*(solution|proposed approach|what we (will|'ll) build)\b")
    ok = wc >= 25
    return CheckResult(
        id="solution_fit",
        pass_=ok,
        detail="Solution section substantive." if ok else "Add ## Solution (or Proposed approach) tying features to the problem.",
    )


def check_metrics_specificity(text: str) -> CheckResult:
    t = lower(text)
    has_header = bool(
        re.search(
            r"^#{1,6}\s*(success metrics|kpis?|goals?|measurement)\b",
            text,
            re.MULTILINE | re.IGNORECASE,
        )
    )
    has_numbers = bool(re.search(r"\d+%|\d+\s*(bp|bps|pp)|\b(okr|north star|conversion|latency|adoption)\b", t))
    ok = has_header and has_numbers
    return CheckResult(
        id="metric_specificity",
        pass_=ok,
        detail="Metrics section with concrete targets or units." if ok else "Add Success metrics / KPIs with numbers, thresholds, or named KPI types.",
    )


def check_scope_boundaries(text: str) -> CheckResult:
    t = lower(text)
    has_scope = bool(re.search(r"^#{1,6}\s*scope\b", text, re.MULTILINE | re.IGNORECASE))
    has_boundary = any(
        p in t
        for p in [
            "out of scope",
            "non-goals",
            "not in scope",
            "excluded",
            "won't",
            "will not",
            "defer",
        ]
    )
    ok = has_scope and has_boundary
    return CheckResult(
        id="scope_boundaries",
        pass_=ok,
        detail="Scope plus explicit out-of-scope / non-goals." if ok else "Add ## Scope and clearly list out of scope or non-goals.",
    )


def check_user_or_stakeholder(text: str) -> CheckResult:
    t = lower(text)
    ok = any(
        k in t
        for k in [
            "persona",
            "user story",
            "stakeholder",
            "primary user",
            "customer segment",
            "operator",
            "sme",
        ]
    )
    return CheckResult(
        id="user_or_stakeholder",
        pass_=ok,
        detail="Users or stakeholders named." if ok else "Name primary users, personas, or stakeholder groups.",
    )


def check_dependencies_or_data(text: str) -> CheckResult:
    t = lower(text)
    ok = any(
        k in t
        for k in [
            "dependency",
            "data source",
            "upstream",
            "integration",
            "api",
            "warehouse",
            "pipeline",
        ]
    )
    return CheckResult(
        id="dependencies_or_data",
        pass_=ok,
        detail="Dependencies or data/integration expectations noted." if ok else "Call out data sources, integrations, or technical dependencies.",
    )


PRD_CHECKS = [
    check_prd_identifier,
    check_problem_statement_substance,
    check_user_or_stakeholder,
    check_solution_approach,
    check_metrics_specificity,
    check_scope_boundaries,
    check_dependencies_or_data,
    check_acceptance_criteria_actionable,
    check_no_placeholders,
]
