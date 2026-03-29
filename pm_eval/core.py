"""Shared types and helpers for binary eval checks."""

from __future__ import annotations

import re
from dataclasses import dataclass, asdict
from typing import Any


@dataclass
class CheckResult:
    id: str
    pass_: bool
    detail: str

    @property
    def as_json_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["pass"] = d.pop("pass_")
        return d


def lower(text: str) -> str:
    return text.lower()


def word_count_in_section(text: str, header_pattern: str) -> int:
    m = re.search(header_pattern, text, re.IGNORECASE | re.MULTILINE)
    if not m:
        return 0
    start = m.end()
    rest = text[start:]
    next_h = re.search(r"^#{1,6}\s", rest, re.MULTILINE)
    section = rest[: next_h.start()] if next_h else rest
    return len(section.split())


def bullet_count_in_section_after_header(text: str, title_keywords: tuple[str, ...]) -> tuple[int, bool]:
    headers = list(re.finditer(r"^#{2,6}\s+(.+)$", text, re.MULTILINE))
    for i, hm in enumerate(headers):
        title = hm.group(1).lower()
        if not any(k in title for k in title_keywords):
            continue
        start = hm.end()
        end = headers[i + 1].start() if i + 1 < len(headers) else len(text)
        section = text[start:end]
        bullets = len(re.findall(r"^\s*[-*]\s+\S", section, re.MULTILINE))
        return bullets, True
    return 0, False
