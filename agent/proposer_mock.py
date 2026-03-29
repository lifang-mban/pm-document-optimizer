"""
Deterministic proposer: fixes the first failing eval check with a canned patch.

Use for offline E2E runs (no API key) or as a baseline ratchet.
"""

from __future__ import annotations

import re
from typing import Callable

from pm_eval.registry import DEFAULT_PROFILE, evaluate


def _insert_after_first_line(doc: str, insertion: str) -> str:
    nl = doc.find("\n")
    if nl == -1:
        return doc + "\n\n" + insertion.strip() + "\n"
    return doc[:nl] + "\n\n" + insertion.strip() + "\n" + doc[nl + 1 :]


def _replace_section(doc: str, header: str, new_section: str) -> str:
    pattern = rf"(^#{{1,6}}\s*{re.escape(header)}\s*$)(.*?)(?=^#{{1,6}}\s|\Z)"
    if not re.search(pattern, doc, re.MULTILINE | re.DOTALL | re.IGNORECASE):
        return doc + "\n\n" + new_section.strip() + "\n"
    return re.sub(pattern, new_section.strip() + "\n", doc, count=1, flags=re.MULTILINE | re.DOTALL | re.IGNORECASE)


def _fix_test_identifier(doc: str) -> tuple[str, str]:
    ins = "**Test case ID:** TC-AURORA-001"
    return _insert_after_first_line(doc, ins), "Insert stable TC-AURORA-001 identifier after title."


def _fix_objective(doc: str) -> tuple[str, str]:
    body = """## Objective

Validate that Aurora returns an SME-appropriate, plain-language insight when the operator asks about weekend lodging softness versus last year. The answer must cite trusted Destination Canada tourism signals across visitation, spend, accommodation, air capacity, booking, and brand sentiment, state the comparison window, and avoid overclaiming when coverage is incomplete. This mitigates reputational risk from an ungrounded \"analyst in a box\" experience."""
    return _replace_section(doc, "objective", body), "Expand Objective to name risk, domains, and expected rigor."


def _fix_preconditions(doc: str) -> tuple[str, str]:
    block = """## Preconditions

- Operator is signed into the Aurora AI Insights Generator pilot with the internal feature flag enabled.
- The six trusted source feeds are loaded to the same published vintage (no partial refresh mid-run).
- Default geography is Canada unless the prompt narrows to a province, city, or corridor."""
    if re.search(r"^#{1,6}\s*preconditions\b", doc, re.MULTILINE | re.IGNORECASE):
        return doc, "preconditions already present"
    anchor = "\n## Notes"
    if anchor in doc:
        return doc.replace(anchor, "\n" + block + "\n" + anchor, 1), "Add Preconditions before Notes."
    return doc.rstrip() + "\n\n" + block + "\n", "Append Preconditions section."


def _fix_user_prompt_literal(doc: str) -> tuple[str, str]:
    def wrap(m: re.Match[str]) -> str:
        q = m.group(1).strip()
        return f"## Sample user question\n\n```\n{q}\n```"

    new_doc, n = re.subn(
        r"^## Sample user question\s*\n+([^\n].+)$",
        wrap,
        doc,
        count=1,
        flags=re.MULTILINE,
    )
    if n:
        return new_doc, "Fence the literal NL test prompt for repeatability."
    return doc + "\n\n## Sample user question\n\n```\nWhy is my weekend hotel occupancy down versus the same weekends last year?\n```\n", "Add fenced sample prompt."


def _fix_expected_and_grounding(doc: str) -> tuple[str, str]:
    block = """## Expected output

Respond in plain language with: (1) an executive headline, (2) 3–5 bullets with specific metric movements and year-over-year framing, (3) explicit citations to the trusted sources and historical context used, and (4) clear time window and geography. Each bullet should include at least one quantitative cue (%, index change, or capacity units) when the sources support it."""
    return _replace_section(doc, "expected output", block), "Define plain-language shape, bullets, metrics, and citations."


def _fix_grounding_only(doc: str) -> tuple[str, str]:
    block = """

## Grounding expectations

Answers must be grounded in the six trusted internal tourism data sources and historical baselines provided to Aurora; the model must surface source attribution in the response body and refuse to invent statistics not present in those sources."""
    return doc.rstrip() + block + "\n", "Add explicit six-source grounding and attribution requirement."


def _fix_data_domains(doc: str) -> tuple[str, str]:
    block = """

## Data domains exercised

Visitation volume and shifts; visitor spend; accommodation occupancy and ADR where available; air capacity and bookings funnel proxies; commercial lodging booking pace; brand sentiment signals from trusted surveys and social listening (scope per Aurora data dictionary)."""
    return doc.rstrip() + block + "\n", "Name multiple tourism dimensions explicitly."


def _fix_failure_modes(doc: str) -> tuple[str, str]:
    block = """

## Failure modes / edge cases

If the SME geography is ambiguous, Aurora must ask a clarifying question. If the requested slice is missing or stale in the trusted sources, Aurora must say data is unavailable for that cut rather than guessing. Out-of-scope asks (non-tourism finance/legal advice) should be refused with a safe redirect."""
    return doc.rstrip() + block + "\n", "Specify ambiguity, sparse data, and scope refusal behavior."


def _fix_rai(doc: str) -> tuple[str, str]:
    block = """

## Responsible AI notes

Outputs may be incomplete or uncertain when signals conflict; operators should treat answers as decision support, not legal, financial, or regulatory advice. Enable human review for high-stakes operational decisions and log traces for optional audit."""
    return doc.rstrip() + block + "\n", "Add limitations, human review, and logging expectation."


def _fix_acceptance(doc: str) -> tuple[str, str]:
    block = """

## Acceptance criteria

- The response must include at least one explicit citation to trusted sources used for each major claim.
- The response must state comparison windows and geography in plain language.
- The system must log the user prompt, retrieval trace id, and model version for this test run (verify in pilot telemetry).
- If data is missing for a slice, the response must use \"data unavailable\" language and must not fabricate metrics."""
    return doc.rstrip() + block + "\n", "Add verifiable must/shall acceptance checks."


def _fix_placeholders(doc: str) -> tuple[str, str]:
    new_doc = re.sub(r"\b(TODO|TBD|FIXME)\b:?.*", "", doc, flags=re.IGNORECASE | re.MULTILINE)
    new_doc = re.sub(r"\n{3,}", "\n\n", new_doc)
    return new_doc, "Remove TODO/TBD/FIXME placeholders."


def _fix_six_feeds_explicit(doc: str) -> tuple[str, str]:
    block = """## Trusted data sources (six feeds)

Enumerate each trusted feed family Aurora may retrieve for SME answers (names must align to the internal data dictionary):

- Visitation and overnight arrivals (provincial / market-level where published)
- Visitor spending and market contribution
- Accommodation and lodging performance (e.g., occupancy, ADR where available)
- Air seat capacity and scheduled lift
- Forward air bookings and booking pace proxies
- Brand sentiment and traveler intent signals (trusted surveys / social listening per dictionary)

"""
    anchor = "## Sample user questions"
    if anchor in doc:
        return doc.replace(anchor, block + "\n" + anchor, 1), "Add six enumerated trusted feed bullets under a dedicated header."
    return doc.rstrip() + "\n\n" + block, "Append Trusted data sources (six feeds) section."


def _fix_pii_safety_expectation(doc: str) -> tuple[str, str]:
    if "personally identifiable" in doc.lower():
        return doc, "PII expectation already present"
    m = re.search(r"^(## Responsible AI notes)\s*\n", doc, re.MULTILINE | re.IGNORECASE)
    if m:
        insert_pos = m.end()
        bullet = (
            "- **PII / safety:** Operators must not paste personally identifiable information (PII) "
            "or sensitive guest-level data into prompts; use aggregated, anonymized operational questions only.\n\n"
        )
        return doc[:insert_pos] + bullet + doc[insert_pos:], "Add PII expectation bullet under Responsible AI notes."
    block = "\n## Testing safety (PII)\n\nOperators must not paste personally identifiable information (PII) or sensitive guest-level data into Aurora prompts; use aggregated, anonymized operational questions only.\n"
    return doc.rstrip() + block, "Append PII safety subsection."


_HANDLERS: dict[str, Callable[[str], tuple[str, str]]] = {
    "test_identifier": _fix_test_identifier,
    "objective_substance": _fix_objective,
    "preconditions_section": _fix_preconditions,
    "user_prompt_literal": _fix_user_prompt_literal,
    "expected_output_shape": _fix_expected_and_grounding,
    "grounding_trusted_sources": _fix_grounding_only,
    "tourism_data_domains": _fix_data_domains,
    "six_trusted_feeds_explicit": _fix_six_feeds_explicit,
    "failure_or_edge_case": _fix_failure_modes,
    "responsible_ai_basics": _fix_rai,
    "pii_safety_expectation": _fix_pii_safety_expectation,
    "acceptance_criteria_actionable": _fix_acceptance,
    "no_critical_placeholders": _fix_placeholders,
}


MOCK_SUPPORTED_PROFILE = "aurora_nl_test_prompts"


def mock_propose(markdown: str, profile: str = DEFAULT_PROFILE) -> tuple[str, str] | None:
    if profile != MOCK_SUPPORTED_PROFILE:
        return None
    ev = evaluate(markdown, profile=profile)
    if ev["all_pass"]:
        return None
    for c in ev["checks"]:
        if c["pass"]:
            continue
        cid = c["id"]
        handler = _HANDLERS.get(cid)
        if handler is None:
            return None
        new_doc, rationale = handler(markdown)
        if new_doc == markdown:
            continue
        return new_doc, rationale
    return None
