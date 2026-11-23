# LogPilot

**A lightweight Python CLI for streaming HTTP JSONL logs, detecting errors, and reporting request performance.**

LogPilot reads one record at a time rather than loading an entire log file. It combines strict parsing, useful request-level statistics, JSON/CSV export, and automated tests. The runtime uses only the Python standard library.

## Features

- Validate structured HTTP request logs with informative file/line-number errors.
- Count requests by status category and status code, including 4xx/5xx error rates.
- Calculate average and maximum request latency.
- Rank endpoints by request count (ties sorted alphabetically).
- Filter 4xx/5xx errors by exact HTTP status, and limit displayed matches.
- Export full analytics to JSON or CSV.
- Stream input via generators and aggregate in a single pass.

## Requirements and installation

Python **3.11+**.

```bash
python -m venv .venv
# PowerShell on Windows: .\.venv\Scripts\Activate.ps1
# macOS / Linux: source .venv/bin/activate
python -m pip install -e .
```

Development setup:

```bash
python -m pip install -e '.[dev]'
python -m pytest -v
python -m ruff check .
```

## Quick start

```bash
logpilot analyze examples/server.jsonl
logpilot analyze examples/server.jsonl --json
logpilot errors examples/server.jsonl --status 500 --limit 10
logpilot top examples/server.jsonl --limit 5
logpilot report examples/server.jsonl --output report.json
logpilot report examples/server.jsonl --output report.csv
```

Alternatively run `python -m logpilot analyze examples/server.jsonl`.

For the provided four-record example, the summary reports **4 requests**, **50% error rate**, and **100 ms average latency**.

## Input format

Each nonblank line must be a complete JSON object:

```json
{"timestamp":"2026-11-18T10:00:00Z","method":"GET","path":"/api/users","status":200,"duration_ms":20}
```

Required: timezone-aware ISO 8601 `timestamp`, nonempty `method`, `path` starting with `/`, integer `status` from 100–599, and nonnegative finite numeric `duration_ms`. Blank lines are ignored. Status codes 400–599 count as errors. Invalid lines stop processing and report the file and physical line number; they are not silently skipped.

## Commands

| Command | Purpose |
| --- | --- |
| `analyze FILE [--json]` | Show overall statistics |
| `errors FILE [--status CODE] [--limit N]` | Print up to N matching 4xx/5xx entries |
| `top FILE [--limit N]` | Show most-requested endpoints |
| `report FILE --output FILE [--format json\|csv]` | Save complete JSON/CSV analytics |
| `--help`, `--version` | Command usage and version |

`--limit` must be positive. Invalid input/files generate a nonzero exit code and a readable error on stderr. JSON export includes a summary, status categories/codes, and endpoints. CSV export uses columns `section,name,value` for easy inspection in spreadsheet tools.

## Design, testing, and performance

See [architecture](docs/architecture.md) for pipeline, error behavior, and complexity. Streaming aggregation takes **O(N)** expected time and **O(U + S)** memory, where U is the number of unique endpoints and S the number of HTTP statuses; memory does not grow with each individual request.

Unit/integration tests use pytest, including malformed inputs, generator consumption, errors, CLI output, and export. GitHub Actions tests Python 3.11–3.13 and runs Ruff. To measure locally:

```bash
python benchmarks/benchmark_reader.py --rows 100000
```

Benchmark output depends on the machine and should not be treated as a general performance guarantee.

## Scope and limitations

Version 1.0 supports **structured JSONL HTTP logs**, not raw Nginx/Apache access log syntax. Latency p95, time-window breakdowns, alerting, and anomaly detection are future enhancements. CLI operations fail fast on malformed records. Avoid using real production logs containing personal data in a public repository.

## License

MIT — see [LICENSE](LICENSE).
