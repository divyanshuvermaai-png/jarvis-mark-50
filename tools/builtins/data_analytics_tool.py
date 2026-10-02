"""
J.A.R.V.I.S. Data & CSV Analytics Tool
Performs automated statistical profiling and analysis of tabular datasets (CSV/TSV/JSON).
"""
import os
import logging
from typing import Dict, Any

from tools.base import BaseTool, ToolResult
from security.capabilities import Capability, RiskTier
from security.action_validator import validate_file_path

logger = logging.getLogger("jarvis.tools.data_analytics")


class DataAnalyticsTool(BaseTool):
    @property
    def id(self) -> str:
        return "data_analytics"

    @property
    def name(self) -> str:
        return "Dataset Profiler & Analytics"

    @property
    def description(self) -> str:
        return "Analyze a CSV, TSV, or JSON data file. Computes shape, column data types, missing value percentages, and statistical summaries."

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path to the data file to analyze (e.g. 'data/sales.csv', '~/Downloads/metrics.csv')."
                },
                "rows_preview": {
                    "type": "integer",
                    "description": "Number of sample preview rows to show (defaults to 3)."
                }
            },
            "required": ["file_path"]
        }

    @property
    def required_capability(self) -> Capability:
        return Capability.FILE_READ

    @property
    def risk_tier(self) -> RiskTier:
        return RiskTier.LOW

    def execute(self, params: Dict[str, Any]) -> ToolResult:
        file_path = params.get("file_path", "").strip()
        preview_n = min(10, max(1, int(params.get("rows_preview", 3))))

        is_valid_path, target_path, err = validate_file_path(file_path)
        if not is_valid_path:
            return ToolResult(success=False, error=f"Access denied to file: {err or 'Path is outside allowed directories.'}")

        expanded = target_path
        if not os.path.exists(expanded):
            return ToolResult(success=False, error=f"Data file '{file_path}' does not exist.")

        try:
            import pandas as pd
            if expanded.endswith(".tsv") or "\t" in expanded:
                df = pd.read_csv(expanded, sep="\t")
            elif expanded.endswith(".json"):
                df = pd.read_json(expanded)
            else:
                df = pd.read_csv(expanded)

            rows, cols = df.shape
            col_types = {col: str(dtype) for col, dtype in df.dtypes.items()}
            nulls = df.isnull().sum().to_dict()

            summary_lines = [
                f"📊 Data Profile for: {os.path.basename(expanded)}",
                f"• Dimensions: {rows:,} rows × {cols:,} columns",
                f"• Memory Usage: {round(df.memory_usage(deep=True).sum() / (1024 * 1024), 2)} MB",
                "",
                "📋 Columns & Missing Values:"
            ]

            for col, dtype in list(col_types.items())[:15]:
                null_pct = round((nulls.get(col, 0) / max(1, rows)) * 100.0, 1)
                summary_lines.append(f"  • {col} ({dtype}): {nulls.get(col, 0)} nulls ({null_pct}%)")

            # Numeric statistics
            numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
            if numeric_cols:
                summary_lines.append("\n📈 Numerical Distributions:")
                desc = df[numeric_cols[:6]].describe().round(2)
                for col in numeric_cols[:6]:
                    c_min = desc.loc["min", col]
                    c_max = desc.loc["max", col]
                    c_mean = desc.loc["mean", col]
                    c_median = desc.loc["50%", col]
                    summary_lines.append(f"  • {col}: mean={c_mean}, median={c_median}, min={c_min}, max={c_max}")

            # Preview
            summary_lines.append(f"\n🔍 First {preview_n} Rows Preview:")
            preview_str = df.head(preview_n).to_string()
            summary_lines.append(preview_str)

            return ToolResult(
                success=True,
                data="\n".join(summary_lines),
                metadata={
                    "rows": rows,
                    "columns": cols,
                    "columns_list": list(df.columns)
                }
            )

        except Exception as e:
            logger.error(f"Data analysis failed on {file_path}: {e}")
            return ToolResult(success=False, error=f"Data analysis error: {str(e)}")
