"""Binary evals for strategy documents (vision coherence, evidence, risks)."""

from __future__ import annotations

import re

from pm_eval.checks_common import check_no_placeholders
from pm_eval.core import CheckResult, lower, word_count_in_section


def check_strategy_doc_label(text: str) -> CheckResult:
    t = lower(text)
    ok = any(
        k in t
        for k in [
            "strategy",
            "strategic",
            "vision",
            "north star",
            "thesis",
        ]
    ) and bool(re.search(r"^#\s+", text, re.MULTILINE))
    return CheckResult(
        id="strategy_doc_signal",
        pass_=ok,
        detail="Reads as a strategy / vision artifact (title + strategy language)." if ok else "Title and strategy framing (vision, thesis, strategic pillars) expected.",
    )


def check_vision_substance(text: str) -> CheckResult:
    wc = word_count_in_section(text, r"^#{1,6}\s*(vision|north star|strategic intent|where we('re| are) going)\b")
    ok = wc >= 30
    return CheckResult(
        id="vision_coherence",
        pass_=ok,
        detail="Vision section has substance." if ok else "Expand ## Vision (or North star): destination, audience, differentiation.",
    )


def check_evidence_or_insights(text: str) -> CheckResult:
    t = lower(text)
    ok = any(
        k in t
        for k in [
            "evidence",
            "research",
            "data shows",
            "insight",
            "we know",
            "finding",
            "benchmark",
        ]
    )
    return CheckResult(
        id="evidence_basis",
        pass_=ok,
        detail="Evidence or research basis referenced." if ok else "Ground strategy in evidence, research, or data-backed insights.",
    )


def check_strategic_risks(text: str) -> CheckResult:
    t = lower(text)
    has_risk_header = bool(re.search(r"^#{1,6}\s*(risk|risks|pre-?mortem|mitigation)\b", text, re.MULTILINE | re.IGNORECASE))
    has_risk_lang = bool(re.search(r"\b(risk|mitigat|downside|dependency|uncertain|premortem)\b", t))
    ok = has_risk_header or has_risk_lang
    return CheckResult(
        id="risk_identification",
        pass_=ok,
        detail="Risks or mitigations called out." if ok else "Add ## Risks (or pre-mortem) with mitigations or watch items.",
    )


def check_horizon_or_priorities(text: str) -> CheckResult:
    t = lower(text)
    ok = any(
        k in t
        for k in [
            "priority",
            "now / next",
            "now, next",
            "horizon",
            "roadmap",
            "phase",
            "quarter",
        ]
    )
    return CheckResult(
        id="priorities_or_horizon",
        pass_=ok,
        detail="Priorities, phases, or time horizon indicated." if ok else "State priorities, horizons, or sequencing (now / next / later).",
    )


STRATEGY_CHECKS = [
    check_strategy_doc_label,
    check_vision_substance,
    check_evidence_or_insights,
    check_strategic_risks,
    check_horizon_or_priorities,
    check_no_placeholders,
]
