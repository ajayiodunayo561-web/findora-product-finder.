from __future__ import annotations
from dataclasses import dataclass, field
from typing import Protocol


@dataclass
class TrendSignal:
    keyword: str
    source: str
    score: float | None = None
    extra: dict = field(default_factory=dict)


class TrendProvider(Protocol):
    name: str
    async def fetch(self, query: str, market: str | None) -> list[TrendSignal]: ...


class NullProvider:
    name = "none"
    async def fetch(self, query: str, market: str | None) -> list[TrendSignal]:
        return []


def get_trend_provider() -> TrendProvider:
    return NullProvider()


def data_source_label(has_live: bool, provider_name: str) -> str:
    if has_live:
        return f"🟢 Live trend data (source: {provider_name})"
    return "🟡 AI-generated research idea (no live trend feed configured)"
