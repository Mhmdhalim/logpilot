"""One-pass statistics for validated HTTP request logs."""

from collections import Counter
from dataclasses import dataclass
from typing import Iterable

from logpilot.models import LogEntry

CATEGORIES = ("1xx", "2xx", "3xx", "4xx", "5xx")


@dataclass(frozen=True)
class AnalysisResult:
    total_requests: int
    error_requests: int
    error_rate: float
    average_latency_ms: float
    maximum_latency_ms: float
    status_categories: dict[str, int]
    status_codes: dict[int, int]
    endpoint_counts: dict[str, int]

    def top_endpoints(self, limit: int = 5) -> list[tuple[str, int]]:
        """Return (path, requests) ordered by descending count, then path."""
        if limit < 1:
            raise ValueError("limit must be a positive integer")
        return sorted(
            self.endpoint_counts.items(), key=lambda item: (-item[1], item[0])
        )[:limit]


def analyze_logs(entries: Iterable[LogEntry]) -> AnalysisResult:
    """Analyze each entry once; memory is O(unique endpoints + status codes)."""
    total = 0
    errors = 0
    latency_sum = 0.0
    max_latency = 0.0
    categories = dict.fromkeys(CATEGORIES, 0)
    status_codes: Counter[int] = Counter()
    endpoints: Counter[str] = Counter()

    for entry in entries:
        total += 1
        categories[f"{entry.status // 100}xx"] += 1
        status_codes[entry.status] += 1
        endpoints[entry.path] += 1
        latency_sum += entry.duration_ms
        max_latency = max(max_latency, entry.duration_ms)
        if entry.status >= 400:
            errors += 1

    return AnalysisResult(
        total_requests=total,
        error_requests=errors,
        error_rate=(errors / total * 100) if total else 0.0,
        average_latency_ms=(latency_sum / total) if total else 0.0,
        maximum_latency_ms=max_latency,
        status_categories=categories,
        status_codes=dict(sorted(status_codes.items())),
        endpoint_counts=dict(endpoints),
    )
