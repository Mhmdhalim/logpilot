# Architecture

```text
JSONL file ──> reader.read_logs() ──> parser.parse_log_entry()
                                          │
                                          v
                                     LogEntry objects
                                          │
                                          v
                                  analyzer.analyze_logs()
                                          │
                                          v
                                    AnalysisResult
                                          │
                           ┌──────────────┴─────────────┐
                           v                            v
                      CLI terminal                  reporter export
                                                   (JSON / CSV)
```

- **models.py**: immutable dataclass for validated HTTP records.
- **parser.py**: JSON parsing and field validation. Raises `ValueError` for bad records.
- **reader.py**: lazily opens UTF-8 JSONL files and yields validated records. Empty lines are skipped. Stops on the first invalid record with a file-and-line-number error.
- **analyzer.py**: computes aggregations in one pass over any iterable; no file I/O and no stored individual log entries.
- **reporter.py**: string formatting plus JSON/CSV serialization.
- **cli.py**: argparse-based command dispatch, exit codes, user-facing errors.

## Complexity

Let **N** be the number of valid records, **U** the number of distinct paths, and **S** the total number of distinct HTTP status codes (at most 500).

- Streaming reader: O(N) processing time; auxiliary memory O(L), where L is the length of the largest individual log line.
- Analyzer: O(N) expected aggregation time, O(U + S) auxiliary memory; no per-request storage.
- Ranking top endpoints: O(U log U) sorting time and O(U) additional memory.
- Report export: O(U + S) output representation/rows.

Latency average is exact up to floating-point rounding. A globally exact p95 needs stored samples or a specialized data structure; p95 is intentionally not claimed here.

## Error policy

Invalid data fails fast rather than silently distorting statistics. The CLI returns nonzero exit status (2) for read/parse/export errors. For `errors --limit N` the generator is closed on early exit via `contextlib.closing`.
