"""
J.A.R.V.I.S. Live News Tool
Fetches top world, technology, and business headlines.
Supports NewsAPI with automatic fallback to live Google News RSS (zero key required).
"""
import os
import requests
import xml.etree.ElementTree as ET
import logging
from typing import Dict, Any, List

from tools.base import BaseTool, ToolResult
from security.capabilities import Capability, RiskTier

logger = logging.getLogger("jarvis.tools.news")


class NewsTool(BaseTool):
    @property
    def id(self) -> str:
        return "news"

    @property
    def name(self) -> str:
        return "Live News Headlines"

    @property
    def description(self) -> str:
        return "Fetch current top news headlines across world, technology, business, or general categories."

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "enum": ["general", "technology", "business", "science", "world"],
                    "description": "News category. Defaults to technology."
                },
                "limit": {
                    "type": "integer",
                    "description": "Number of headlines to return (1-10). Defaults to 5."
                }
            }
        }

    @property
    def required_capability(self) -> Capability:
        return Capability.CHAT

    @property
    def risk_tier(self) -> RiskTier:
        return RiskTier.LOW

    def execute(self, params: Dict[str, Any]) -> ToolResult:
        category = params.get("category", "technology").lower()
        limit = min(10, max(1, int(params.get("limit", 5))))

        # 1. Try NewsAPI if key is configured
        api_key = os.environ.get("NEWS_API_KEY", "")
        if api_key:
            try:
                cat_param = "technology" if category == "technology" else "business" if category == "business" else "general"
                url = f"https://newsapi.org/v2/top-headlines?country=in&category={cat_param}&pageSize={limit}&apiKey={api_key}"
                resp = requests.get(url, timeout=7)
                if resp.status_code == 200:
                    data = resp.json()
                    articles = data.get("articles", [])
                    if articles:
                        lines = [f"📰 Top {category.title()} Headlines:"]
                        for a in articles[:limit]:
                            src = a.get("source", {}).get("name", "Unknown")
                            title = a.get("title", "Untitled")
                            lines.append(f"• {title} ({src})")
                        return ToolResult(success=True, data="\n".join(lines))
            except Exception as e:
                logger.warning(f"NewsAPI error, falling back to RSS: {e}")

        # 2. Resilient Fallback: Google News RSS (Zero Key Required)
        try:
            topic_query = "technology" if category == "technology" else "business" if category == "business" else "top stories"
            rss_url = f"https://news.google.com/rss/search?q={topic_query}&hl=en-IN&gl=IN&ceid=IN:en"
            resp = requests.get(rss_url, timeout=8, headers={"User-Agent": "Mozilla/5.0"})
            if resp.status_code == 200:
                root = ET.fromstring(resp.content)
                items = root.findall(".//item")
                if items:
                    lines = [f"📰 Top {category.title()} Headlines (Live):"]
                    for it in items[:limit]:
                        title_el = it.find("title")
                        if title_el is not None and title_el.text:
                            # Clean Google News suffix "- Source Name"
                            t_text = title_el.text.strip()
                            lines.append(f"• {t_text}")
                    return ToolResult(success=True, data="\n".join(lines))
        except Exception as e:
            logger.error(f"RSS news fetch failed: {e}")

        return ToolResult(success=False, error="Unable to fetch live news at this time.")
