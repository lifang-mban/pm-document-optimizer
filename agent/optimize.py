"""
Document optimizer: propose → eval → keep if improved → git commit; else revert.

Run from repo root `pm-document-optimizer` with PYTHONPATH set (see README).
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _ensure_path() -> None:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))


def _git_available() -> bool:
    return shutil.which("git") is not None


def _run_git(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        check=False,
        text=True,
        capture_output=True,
    )


def _init_git_if_needed(cwd: Path) -> None:
    if not _git_available():
        return
    if (cwd / ".git").exists():
        return
    p = _run_git(["init"], cwd)
    if p.returncode != 0:
        raise RuntimeError(p.stderr or "git init failed")
    subprocess.run(["git", "add", "-A"], cwd=str(cwd), check=True)
    subprocess.run(["git", "commit", "-m", "chore: init pm-document-optimizer"], cwd=str(cwd), check=False)


def _git_commit_file(path: Path, message: str, cwd: Path) -> None:
    if not _git_available() or not (cwd / ".git").exists():
        return
    rel = path.relative_to(cwd).as_posix()
    subprocess.run(["git", "add", rel], cwd=str(cwd), check=True)
    subprocess.run(["git", "commit", "-m", message], cwd=str(cwd), check=True)


def _git_revert_file(path: Path, cwd: Path) -> None:
    if not _git_available() or not (cwd / ".git").exists():
        return
    rel = path.relative_to(cwd).as_posix()
    subprocess.run(["git", "restore", rel], cwd=str(cwd), check=True)


def _append_log(cwd: Path, entry: dict) -> None:
    log_dir = cwd / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "experiment_log.jsonl"
    entry["ts"] = datetime.now(timezone.utc).isoformat()
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def main() -> None:
    _ensure_path()
    from pm_eval.registry import DEFAULT_PROFILE, evaluate, list_profiles

    parser = argparse.ArgumentParser(description="Optimize a markdown artifact against pm_eval checks (git ratchet).")
    parser.add_argument(
        "--artifact",
        type=Path,
        default=ROOT / "artifacts" / "test_cases" / "aurora_prototype_testing_prompt_draft.md",
        help="Path to markdown file (tracked under repo root).",
    )
    parser.add_argument(
        "--profile",
        "-p",
        default=DEFAULT_PROFILE,
        metavar="NAME",
        help=f"Eval profile (default {DEFAULT_PROFILE}). Same names as: python -m pm_eval.suite --list-profiles",
    )
    parser.add_argument("--max-rounds", type=int, default=30)
    parser.add_argument("--proposer", choices=("mock", "llm"), default="mock")
    parser.add_argument(
        "--vertex",
        action="store_true",
        help="For --proposer llm: call Gemini on Vertex AI (ADC / service account). Set GOOGLE_CLOUD_PROJECT and optional PM_VERTEX_LOCATION.",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Gemini model id for --proposer llm (default: gemini-2.0-flash). Override with GEMINI_MODEL.",
    )
    parser.add_argument(
        "--print-chart",
        action="store_true",
        help="After the run, print an ASCII score chart from this session in the log.",
    )
    args = parser.parse_args()

    if args.profile not in list_profiles():
        raise SystemExit(f"Unknown --profile {args.profile!r}. Valid: {', '.join(list_profiles())}")

    cwd = ROOT
    artifact: Path = args.artifact if args.artifact.is_absolute() else cwd / args.artifact
    if not artifact.exists():
        raise SystemExit(f"Artifact not found: {artifact}")

    use_git = _git_available()
    _init_git_if_needed(cwd)
    if not use_git:
        print("[ratchet] git not found; using in-file revert to last accepted version.")

    if args.proposer == "mock" and args.profile != "aurora_nl_test_prompts":
        print(
            "[note] Mock proposer only auto-patches profile 'aurora_nl_test_prompts'. "
            "For other profiles use --proposer llm (or add handlers in agent/proposer_mock.py).",
        )

    text = artifact.read_text(encoding="utf-8")
    last_accepted = text
    baseline = evaluate(text, profile=args.profile)
    _append_log(
        cwd,
        {
            "event": "baseline",
            "artifact": str(artifact.relative_to(cwd)),
            "profile": args.profile,
            "score": baseline["score"],
            "checks": baseline["checks"],
        },
    )

    llm_resolved: str | None = None
    if args.proposer == "mock":
        from agent.proposer_mock import mock_propose

        def propose(m: str):
            return mock_propose(m, profile=args.profile)
    else:
        from agent.proposer_llm import gemini_surface_label, llm_propose, resolve_gemini_surface

        gemini_surface = resolve_gemini_surface(vertex_flag=args.vertex)
        llm_resolved = gemini_surface_label(gemini_surface)
        print(
            f"[llm] {llm_resolved} model="
            f"{args.model or '(GEMINI_MODEL / gemini-2.0-flash)'}",
        )

        def propose(m: str):
            return llm_propose(
                m,
                model=args.model,
                profile=args.profile,
                gemini_surface=gemini_surface,
            )

    current_score = baseline["score"]

    for rnd in range(1, args.max_rounds + 1):
        text_before = artifact.read_text(encoding="utf-8")
        ev_before = evaluate(text_before, profile=args.profile)

        if args.proposer == "mock":
            proposed = propose(text_before)
            if proposed is None:
                ev_chk = evaluate(text_before, profile=args.profile)
                if ev_chk["all_pass"]:
                    print(f"[round {rnd}] all checks pass; stopping.")
                else:
                    print(f"[round {rnd}] mock proposer could not advance; stopping.")
                break
            candidate, rationale = proposed
        else:
            try:
                candidate, rationale = propose(text_before)
            except Exception as e:
                print(f"[round {rnd}] LLM proposer error: {e}")
                _append_log(
                    cwd,
                    {
                        "event": "proposer_error",
                        "round": rnd,
                        "error": str(e),
                    },
                )
                break

        if candidate == text_before:
            print(f"[round {rnd}] no-op proposal; stopping.")
            break

        artifact.write_text(candidate, encoding="utf-8")
        ev_after = evaluate(candidate, profile=args.profile)
        improved = ev_after["score"] > current_score

        log_entry = {
            "event": "round",
            "round": rnd,
            "proposer": args.proposer,
            "llm_backend": llm_resolved,
            "rationale": rationale,
            "score_before": ev_before["score"],
            "score_after": ev_after["score"],
            "kept": improved,
            "failing_before": [c["id"] for c in ev_before["checks"] if not c["pass"]],
            "failing_after": [c["id"] for c in ev_after["checks"] if not c["pass"]],
        }

        if improved:
            msg = f"eval: improve score {ev_before['score']}→{ev_after['score']} ({rationale})"
            _git_commit_file(artifact, msg, cwd)
            last_accepted = candidate
            current_score = ev_after["score"]
            print(f"[round {rnd}] KEPT score {ev_after['score']}/{ev_after['max']} - {rationale}")
        else:
            if use_git and (cwd / ".git").exists():
                _git_revert_file(artifact, cwd)
            else:
                artifact.write_text(last_accepted, encoding="utf-8")
            print(f"[round {rnd}] REVERT score would be {ev_after['score']} (was {current_score}) - {rationale}")

        _append_log(cwd, log_entry)

        if ev_after["all_pass"]:
            print("All checks pass.")
            break

    final_text = artifact.read_text(encoding="utf-8")
    final_ev = evaluate(final_text, profile=args.profile)
    print(json.dumps(final_ev, indent=2))

    if args.print_chart:
        from agent.visualize_log import build_timeline, load_sessions, render_chart, render_legend

        log_path = cwd / "logs" / "experiment_log.jsonl"
        sessions = load_sessions(log_path)
        if sessions:
            sess = sessions[-1]
            scores, outcomes, max_score = build_timeline(sess)
            print()
            print(render_chart(scores, outcomes, max_score))
            print(render_legend())


if __name__ == "__main__":
    main()
