from datetime import datetime, timezone

import pytest

from logpilot.analyzer import analyze_logs
from logpilot.models import LogEntry


def entry(path: str, status: int, duration: float) -> LogEntry:
    return LogEntry(datetime(2026, 11, 18, tzinfo=timezone.utc), "GET", path,
                    status, duration)


def test_aggregate_counts_rates_and_top_order():
    logs = (
        log for log in [
            entry("/api/users", 200, 20),
            entry("/api/login", 500, 300),
            entry("/api/users", 404, 40),
            entry("/api/users", 200, 40),
        ]
    )
    result = analyze_logs(logs)
    assert result.total_requests == 4
    assert result.error_requests == 2
    assert result.error_rate == 50.0
    assert result.average_latency_ms == 100.0
    assert result.maximum_latency_ms == 300
    assert result.status_categories == {"1xx": 0, "2xx": 2, "3xx": 0, "4xx": 1, "5xx": 1}
    assert result.status_codes == {200: 2, 404: 1, 500: 1}
    assert result.top_endpoints() == [("/api/users", 3), ("/api/login", 1)]


def test_empty_input():
    result = analyze_logs(iter([]))
    assert result.total_requests == 0
    assert result.error_rate == 0.0
    assert result.average_latency_ms == 0.0
    assert result.maximum_latency_ms == 0.0
    assert result.top_endpoints() == []
    assert all(value == 0 for value in result.status_categories.values())


@pytest.mark.parametrize("statuses,expected", [([200, 302], 0.0), ([404, 500], 100.0)])
def test_error_rate_extremes(statuses, expected):
    result = analyze_logs(entry("/", s, 2) for s in statuses)
    assert result.error_rate == expected


def test_informational_and_redirect_not_errors():
    result = analyze_logs([entry("/a", 101, 1), entry("/b", 301, 2)])
    assert result.status_categories["1xx"] == 1
    assert result.status_categories["3xx"] == 1
    assert result.error_requests == 0


def test_tied_endpoints_sort_alphabetically():
    result = analyze_logs(entry(path, 200, 1) for path in ["/z", "/a", "/z", "/a"])
    assert result.top_endpoints(1) == [("/a", 2)]
    assert result.top_endpoints(2) == [("/a", 2), ("/z", 2)]


def test_fractional_duration():
    result = analyze_logs([entry("/a", 200, 0.1), entry("/a", 200, 0.2)])
    assert result.average_latency_ms == pytest.approx(0.15)


def test_limit_must_be_positive():
    with pytest.raises(ValueError, match="positive"):
        analyze_logs([]).top_endpoints(0)


def test_iterator_consumed_once():
    class Once:
        def __init__(self):
            self.calls = 0

        def __iter__(self):
            self.calls += 1
            if self.calls > 1:
                raise RuntimeError("second iteration")
            yield entry("/ok", 200, 10)

    source = Once()
    assert analyze_logs(source).total_requests == 1
    assert source.calls == 1
