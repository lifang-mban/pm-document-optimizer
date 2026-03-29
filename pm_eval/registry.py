"""Artifact profiles: each maps to an ordered list of binary check callables."""

from __future__ import annotations

from typing import Any, Callable

from pm_eval.checks_aurora_nl import AURORA_NL_PACK_CHECKS
from pm_eval.checks_one_pager import ONE_PAGER_CHECKS
from pm_eval.checks_prd import PRD_CHECKS
from pm_eval.checks_skill_prompt import SKILL_OR_SYSTEM_PROMPT_CHECKS
from pm_eval.checks_strategy import STRATEGY_CHECKS
from pm_eval.core import CheckResult

CheckFn = Callable[[str], CheckResult]

CHECK_PROFILES: dict[str, list[CheckFn]] = {
    "aurora_nl_test_prompts": AURORA_NL_PACK_CHECKS,
    "prd": PRD_CHECKS,
    "strategy_doc": STRATEGY_CHECKS,
    "one_pager": ONE_PAGER_CHECKS,
    "skill_or_system_prompt": SKILL_OR_SYSTEM_PROMPT_CHECKS,
}

DEFAULT_PROFILE = "aurora_nl_test_prompts"


def list_profiles() -> list[str]:
    return sorted(CHECK_PROFILES.keys())


def get_checks(profile: str) -> list[CheckFn]:
    if profile not in CHECK_PROFILES:
        raise ValueError(
            f"Unknown eval profile {profile!r}. Choose one of: {', '.join(list_profiles())}",
        )
    return CHECK_PROFILES[profile]


def evaluate(markdown: str, profile: str = DEFAULT_PROFILE) -> dict[str, Any]:
    checks = get_checks(profile)
    results = [fn(markdown) for fn in checks]
    passed = sum(1 for r in results if r.pass_)
    return {
        "profile": profile,
        "score": passed,
        "max": len(results),
        "passed": passed,
        "total": len(results),
        "checks": [r.as_json_dict for r in results],
        "all_pass": passed == len(results),
    }
