"""Checks reused across multiple artifact profiles."""

from __future__ import annotations

import re

from pm_eval.core import CheckResult, lower


def check_no_placeholders(text: str) -> CheckResult:
    bad = re.search(r"\b(TODO|TBD|FIXME|lorem ipsum)\b", text, re.IGNORECASE)
    ok = bad is None
    return CheckResult(
        id="no_critical_placeholders",
        pass_=ok,
        detail="No TODO/TBD/FIXME placeholders." if ok else f"Remove placeholder: {bad.group(0) if bad else ''}.",
    )


def check_acceptance_criteria_actionable(text: str) -> CheckResult:
    has_header = bool(
        re.search(
            r"^#{1,6}\s*(acceptance criteria|definition of done|success criteria|release criteria)\b",
            text,
            re.MULTILINE | re.IGNORECASE,
        )
    )
    t = lower(text)
    measurable = bool(re.search(r"\b(must|shall|pass if|verify|instrument|metric|log|trace)\b", t))
    ok = has_header and measurable
    return CheckResult(
        id="acceptance_criteria_actionable",
        pass_=ok,
        detail="Acceptance criteria section with verifiable language." if ok else "Add acceptance / DoD with checkable must/shall statements.",
    )
