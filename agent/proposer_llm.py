"""
LLM-backed proposer: one surgical find/replace per iteration (JSON contract).

Gemini only (Google), via `google-genai`:
- API key: GEMINI_API_KEY or GOOGLE_API_KEY
- Vertex AI: GCP project + region + Application Default Credentials (Workbench, Colab with GCP, Cloud Run SA)
"""

from __future__ import annotations

import json
import os
import re
from typing import Any, Literal

GeminiSurface = Literal["api_key", "vertex"]

PROFILE_GUIDANCE: dict[str, str] = {
    "aurora_nl_test_prompts": "GenAI tourism SME NL test scenarios (Aurora): trusted sources, PII, fenced prompts, acceptance criteria.",
    "prd": "Data/analytics product PRD: problem, users, solution, KPIs with numbers, scope in/out, dependencies, acceptance criteria.",
    "strategy_doc": "Strategy doc: vision, evidence, risks, priorities/horizon.",
    "one_pager": "Exec one-pager: exec summary, decision ask, dated/owned next steps, success signal.",
    "skill_or_system_prompt": "System prompt or skill: clear role/goal, output format, edge cases, sufficient length.",
}


def _gemini_key() -> str | None:
    return os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")


def _vertex_project() -> str | None:
    return (
        os.environ.get("PM_VERTEX_PROJECT")
        or os.environ.get("GOOGLE_CLOUD_PROJECT")
        or os.environ.get("GCP_PROJECT")
    )


def _vertex_location() -> str:
    return os.environ.get("PM_VERTEX_LOCATION", "us-central1")


def resolve_gemini_surface(*, vertex_flag: bool) -> GeminiSurface:
    """Pick API key vs Vertex from CLI and env."""
    env_vertex = (os.environ.get("PM_GEMINI_VERTEX") or "").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )
    if vertex_flag or env_vertex:
        if not _vertex_project():
            raise RuntimeError(
                "Vertex mode requires GOOGLE_CLOUD_PROJECT (or PM_VERTEX_PROJECT / GCP_PROJECT). "
                "Optional: PM_VERTEX_LOCATION (default us-central1). Use Application Default Credentials.",
            )
        return "vertex"
    if not _gemini_key():
        raise RuntimeError(
            "Set GEMINI_API_KEY or GOOGLE_API_KEY for Gemini API key mode, "
            "or use --vertex with GOOGLE_CLOUD_PROJECT and Vertex ADC.",
        )
    return "api_key"


def gemini_surface_label(surface: GeminiSurface) -> str:
    return f"gemini_{surface}"


def _extract_json_object(text: str) -> dict[str, Any]:
    text = text.strip()
    m = re.search(r"\{[\s\S]*\}", text)
    if not m:
        raise ValueError("No JSON object in model output")
    return json.loads(m.group(0))


def _system_and_user(markdown: str, profile: str) -> tuple[str, str]:
    focus = PROFILE_GUIDANCE.get(profile, "PM markdown artifact.")
    system = (
        f"You improve markdown for this artifact type: {focus}\n"
        "Make ONE surgical edit only. Reply with JSON only:\n"
        '{"rationale": "short", "find": "exact substring from the document", "replace": "replacement text"}\n'
        "Rules: find must match exactly once; no large rewrites; prefer adding missing sections or bullets "
        "that satisfy typical PM rigor for this doc type."
    )
    user = "Current document:\n\n" + markdown
    return system, user


def _apply_find_replace(markdown: str, data: dict[str, Any]) -> tuple[str, str]:
    find = data.get("find", "")
    replace = data.get("replace", "")
    rationale = str(data.get("rationale", "llm edit"))
    if not isinstance(find, str) or not isinstance(replace, str):
        raise ValueError("find/replace must be strings")
    count = markdown.count(find)
    if count != 1:
        raise ValueError(f"find must appear exactly once; appearances={count}")
    return markdown.replace(find, replace, 1), rationale


def _make_genai_client(surface: GeminiSurface):
    try:
        from google import genai
    except ImportError as e:
        raise RuntimeError("Install: pip install google-genai (see requirements.txt)") from e

    if surface == "vertex":
        project = _vertex_project()
        assert project
        return genai.Client(
            vertexai=True,
            project=project,
            location=_vertex_location(),
        )
    key = _gemini_key()
    assert key
    return genai.Client(api_key=key)


def _complete_gemini(
    markdown: str,
    *,
    model: str | None,
    profile: str,
    surface: GeminiSurface,
) -> str:
    from google.genai import types

    client = _make_genai_client(surface)
    use_model = model or os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
    system, user = _system_and_user(markdown, profile)
    response = client.models.generate_content(
        model=use_model,
        contents=user,
        config=types.GenerateContentConfig(
            temperature=0.2,
            system_instruction=system,
        ),
    )
    raw = (getattr(response, "text", None) or "").strip()
    if not raw:
        raise RuntimeError("Gemini returned empty text (safety filter or model error).")
    return raw


def llm_propose(
    markdown: str,
    *,
    model: str | None = None,
    profile: str = "aurora_nl_test_prompts",
    gemini_surface: GeminiSurface | None = None,
    vertex: bool = False,
) -> tuple[str, str]:
    surface = gemini_surface if gemini_surface is not None else resolve_gemini_surface(vertex_flag=vertex)
    raw = _complete_gemini(markdown, model=model, profile=profile, surface=surface)
    data = _extract_json_object(raw)
    return _apply_find_replace(markdown, data)
