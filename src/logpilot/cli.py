"""User-facing CLI built on Python's standard-library argparse."""

import argparse
import json
import sys
from contextlib import closing
from pathlib import Path
from typing import Sequence

from logpilot.analyzer import analyze_logs
from logpilot.reader import read_logs
from logpilot.reporter import format_summary, format_top, report_dict, write_report


def positive_int(text: str) -> int:
    try:
        value = int(text)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a positive integer") from exc
    if value < 1:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return value


def error_status(text: str) -> int:
    try:
        value = int(text)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a 4xx or 5xx HTTP status") from exc
    if not 400 <= value <= 599:
        raise argparse.ArgumentTypeError("must be a 4xx or 5xx HTTP status")
    return value


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="logpilot", description="Analyze JSONL HTTP logs without loading them into RAM."
    )
    parser.add_argument("--version", action="version", version="%(prog)s 1.0.0")
    commands = parser.add_subparsers(dest="command", required=True)

    analyze = commands.add_parser("analyze", help="Show a summary of HTTP log statistics")
    analyze.add_argument("file", type=Path)
    analyze.add_argument("--json", action="store_true", help="Output structured JSON")

    errors = commands.add_parser("errors", help="Print 4xx and 5xx entries")
    errors.add_argument("file", type=Path)
    errors.add_argument("--status", type=error_status, help="Filter by exact 4xx/5xx code")
    errors.add_argument("--limit", type=positive_int, default=20)

    top = commands.add_parser("top", help="Show most frequently requested endpoints")
    top.add_argument("file", type=Path)
    top.add_argument("--limit", type=positive_int, default=5)

    report = commands.add_parser("report", help="Export a JSON or CSV report")
    report.add_argument("file", type=Path)
    report.add_argument("--output", required=True, type=Path)
    report.add_argument("--format", choices=("json", "csv"), help="Defaults to output extension")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "errors":
            printed = 0
            with closing(read_logs(args.file)) as entries:
                for entry in entries:
                    if entry.status < 400 or (
                        args.status is not None and entry.status != args.status
                    ):
                        continue
                    print(
                        f"{entry.timestamp.isoformat()} "
                        f"{entry.method} {entry.path} "
                        f"{entry.status} {entry.duration_ms:.2f}ms"
                    )
                    printed += 1
                    if printed >= args.limit:
                        break
            if printed == 0:
                print("No matching errors.")
            return 0

        result = analyze_logs(read_logs(args.file))
        if args.command == "analyze":
            if args.json:
                print(json.dumps(report_dict(result), indent=2, ensure_ascii=False))
            else:
                print(format_summary(result))
        elif args.command == "top":
            print(format_top(result, args.limit))
        elif args.command == "report":
            fmt = args.format or args.output.suffix.lower().lstrip(".")
            if fmt not in {"json", "csv"}:
                raise ValueError("Output must use .json or .csv, or specify --format")
            write_report(result, args.output, fmt)
            print(f"Report saved to {args.output}")
        return 0
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"logpilot: error: {exc}", file=sys.stderr)
        return 2
