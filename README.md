# PM document optimizer (git ratchet + binary eval)

Karpathy-style **autoresearch** adaptation for PM artifacts: edit a markdown document in a loop, score each candidate with a **programmatic** suite of pass/fail checks, **commit** only when the score increases, otherwise **revert** with `git restore`. Experiment history is appended to `logs/experiment_log.jsonl`.

## Artifact profiles (specialization)

Evals are grouped by **profile** so one codebase can score different PM deliverables. List names:

```bash
py -3 -m pm_eval.suite --list-profiles
```

| Profile | File module | What it pushes on |
|--------|-------------|-------------------|
| `aurora_nl_test_prompts` | `checks_aurora_nl.py` | NL test packs, 12 fenced prompts, six feeds, PII, grounding (default). |
| `prd` | `checks_prd.py` | Problem depth, users, solution, KPIs with numbers, scope in/out, dependencies, acceptance. |
| `strategy_doc` | `checks_strategy.py` | Vision substance, evidence, risks, priorities/horizon. |
| `one_pager` | `checks_one_pager.py` | Exec summary, decision ask, specific next steps, success signal. |
| `skill_or_system_prompt` | `checks_skill_prompt.py` | Role/goal, length, output format, edge cases. |

**Score a file with a profile:**

```bash
py -3 -m pm_eval.suite artifacts/prd/prd_seed.md --profile prd
```

**Optimize with a profile:**

```bash
py -3 agent/optimize.py --profile prd --artifact artifacts/prd/prd_seed.md --proposer llm
```

The **mock** proposer only has canned patches for `aurora_nl_test_prompts`. For `prd`, `strategy_doc`, etc., use **`--proposer llm`** (or extend `agent/proposer_mock.py`).

The default artifact path remains the Aurora NL draft; override with `--artifact`.

## Quickstart (Windows / macOS / Linux)

```bash
cd pm-document-optimizer
py -3 -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
py -3 agent/optimize.py --proposer mock
```

Starter files:

- `artifacts/test_cases/aurora_prototype_testing_prompt_draft.md` — default Aurora NL scenario pack.
- `artifacts/prd/prd_seed.md` — thin PRD stub (try with `--profile prd`).
- `artifacts/strategy/strategy_seed.md` — thin strategy stub (`--profile strategy_doc`).

If `git` is not installed, the ratchet falls back to restoring the last accepted file contents.

- **Mock proposer:** offline patches for **Aurora NL** profile only.
- **LLM proposer:** **Gemini only** via [`google-genai`](https://github.com/googleapis/python-genai).
  - **API key:** set `GEMINI_API_KEY` or `GOOGLE_API_KEY`; optional `GEMINI_MODEL` (default `gemini-2.0-flash`).
  - **Vertex AI (no user API key):** set `GOOGLE_CLOUD_PROJECT` (or `PM_VERTEX_PROJECT`), optional `PM_VERTEX_LOCATION` (default `us-central1`), ensure **Application Default Credentials** (Workbench / Colab with GCP connector / Cloud Run service account). Run with `--vertex` or set `PM_GEMINI_VERTEX=1`.

```bash
set GEMINI_API_KEY=...
py -3 agent/optimize.py --proposer llm --profile prd --artifact artifacts/prd/prd_seed.md
```

```bash
set GOOGLE_CLOUD_PROJECT=my-project
py -3 agent/optimize.py --proposer llm --vertex --profile prd --artifact artifacts/prd/prd_seed.md
```

### Personal GitHub + Vertex Colab / Workbench

Yes: keep the repo on **GitHub**, open **Vertex AI Workbench** or **Colab Enterprise**, **clone** (or sync) the repo, `pip install -r requirements.txt`, `cd` into the project root, then run `python agent/optimize.py ...`. Use **`--vertex`** when the notebook runtime has a GCP identity with **Vertex AI User** (or equivalent) on your project. Artifacts under `artifacts/` are plain files—edit or mount them as needed; logs go to `logs/experiment_log.jsonl`.

## Run eval only

```bash
py -3 -m pm_eval.suite artifacts/test_cases/aurora_prototype_testing_prompt_draft.md
py -3 -m pm_eval.suite artifacts/test_cases/aurora_prototype_testing_prompt_draft.md --profile aurora_nl_test_prompts
```

JSON output includes `"profile"` and per-check results.

## Friendly chart from the log

```bash
py -3 -m agent.visualize_log
```

Baseline log lines now include `"profile"` when present.

```bash
py -3 agent/optimize.py --proposer mock --print-chart
```

## Git ratchet

The first run calls `git init` if needed and makes an initial commit. Each accepted improvement is committed; rejected candidates are restored from HEAD.

## GCP

Use the included `Dockerfile` with **Cloud Build** + **Cloud Run**. Override `CMD` to pass `--profile`, optional `--vertex`, and mount artifacts. For API-key mode inject `GEMINI_API_KEY` or `GOOGLE_API_KEY` from **Secret Manager**; for Vertex use the runtime service account and set `GOOGLE_CLOUD_PROJECT` / `PM_VERTEX_LOCATION`.

## Where checks live

- `pm_eval/registry.py` — profile → ordered list of check functions.
- `pm_eval/checks_aurora_nl.py` — Aurora NL pack (14 checks).
- `pm_eval/checks_prd.py`, `checks_strategy.py`, `checks_one_pager.py`, `checks_skill_prompt.py` — other profiles.
- `pm_eval/checks_common.py` — shared checks (e.g. placeholders, acceptance header).

## Customize

- Add a profile: new `checks_*.py` + register in `registry.py`.
- Tune thresholds (word counts, regexes) in the relevant `checks_*.py`.
- Extend `agent/proposer_mock.py` with handlers keyed by check `id` for offline runs on new profiles.

## Responsible AI

Aurora and PRD-style docs can include RAI or safety expectations; extend checks as your governance bar tightens.
