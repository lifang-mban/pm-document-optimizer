# Aurora AI Insights Generator — testing prompt (draft)

**Test case ID:** TC-AURORA-001

**Test case:** SME operator asks why weekend hotel demand looks soft compared to last year.

## Objective

Validate that Aurora returns an SME-appropriate, plain-language insight when the operator asks about weekend lodging softness versus last year. The answer must cite trusted Destination Canada tourism signals across visitation, spend, accommodation, air capacity, booking, and brand sentiment, state the comparison window, and avoid overclaiming when coverage is incomplete. This mitigates reputational risk from an ungrounded "analyst in a box" experience.

## Sample user question

```
Why is my weekend occupancy down?
```

## Expected output

Respond in plain language with: (1) an executive headline, (2) 3–5 bullets with specific metric movements and year-over-year framing, (3) explicit citations to the trusted sources and historical context used, and (4) clear time window and geography. Each bullet should include at least one quantitative cue (%, index change, or capacity units) when the sources support it.

## Preconditions

- Operator is signed into the Aurora AI Insights Generator pilot with the internal feature flag enabled.
- The six trusted source feeds are loaded to the same published vintage (no partial refresh mid-run).
- Default geography is Canada unless the prompt narrows to a province, city, or corridor.

## Notes

Uses visitation and spend.

## Failure modes / edge cases

If the SME geography is ambiguous, Aurora must ask a clarifying question. If the requested slice is missing or stale in the trusted sources, Aurora must say data is unavailable for that cut rather than guessing. Out-of-scope asks (non-tourism finance/legal advice) should be refused with a safe redirect.

## Responsible AI notes

Outputs may be incomplete or uncertain when signals conflict; operators should treat answers as decision support, not legal, financial, or regulatory advice. Enable human review for high-stakes operational decisions and log traces for optional audit.

## Acceptance criteria

- The response must include at least one explicit citation to trusted sources used for each major claim.
- The response must state comparison windows and geography in plain language.
- The system must log the user prompt, retrieval trace id, and model version for this test run (verify in pilot telemetry).
- If data is missing for a slice, the response must use "data unavailable" language and must not fabricate metrics.
