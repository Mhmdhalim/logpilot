import json
import math
from datetime import datetime, timezone
from logpilot.models import LogEntry


def parse_log_entry(row: str) -> LogEntry:
    try:
        data = json.loads(row)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON format: {e.msg}") from e

    if not isinstance(data, dict):
        raise ValueError("Log entry must be a JSON object")

    required_fields = [
        "timestamp",
        "method",
        "path",
        "status",
        "duration_ms",
    ]

    for field in required_fields:
        if field not in data:
            raise ValueError(f"Missing required field: '{field}'")

    method = data["method"]
    if not isinstance(method, str) or not method.strip():
        raise ValueError("Invalid HTTP method")

    path = data["path"]
    if not isinstance(path, str) or not path.startswith("/"):
        raise ValueError("Invalid request path")

    status = data["status"]
    if type(status) is not int or not (100 <= status <= 599):
        raise ValueError(f"Invalid HTTP status: {status}")

    duration = data["duration_ms"]

    if type(duration) not in (int, float):
        raise ValueError("Duration must be a number")

    if duration < 0:
        raise ValueError("Duration must be non-negative")

    try:
        duration = float(duration)
    except OverflowError as e:
        raise ValueError("Duration is too large") from e

    if not math.isfinite(duration):
        raise ValueError("Duration must be finite")

    timestamp = data["timestamp"]

    if not isinstance(timestamp, str):
        raise ValueError("Timestamp must be a string")

    try:
        ts = datetime.fromisoformat(
            timestamp.replace("Z", "+00:00")
        )
    except ValueError as e:
        raise ValueError(
            f"Invalid timestamp: {timestamp}"
        ) from e

    if ts.tzinfo is None or ts.utcoffset() is None:
        raise ValueError("Timestamp must contain timezone information")

    ts = ts.astimezone(timezone.utc)

    return LogEntry(
        timestamp=ts,
        method=method,
        path=path,
        status=status,
        duration_ms=duration,
    )
