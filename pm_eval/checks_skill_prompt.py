"""Binary evals for system prompts / Cursor skills (clarity, edge cases, output shape)."""

from __future__ import annotations

import re

from pm_eval.checks_common import check_no_placeholders
from pm_eval.core import CheckResult, lower


def check_role_or_goal(text: str) -> CheckResult:
    t = lower(text)
    ok = any(
        k in t
        for k in [
            "you are",
            "your role",
            "act as",
            "instructions:",
            "purpose:",
            "goal:",
        ]
    ) or bool(re.search(r"^#\s+", text, re.MULTILINE))
    return CheckResult(
        id="instruction_clarity_role",
        pass_=ok,
        detail="Role, goal, or top-level instructions present." if ok else "Open with role, purpose, or explicit instructions for the agent.",
    )


def check_output_format(text: str) -> CheckResult:
    t = lower(text)
    ok = any(
        k in t
        for k in [
            "output format",
            "respond with",
            "return json",
            "markdown",
            "schema",
            "structured",
            "use headings",
            "bullet",
        ]
    )
    return CheckResult(
        id="output_format_specified",
        pass_=ok,
        detail="Expected output format or structure specified." if ok else "Specify output format (JSON, markdown sections, bullets, etc.).",
    )


def check_edge_or_failure_behavior(text: str) -> CheckResult:
    t = lower(text)
    ok = any(
        k in t
        for k in [
            "edge case",
            "if the user",
            "if unclear",
            "if missing",
            "otherwise",
            "when in doubt",
            "refuse",
            "do not",
            "never",
        ]
    )
    return CheckResult(
        id="edge_cases_or_guardrails",
        pass_=ok,
        detail="Edge cases, ambiguities, or guardrails addressed." if ok else "Add edge cases: unclear input, missing data, refusal conditions.",
    )


def check_min_instruction_length(text: str) -> CheckResult:
    wc = len(text.split())
    ok = wc >= 80
    return CheckResult(
        id="instruction_substance",
        pass_=ok,
        detail=f"Prompt/skill body ~{wc} words (need >= 80)." if ok else f"Instructions thin (~{wc} words); add constraints, examples, or policy.",
    )


SKILL_OR_SYSTEM_PROMPT_CHECKS = [
    check_role_or_goal,
    check_min_instruction_length,
    check_output_format,
    check_edge_or_failure_behavior,
    check_no_placeholders,
]
