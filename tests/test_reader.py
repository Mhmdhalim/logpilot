
import json

import pytest

from logpilot.models import LogEntry
from logpilot.reader import read_logs


VALID_LOG = {
    "timestamp": "2026-11-18T10:00:00Z",
    "method": "GET",
    "path": "/api/users",
    "status": 200,
    "duration_ms": 45.5,
}


def test_read_valid_logs(tmp_path):
    file = tmp_path / "server.jsonl"

    logs = [
        VALID_LOG,
        {**VALID_LOG, "status": 500},
    ]

    file.write_text(
        "\n".join(json.dumps(log) for log in logs),
        encoding="utf-8",
    )

    entries = list(read_logs(file))

    assert len(entries) == 2
    assert all(isinstance(e, LogEntry) for e in entries)
    assert entries[0].status == 200
    assert entries[1].status == 500


def test_empty_file(tmp_path):
    file = tmp_path / "empty.jsonl"
    file.write_text("", encoding="utf-8")

    assert list(read_logs(file)) == []


def test_skip_blank_lines(tmp_path):
    file = tmp_path / "server.jsonl"

    file.write_text(
        "\n" + json.dumps(VALID_LOG) + "\n   \n",
        encoding="utf-8",
    )

    entries = list(read_logs(file))

    assert len(entries) == 1


def test_invalid_json_line_number(tmp_path):
    file = tmp_path / "server.jsonl"

    file.write_text(
        json.dumps(VALID_LOG) + "\n\n{invalid json}",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="line 3"):
        list(read_logs(file))


def test_invalid_log_fields(tmp_path):
    file = tmp_path / "server.jsonl"

    invalid = {**VALID_LOG, "status": 700}
    file.write_text(json.dumps(invalid), encoding="utf-8")

    with pytest.raises(ValueError, match="line 1"):
        list(read_logs(file))


def test_file_not_found(tmp_path):
    file = tmp_path / "missing.jsonl"

    with pytest.raises(FileNotFoundError):
        list(read_logs(file))


def test_generator_reads_incrementally(tmp_path):
    file = tmp_path / "server.jsonl"

    file.write_text(
        json.dumps(VALID_LOG) + "\n"
        + json.dumps({**VALID_LOG, "status": 404}),
        encoding="utf-8",
    )

    generator = read_logs(file)

    assert next(generator).status == 200
    assert next(generator).status == 404

    with pytest.raises(StopIteration):
        next(generator)
