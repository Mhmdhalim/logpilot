import json

import pytest

from datetime import datetime, timezone

from logpilot.models import LogEntry
from logpilot.parser import parse_log_entry


VALID_LOG = {
    "timestamp": "2026-11-18T10:00:00Z",
    "method": "GET",
    "path": "/api/users",
    "status": 200,
    "duration_ms": 45.5,
}


def test_valid_log_entry():
    entry = parse_log_entry(json.dumps(VALID_LOG))

    assert isinstance(entry, LogEntry)
    assert entry.method == "GET"
    assert entry.path == "/api/users"
    assert entry.status == 200
    assert entry.duration_ms == 45.5
    assert entry.timestamp == datetime(
        2026, 11, 18, 10, 0, tzinfo=timezone.utc
    )


def test_invalid_json():
    with pytest.raises(ValueError):
        parse_log_entry("{invalid json}")


def test_missing_required_field():
    data = VALID_LOG.copy()
    del data["status"]

    with pytest.raises(ValueError, match="Missing required field"):
        parse_log_entry(json.dumps(data))


@pytest.mark.parametrize("status", [
    99,
    700,
    True,
    "200",
])
def test_invalid_status(status):
    data = {**VALID_LOG, "status": status}

    with pytest.raises(ValueError):
        parse_log_entry(json.dumps(data))


@pytest.mark.parametrize("duration", [
    -10,
    "45",
    True,
    float("nan"),
    float("inf"),
])
def test_invalid_duration(duration):
    data = {**VALID_LOG, "duration_ms": duration}

    with pytest.raises(ValueError):
        parse_log_entry(json.dumps(data))


@pytest.mark.parametrize("timestamp", [
    "2026-11-18T10:00:00",
    "invalid-date",
    None,
])
def test_invalid_timestamp(timestamp):
    data = {**VALID_LOG, "timestamp": timestamp}

    with pytest.raises(ValueError):
        parse_log_entry(json.dumps(data))


def test_invalid_path():
    data = {**VALID_LOG, "path": "api/users"}

    with pytest.raises(ValueError):
        parse_log_entry(json.dumps(data))


def test_invalid_top_level_json():
    with pytest.raises(ValueError):
        parse_log_entry("[1, 2, 3]")
