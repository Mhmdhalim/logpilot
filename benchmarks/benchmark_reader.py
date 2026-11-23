"""Reproducible local streaming benchmark; not a guaranteed performance claim."""

import argparse
import json
import tempfile
import time
import tracemalloc
from pathlib import Path

from logpilot.analyzer import analyze_logs
from logpilot.reader import read_logs


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark LogPilot streaming analytics")
    parser.add_argument("--rows", type=int, default=100_000)
    args = parser.parse_args()
    if args.rows <= 0:
        parser.error("--rows must be positive")

    record = {
        "timestamp": "2026-11-18T10:00:00Z", "method": "GET",
        "path": "/api/users", "status": 200, "duration_ms": 45.5,
    }
    line = json.dumps(record) + "\n"
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "sample.jsonl"
        with path.open("w", encoding="utf-8") as handle:
            for _ in range(args.rows):
                handle.write(line)
        tracemalloc.start()
        start = time.perf_counter()
        result = analyze_logs(read_logs(path))
        elapsed = time.perf_counter() - start
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
    print(f"Requests analyzed: {result.total_requests:,}")
    print(f"Elapsed: {elapsed:.3f} seconds")
    print(f"Python peak allocated memory: {peak / (1024**2):.2f} MiB")
    print("Note: tracemalloc measures Python allocations, not entire process RSS.")


if __name__ == "__main__":
    main()
