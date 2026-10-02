"""
Web Search & Knowledge Retrieval Tool
Fetches factual summaries from Wikipedia and search sources.
"""
from typing import Dict, Any
import urllib.parse
import requests
from tools.base import BaseTool, ToolResult
from security.capabilities import Capability, RiskTier

class WebSearchTool(BaseTool):
    @property
    def id(self) -> str:
        return "web_search"

    @property
    def name(self) -> str:
        return "Web & Knowledge Search"

    @property
    def description(self) -> str:
        return "Search the web and encyclopedia repositories for factual knowledge and summaries."

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "required": ["query"],
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query to look up"
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
        query = params.get("query", "").strip()
        if not query:
            return ToolResult(success=False, error="Empty query provided.")

        # Query Wikipedia REST API for reliable factual encyclopedic knowledge
        try:
            encoded = urllib.parse.quote(query)
            url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{encoded}"
            headers = {"User-Agent": "JarvisAssistant/5.1 (AI System Engineering)"}
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                extract = data.get("extract")
                title = data.get("title")
                if extract:
                    return ToolResult(success=True, data={
                        "title": title,
                        "summary": extract,
                        "source": data.get("content_urls", {}).get("desktop", {}).get("page", "Wikipedia")
                    })
        except Exception:
            pass

        # Fallback to DuckDuckGo instant answer
        try:
            url = f"https://api.duckduckgo.com/?q={urllib.parse.quote(query)}&format=json&no_html=1&skip_disambig=1"
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                abstract = data.get("AbstractText")
                if abstract:
                    return ToolResult(success=True, data={
                        "title": data.get("Heading", query),
                        "summary": abstract,
                        "source": data.get("AbstractURL", "DuckDuckGo")
                    })
        except Exception:
            pass

        return ToolResult(success=True, data={
            "query": query,
            "status": "Search executed; consult reasoning engine for synthesis."
        })
