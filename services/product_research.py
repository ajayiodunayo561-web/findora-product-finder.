from __future__ import annotations
import logging
from typing import Any

from services.deepseek import chat_json, DeepSeekError
from services.trend_data import get_trend_provider, data_source_label

log = logging.getLogger(__name__)

_INTENT_SYSTEM = (
    "You are an intent classifier for a product-research Telegram bot. "
    "Return ONLY JSON with keys: intent, market, category, count. "
    "intent in {research, clarify, help, other}. "
    "market = country/region if mentioned else null. "
    "category = product niche if mentioned else null. "
    "count = requested number of products (default 3, max 5)."
)


async def detect_intent(text: str) -> dict[str, Any]:
    try:
        data = await chat_json(_INTENT_SYSTEM, text, temperature=0.0)
    except DeepSeekError as e:
        log.warning("intent detection failed: %s", e)
        return {"intent": "research", "market": None, "category": None, "count": 3}
    data.setdefault("intent", "research")
    data.setdefault("count", 3)
    data["count"] = max(1, min(int(data["count"] or 3), 5))
    return data


_PRODUCT_SYSTEM = """You are Findora, a senior e-commerce product researcher.
Return ONLY valid JSON with this shape:

{
  "products": [
    {
      "name": "string",
      "category": "string",
      "trend_status": "Trending|Emerging|Stable|Declining",
      "demand_analysis": "string",
      "target_audience": "string",
      "target_market": "string",
      "estimated_price": "string or 'Not reliably available'",
      "sourcing_info": "string",
      "competition_level": "Low|Medium|High",
      "why_consider": "string",
      "research_note": "string"
    }
  ]
}

RULES:
- Never invent sales numbers, rankings, or fake statistics.
- If unsure, write 'Not reliably available'.
- Each field under 320 characters.
"""


async def generate_products(query: str, market: str | None, category: str | None, count: int) -> list[dict[str, Any]]:
    provider = get_trend_provider()
    live_signals = await provider.fetch(query, market)
    has_live = bool(live_signals)
    live_context = "No live trend data available." if not has_live else (
        "Live trend signals:\n" + "\n".join(f"- {s.keyword} ({s.source})" for s in live_signals)
    )
    user_prompt = (
        f"User request: {query}\n"
        f"Target market: {market or 'Global'}\n"
        f"Category focus: {category or 'Any'}\n"
        f"Number of products: {count}\n"
        f"{live_context}\n"
        "Return the JSON object."
    )
    data = await chat_json(_PRODUCT_SYSTEM, user_prompt, temperature=0.6)
    products = data.get("products", [])
    if not isinstance(products, list) or not products:
        raise DeepSeekError("Empty product list")
    return products


def format_results(products: list[dict[str, Any]], has_live: bool, provider_name: str) -> str:
    chunks: list[str] = ["🔎 FINDORA PRODUCT DISCOVERY RESULTS\n"]
    for i, p in enumerate(products, 1):
        chunks.append(
            f"\n─── Product {i} ───\n"
            f"Product Name: {p.get('name','—')}\n"
            f"📂 Category: {p.get('category','—')}\n"
            f"🔥 Trend Status: {p.get('trend_status','—')}\n"
            f"📈 Demand Analysis: {p.get('demand_analysis','—')}\n"
            f"🎯 Target Audience: {p.get('target_audience','—')}\n"
            f"🌍 Target Market: {p.get('target_market','—')}\n"
            f"💰 Estimated Selling Price: {p.get('estimated_price','Not reliably available')}\n"
            f"🏷️ Product Sourcing Information: {p.get('sourcing_info','—')}\n"
            f"⭐ Competition Level: {p.get('competition_level','—')}\n"
            f"💡 Why Consider This Product?\n{p.get('why_consider','—')}\n"
            f"⚠️ Research Note:\n{p.get('research_note','—')}\n"
        )
    chunks.append(f"\n📊 Data Source: {data_source_label(has_live, provider_name)}")
    return "".join(chunks)
