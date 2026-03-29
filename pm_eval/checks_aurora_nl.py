"""Binary evals for Aurora NL test scenario packs (GenAI tourism SME prompts)."""

from __future__ import annotations

import re

from pm_eval.checks_common import check_acceptance_criteria_actionable, check_no_placeholders
from pm_eval.core import CheckResult, bullet_count_in_section_after_header, lower, word_count_in_section

DATA_DOMAIN_KEYS = [
    "visitation",
    "spend",
    "accommodation",
    "air",
    "booking",
    "sentiment",
    "capacity",
    "hotel",
    "occupancy",
]

GROUNDING_KEYS = [
    "ground",
    "trusted source",
    "trusted data",
    "historical context",
    "citation",
    "source attribution",
    "six source",
    "6 source",
    "data source",
    "provenance",
]

RAI_KEYS = [
    "limitation",
    "disclaimer",
    "human review",
    "human in the loop",
    "responsible",
    "hallucination",
    "uncertain",
    "not legal",
    "not financial",
    "may be incomplete",
]


def check_test_id(text: str) -> CheckResult:
    ok = bool(
        re.search(r"\bTC[- ][A-Z0-9]{2,}\b", text, re.IGNORECASE)
        or re.search(r"test case id\s*[:#]", text, re.IGNORECASE)
    )
    return CheckResult(
        id="test_identifier",
        pass_=ok,
        detail="Document exposes a stable test case id (e.g. TC-AURORA-001)." if ok else "Add TC-STYLE-ID or 'Test case ID:' line.",
    )


def check_objective(text: str) -> CheckResult:
    wc = word_count_in_section(text, r"^#{1,6}\s*objective\b")
    ok = wc >= 25
    return CheckResult(
        id="objective_substance",
        pass_=ok,
        detail=f"Objective section has ~{wc} words (need >= 25)." if ok else f"Objective too thin (~{wc} words); explain product risk this test mitigates.",
    )


def check_preconditions(text: str) -> CheckResult:
    ok = bool(re.search(r"^#{1,6}\s*(preconditions|setup|prerequisites)\b", text, re.MULTILINE | re.IGNORECASE))
    return CheckResult(
        id="preconditions_section",
        pass_=ok,
        detail="Preconditions/setup section present." if ok else "Add Preconditions (auth, data vintage, feature flags, locale).",
    )


def check_user_prompt_sample(text: str) -> CheckResult:
    fenced = len(re.findall(r"```", text)) >= 2
    quoted = bool(re.search(r"^\s*>\s+\S+", text, re.MULTILINE))
    ok = fenced or quoted
    return CheckResult(
        id="user_prompt_literal",
        pass_=ok,
        detail="User utterance captured in blockquote or fenced block." if ok else "Wrap the exact NL test prompt in ``` or blockquote for repeatability.",
    )


def check_twelve_fenced_nl_blocks(text: str) -> CheckResult:
    blocks = re.findall(r"```[\w]*\s*\n(.*?)```", text, re.DOTALL | re.IGNORECASE)
    nonempty = [b for b in blocks if b.strip()]
    n = len(nonempty)
    ok = n >= 12
    return CheckResult(
        id="twelve_fenced_nl_blocks",
        pass_=ok,
        detail=f"Found {n} fenced NL prompt block(s) (need >= 12)." if ok else f"Only {n} fenced prompt block(s); add or fence 12 distinct SME prompts.",
    )


def check_six_trusted_feeds_explicit(text: str) -> CheckResult:
    bullets, found = bullet_count_in_section_after_header(
        text,
        ("trusted data source", "six feed", "six trusted", "trusted feed", "data feeds (six)"),
    )
    ok = found and bullets >= 6
    if not found:
        return CheckResult(
            id="six_trusted_feeds_explicit",
            pass_=False,
            detail="Add a section like '## Trusted data sources (six feeds)' with six bullet lines naming each feed family.",
        )
    return CheckResult(
        id="six_trusted_feeds_explicit",
        pass_=ok,
        detail=f"Six feeds enumerated ({bullets} bullets under header)." if ok else f"Only {bullets} feed bullet(s) (need >= 6).",
    )


def check_pii_safety_expectation(text: str) -> CheckResult:
    t = lower(text)
    ok = any(
        k in t
        for k in [
            "pii",
            "personally identifiable",
            "personal information",
            "sensitive data",
            "de-identified",
            "anonymized",
            "do not paste",
        ]
    )
    return CheckResult(
        id="pii_safety_expectation",
        pass_=ok,
        detail="PII / sensitive-data expectations stated for NL testing." if ok else "State that operators must not paste PII or sensitive guest data into prompts (anonymized ops questions only).",
    )


def check_expected_plain_language_grounding(text: str) -> CheckResult:
    t = lower(text)
    has_plain = "plain language" in t or "non-technical" in t or "executive" in t
    has_structure = any(k in t for k in ["bullets", "bullet", "headline", "summary first", "numbers", "metric"])
    ok = has_plain and has_structure
    return CheckResult(
        id="expected_output_shape",
        pass_=ok,
        detail="Expected output describes plain-language shape and concrete elements." if ok else "State expected structure (headline + bullets + cited metrics/time windows).",
    )


def check_trusted_sources(text: str) -> CheckResult:
    t = lower(text)
    ok = any(k in t for k in GROUNDING_KEYS)
    return CheckResult(
        id="grounding_trusted_sources",
        pass_=ok,
        detail="Grounding / trusted sources called out." if ok else "Require grounding in trusted sources + historical context for SME answer.",
    )


def check_data_domains(text: str) -> CheckResult:
    t = lower(text)
    hits = sum(1 for k in DATA_DOMAIN_KEYS if k in t)
    ok = hits >= 3
    return CheckResult(
        id="tourism_data_domains",
        pass_=ok,
        detail=f"Touches {hits} tourism data dimensions (need >= 3)." if ok else f"Only {hits} domain hints inferred; name e.g. visitation, spend, accommodation, air capacity, booking, sentiment.",
    )


def check_negative_case(text: str) -> CheckResult:
    t = lower(text)
    ok = any(
        phrase in t
        for phrase in [
            "no data",
            "data unavailable",
            "sparse",
            "ambiguous",
            "clarify",
            "out of scope",
            "negative case",
            "failure mode",
            "edge case",
            "refuse",
        ]
    )
    return CheckResult(
        id="failure_or_edge_case",
        pass_=ok,
        detail="Failure/edge behavior specified." if ok else "Add failure mode (missing slice, ambiguous intent, stale data).",
    )


def check_responsible_ai(text: str) -> CheckResult:
    t = lower(text)
    ok = any(k in t for k in RAI_KEYS)
    return CheckResult(
        id="responsible_ai_basics",
        pass_=ok,
        detail="Basic RAI / limitations noted." if ok else "Add limitation, uncertainty, or human-review expectation.",
    )


AURORA_NL_PACK_CHECKS = [
    check_test_id,
    check_objective,
    check_preconditions,
    check_user_prompt_sample,
    check_twelve_fenced_nl_blocks,
    check_expected_plain_language_grounding,
    check_trusted_sources,
    check_data_domains,
    check_six_trusted_feeds_explicit,
    check_negative_case,
    check_responsible_ai,
    check_pii_safety_expectation,
    check_acceptance_criteria_actionable,
    check_no_placeholders,
]
