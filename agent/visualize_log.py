"""
Pretty-print experiment_log.jsonl as an ASCII score chart (rounds vs ratcheted score).

Run from repo root: python -m agent.visualize_log
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _ensure_path() -> None:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))


def load_sessions(log_path: Path) -> list[dict]:
    if not log_path.exists():
        return []
    sessions: list[dict] = []
    current: dict | None = None
    with log_path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            if obj.get("event") == "baseline":
                if current is not None:
                    sessions.append(current)
                current = {"baseline": obj, "rounds": []}
            elif obj.get("event") == "round" and current is not None:
                current["rounds"].append(obj)
    if current is not None:
        sessions.append(current)
    return sessions


def build_timeline(session: dict) -> tuple[list[int], list[str | None], int]:
    """Ratcheted scores per step, outcome per round column, max_score from eval size."""
    baseline = session["baseline"]
    max_score = len(baseline.get("checks", [])) or 11
    scores: list[int] = [int(baseline["score"])]
    outcomes: list[str | None] = [None]

    for r in session["rounds"]:
        kept = r.get("kept", True)
        if kept:
            scores.append(int(r["score_after"]))
            outcomes.append("keep")
        else:
            scores.append(scores[-1])
            outcomes.append("revert")

    return scores, outcomes, max_score


def render_chart(scores: list[int], outcomes: list[str | None], max_score: int) -> str:
    """
    Filled-column chart: each column is a stack of * from the bottom up to the ratcheted score.
    Reads like a staircase when score increases left to right.
    """
    if not scores:
        return "(no data)"

    n = len(scores)
    col_w = 3  # column width for chart body

    lines: list[str] = []

    # Y-axis: one row per integer level, top = 100%, bottom = 0%
    for level in range(max_score, 0, -1):
        pct = round(100 * level / max_score)
        if level == max_score:
            y_label = "SCORE"
        else:
            y_label = f"{pct:>3}%"

        parts: list[str] = []
        for i in range(n):
            s = scores[i]
            parts.append(("*" if s >= level else " ").center(col_w))
        lines.append(f"{y_label:>6} |" + "".join(parts))

    # Baseline axis
    lines.append("       +" + ("-" * (col_w * n)))
    # X labels: B0 = after baseline eval, R1.. = after each round
    x1 = "".join(("B0" if i == 0 else f"R{i}").center(col_w) for i in range(n))
    lines.append("       " + x1)
    lines.append("        (each column = ratcheted binary eval score after that step)")

    # Kept / revert row
    parts2: list[str] = []
    for i in range(n):
        o = outcomes[i] if i < len(outcomes) else None
        if o == "keep":
            sym = "K"
        elif o == "revert":
            sym = "R"
        else:
            sym = "."
        parts2.append(sym.center(col_w))
    lines.append("       |" + "".join(parts2))
    lines.append("        K = kept (score went up)   R = reverted   . = baseline")

    return "\n".join(lines)


def render_legend() -> str:
    return "\n".join(
        [
            "",
            "How to read this",
            "  - Each column is one moment in time: B0 = score right after baseline, R1 = after round 1, and so on.",
            "  - Taller stacks of * = more binary eval checks passing.",
            "  - Git: each keep can be a commit; a revert puts the file back to the last good version.",
            "  - The run stops when every check passes or the proposer cannot improve the score.",
        ]
    )


def main() -> None:
    _ensure_path()
    p = argparse.ArgumentParser(description="Visualize experiment_log.jsonl as an ASCII chart.")
    p.add_argument(
        "--log",
        type=Path,
        default=ROOT / "logs" / "experiment_log.jsonl",
        help="Path to JSONL log file",
    )
    p.add_argument(
        "--session",
        type=int,
        default=-1,
        help="Which session to show (0 = first, -1 = last)",
    )
    args = p.parse_args()

    sessions = load_sessions(args.log)
    if not sessions:
        print(f"No sessions found in {args.log} (need at least one baseline line).")
        sys.exit(1)

    idx = args.session if args.session >= 0 else len(sessions) + args.session
    if idx < 0 or idx >= len(sessions):
        print(f"Session index out of range (have {len(sessions)} session(s)).")
        sys.exit(1)

    sess = sessions[idx]
    base = sess["baseline"]
    artifact = base.get("artifact", "?")
    scores, outcomes, max_score = build_timeline(sess)

    pct = 100 * scores[-1] / max_score if max_score else 0
    header = (
        f"Session {idx + 1}/{len(sessions)}  |  {artifact}\n"
        f"Final score: {scores[-1]}/{max_score}  ({pct:.0f}%)  |  optimization rounds: {len(sess['rounds'])}"
    )

    print(header)
    print()
    print(render_chart(scores, outcomes, max_score))
    print(render_legend())


if __name__ == "__main__":
    main()
