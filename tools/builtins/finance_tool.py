"""
J.A.R.V.I.S. Finance & Market Intelligence Tool
Fetches real-time stock quotes, indices, and currency conversions.
Zero API key required via public financial market data endpoints.
"""
import requests
import logging
from typing import Dict, Any

from tools.base import BaseTool, ToolResult
from security.capabilities import Capability, RiskTier

logger = logging.getLogger("jarvis.tools.finance")


class FinanceTool(BaseTool):
    @property
    def id(self) -> str:
        return "finance"

    @property
    def name(self) -> str:
        return "Market & Stock Quotes"

    @property
    def description(self) -> str:
        return "Retrieve real-time market data, stock prices, day change, and currency exchange rates for any ticker (e.g. AAPL, NVDA, TSLA, MSFT, BTC-USD, RELIANCE.NS)."

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "Stock symbol or ticker (e.g. 'AAPL', 'NVDA', 'TSLA', 'BTC-USD', 'INFY.NS')."
                }
            },
            "required": ["symbol"]
        }

    @property
    def required_capability(self) -> Capability:
        return Capability.CHAT

    @property
    def risk_tier(self) -> RiskTier:
        return RiskTier.LOW

    def execute(self, params: Dict[str, Any]) -> ToolResult:
        sym = params.get("symbol", "").strip().upper()
        if not sym:
            return ToolResult(success=False, error="Stock symbol/ticker is required.")

        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?interval=1d&range=1d"

        try:
            resp = requests.get(url, headers=headers, timeout=8)
            if resp.status_code != 200:
                return ToolResult(success=False, error=f"Could not retrieve ticker '{sym}'. Verify the symbol.")

            d = resp.json()
            result = d.get("chart", {}).get("result", [{}])[0]
            meta = result.get("meta", {})
            if not meta:
                return ToolResult(success=False, error=f"No financial data found for ticker '{sym}'.")

            price = meta.get("regularMarketPrice")
            prev_close = meta.get("chartPreviousClose") or meta.get("previousClose")
            currency = meta.get("currency", "USD")
            exchange = meta.get("exchangeName", "")
            instrument = meta.get("instrumentType", "EQUITY")

            change = round(price - prev_close, 2) if (price and prev_close) else 0.0
            pct_change = round((change / prev_close) * 100.0, 2) if prev_close else 0.0
            direction = "📈 +" if change >= 0 else "📉 "

            high = meta.get("regularMarketDayHigh", "?")
            low = meta.get("regularMarketDayLow", "?")

            summary = (
                f"💹 {sym} ({exchange})\n"
                f"• Current Price: {price} {currency}\n"
                f"• Change:        {direction}{change} ({pct_change}%)\n"
                f"• Previous Close:{prev_close} {currency}\n"
                f"• Day High/Low:  {high} / {low}\n"
                f"• Asset Type:    {instrument}"
            )

            return ToolResult(
                success=True,
                data=summary,
                metadata={
                    "symbol": sym,
                    "price": price,
                    "change": change,
                    "pct_change": pct_change,
                    "currency": currency
                }
            )

        except Exception as e:
            logger.error(f"Finance tool error for {sym}: {e}")
            return ToolResult(success=False, error=f"Market data lookup failed for '{sym}': {str(e)}")
