"""Small formatting helpers shared across UI views."""
from __future__ import annotations


def format_number(n: float) -> str:
    if abs(n) >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if abs(n) >= 1_000:
        return f"{n / 1_000:.1f}K"
    if isinstance(n, float) and not n.is_integer():
        return f"{n:.2f}"
    return str(int(n))


def truncate(text: str, length: int = 120) -> str:
    return text if len(text) <= length else text[: length - 1].rstrip() + "…"
