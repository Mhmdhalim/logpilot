"""Terminal formatting and machine-readable exports for analytics results."""

import csv
import json
from pathlib import Path
from typing import TextIO

from logpilot.analyzer import AnalysisResult


def report_dict(result: AnalysisResult) -> dict:
    """Represent analysis results in a stable, JSON-friendly schema."""
    return {
        "summary": {
            "total_requests": result.total_requests,
            "error_requests": result.error_requests,
            "error_rate_percent": result.error_rate,
            "average_latency_ms": result.average_latency_ms,
            "maximum_latency_ms": result.maximum_latency_ms,
            "unique_endpoints": len(result.endpoint_counts),
        },
        "status_categories": result.status_categories,
        "status_codes": {str(k): v for k, v in result.status_codes.items()},
        "endpoints": [
            {"path": path, "requests": count}
            for path, count in result.top_endpoints(
                max(1, len(result.endpoint_counts))
            )
        ],
    }


def format_summary(result: AnalysisResult) -> str:
    categories = "  ".join(
        f"{category}: {count}"
        for category, count in result.status_categories.items()
    )
    return "\n".join(
        [
            "LogPilot — HTTP log summary",
            f"Total requests:       {result.total_requests}",
            f"Error requests:       {result.error_requests}",
            f"Error rate:           {result.error_rate:.2f}%",
            f"Average latency:      {result.average_latency_ms:.2f} ms",
            f"Maximum latency:      {result.maximum_latency_ms:.2f} ms",
            f"Unique endpoints:     {len(result.endpoint_counts)}",
            f"Status categories:    {categories}",
        ]
    )


def format_top(result: AnalysisResult, limit: int) -> str:
    lines = ["Requests  Endpoint"]
    lines.extend(f"{count:8d}  {path}" for path, count in result.top_endpoints(limit))
    return "\n".join(lines)


def write_report(result: AnalysisResult, destination: str | Path, fmt: str) -> None:
    """Write a JSON report or one normalized CSV table to destination."""
    path = Path(destination)
    if fmt == "json":
        path.write_text(
            json.dumps(report_dict(result), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    elif fmt == "csv":
        with path.open("w", newline="", encoding="utf-8") as handle:
            _write_csv(result, handle)
    else:
        raise ValueError(f"Unsupported report format: {fmt}")


def _write_csv(result: AnalysisResult, handle: TextIO) -> None:
    writer = csv.writer(handle)
    writer.writerow(["section", "name", "value"])
    for name, value in report_dict(result)["summary"].items():
        writer.writerow(["summary", name, value])
    for category, count in result.status_categories.items():
        writer.writerow(["status_category", category, count])
    for status, count in result.status_codes.items():
        writer.writerow(["status_code", status, count])
    for path, count in result.top_endpoints(max(1, len(result.endpoint_counts))):
        writer.writerow(["endpoint", path, count])
