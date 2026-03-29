"""Binary evals for one-pagers / exec briefs (summary, actions, testability)."""

from __future__ import annotations

import re

from pm_eval.checks_common import check_no_placeholders
from pm_eval.core import CheckResult, lower, word_count_in_section


def check_executive_summary(text: str) -> CheckResult:
    wc = word_count_in_section(
        text,
        r"^#{1,6}\s*(executive summary|tl;dr|at a glance|summary)\b",
    )
    ok = wc >= 40
    return CheckResult(
        id="executive_summary_quality",
        pass_=ok,
        detail="Executive summary has enough substance." if ok else "Add ## Executive summary (40+ words): decision, why, so what.",
    )


def check_decision_or_ask(text: str) -> CheckResult:
    t = lower(text)
    ok = any(
        k in t
        for k in [
            "decision",
            "approve",
            "ask:",
            "recommendation",
            "we propose",
            "request",
        ]
    )
    return CheckResult(
        id="decision_or_ask",
        pass_=ok,
        detail="Clear decision, ask, or recommendation." if ok else "State the decision needed, approval ask, or recommendation.",
    )


def check_action_items_specific(text: str) -> CheckResult:
    t = lower(text)
    has_actions = bool(re.search(r"^#{1,6}\s*(action|next steps|follow-?up)\b", text, re.MULTILINE | re.IGNORECASE))
    has_specificity = bool(
        re.search(r"\b(owner|due|by \w+day|deadline|this week|q\d|must|will)\b", t)
        or re.search(r"^\s*[-*]\s+.+\s[-–]\s+", text, re.MULTILINE)
    )
    ok = has_actions and has_specificity
    return CheckResult(
        id="action_item_specificity",
        pass_=ok,
        detail="Next steps with owners, dates, or strong verbs." if ok else "Add ## Next steps with owner/due or unambiguous accountable actions.",
    )


def check_test_or_success_signal(text: str) -> CheckResult:
    t = lower(text)
    ok = any(
        k in t
        for k in [
            "success looks",
            "we will know",
            "measure",
            "validate",
            "test",
            "metric",
            "definition of done",
        ]
    )
    return CheckResult(
        id="test_or_success_signal",
        pass_=ok,
        detail="How success will be observed or validated." if ok else "Add how you'll validate success (metric, test, DoD).",
    )


ONE_PAGER_CHECKS = [
    check_executive_summary,
    check_decision_or_ask,
    check_action_items_specific,
    check_test_or_success_signal,
    check_no_placeholders,
]
