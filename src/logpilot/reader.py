from pathlib import Path
from typing import Iterator

from logpilot.models import LogEntry
from logpilot.parser import parse_log_entry


def read_logs(file_path: str | Path) -> Iterator[LogEntry]:
    with open(file_path, "r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            if not line.strip():
                continue

            try:
                entry = parse_log_entry(line)
            except ValueError as e:
                raise ValueError(
                    f"Invalid log entry in {file_path} "
                    f"at line {line_number}: {e}"
                ) from e

            yield entry