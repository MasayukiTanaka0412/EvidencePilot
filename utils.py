from __future__ import annotations

import html
import re
from pathlib import Path

INVALID_FILENAME_CHARS = r'[<>:"/\\|?*\x00-\x1F]'


def sanitize_name(value: str, max_length: int = 80) -> str:
    """Convert an arbitrary label into a safe Windows-compatible path segment."""
    clean = re.sub(INVALID_FILENAME_CHARS, "_", value or "")
    clean = re.sub(r"\s+", " ", clean).strip().strip(".")
    if not clean:
        clean = "unnamed"
    if len(clean) > max_length:
        clean = clean[:max_length].rstrip(" .")
    return clean or "unnamed"


def html_to_text(value: str) -> str:
    if not value:
        return ""
    stripped = re.sub(r"<[^>]+>", "", value)
    return html.unescape(stripped).strip()


def ensure_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
