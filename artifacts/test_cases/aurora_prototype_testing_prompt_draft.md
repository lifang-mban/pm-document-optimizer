# Aurora AI Insights Generator — test scenario draft

**Test case ID:** TC-AURORA-SCENARIOS-001

## Objective

Validate that Aurora answers representative Canadian tourism SME natural-language questions using trusted Destination Canada signals across traveler sentiment, overnight arrivals, visitor spending, hotel performance, forward air bookings, air seat capacity, international market mix, and provincial/regional views. Responses must stay plain-language, grounded in historical and descriptive context, and must handle forecast-style asks without presenting unsupported predictions.

## Preconditions

- Operator is signed into the Aurora AI Insights Generator pilot with internal feature flags as configured for Destination Canada SMEs.
- The six trusted source feeds are loaded to a consistent published vintage for the test window (no partial refresh mid-run unless testing refresh behavior explicitly).

## Trusted data sources (six feeds)

Enumerate each trusted feed family Aurora may retrieve for SME answers (names must align to the internal data dictionary):

- Visitation and overnight arrivals (provincial / market-level where published)
- Visitor spending and market contribution
- Accommodation and lodging performance (e.g., occupancy, ADR where available)
- Air seat capacity and scheduled lift
- Forward air bookings and booking pace proxies
- Brand sentiment and traveler intent signals (trusted surveys / social listening per dictionary)


## Sample user questions

Run each block as a separate NL test. Wording is fixed for repeatability.

### 1 — Sentiment (markets)

```
How does traveler sentiment toward Canada differ between Germany and France?
```

### 2 — Arrivals (province)

```
How did overnight arrivals numbers change in Nova Scotia over the past year?
```

### 3 — Spending (province + markets)

```
How has visitor spending changed in British Columbia recently, and which markets contributed most?
```

### 4 — Hotel performance (city)

```
How is hotel performance trending in Vancouver?
```

### 5 — Forward bookings (province)

```
What do forward air bookings suggest about upcoming travel demand to Ontario?
```

### 6 — Air capacity + demand read

```
Has air seat capacity to Canada increased or decreased recently, and what might that mean for tourism demand?
```

### 7 — International markets (intent + spending)

```
Which international markets appear to be strengthening in terms of visitor travel intent and spending?
```

### 8 — Provincial snapshot

```
How is tourism performing in Prince Edward Island?
```

### 9 — Forward-looking signals (Manitoba)

```
What signals suggest tourism demand in Manitoba may change in the coming months?
```

### 10 — Regional stress test

```
Are there any early signs of tourism slowdown in Northern Canada?
```

### 11 — Capacity vs spending alignment

```
Are changes in air capacity aligned with changes in visitor spending to Canada in summer 2025?
```

### 12 — Forecast refusal (behavioral)

```
What will tourism demand in Alberta look like next year?
```

**Expected behavior for prompt 12:** The system should clarify that it does not provide forecasts and focuses on historical descriptive insights (trends, comparisons, grounded context), not future-year predictions.

## Expected output

For each prompt, Aurora should return plain language insights: a short headline first, then supporting bullets with cited metrics or indices where available, and explicit reference to trusted data sources and time windows. Where data are missing or ambiguous, the answer should say so instead of guessing.

## Failure modes / edge cases

If geography or time range is underspecified, Aurora should ask a clarifying question or state default scope (e.g., Canada-wide vs provincial). If a slice is unavailable in trusted sources, Aurora must not fabricate metrics.

## Responsible AI notes

- **PII / safety:** Operators must not paste personally identifiable information (PII) or sensitive guest-level data into prompts; use aggregated, anonymized operational questions only.

Outputs are decision support for operators, not legal, financial, or regulatory advice. Surface uncertainty and limitations where signals conflict.

## Acceptance criteria

- Each answer must cite or clearly attribute the trusted tourism sources used for major claims.
- Prompt 12 must not present a numeric or categorical forecast for “next year”; it must redirect to historical/descriptive framing or refuse unsupported prediction.
- The system must log trace identifiers for pilot runs when telemetry is enabled.

## Notes

Draft scenario pack for Aurora AI Insights Generator NL testing. Refine with product and data dictionary labels as feeds evolve.
