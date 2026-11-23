import csv
import json
import subprocess
import sys

import pytest

from logpilot.cli import main


@pytest.fixture
def logfile(tmp_path):
    path = tmp_path / "sample.jsonl"
    values = [
        {"timestamp": "2026-11-18T10:00:00Z", "method": "GET", "path": "/users",
         "status": 200, "duration_ms": 20},
        {"timestamp": "2026-11-18T10:00:01Z", "method": "POST", "path": "/login",
         "status": 500, "duration_ms": 100},
        {"timestamp": "2026-11-18T10:00:02Z", "method": "GET", "path": "/users",
         "status": 404, "duration_ms": 30},
    ]
    path.write_text("\n".join(json.dumps(v) for v in values) + "\n", encoding="utf-8")
    return path


def test_analyze_human_output(logfile, capsys):
    assert main(["analyze", str(logfile)]) == 0
    captured = capsys.readouterr()
    assert "Total requests:       3" in captured.out
    assert "66.67%" in captured.out


def test_analyze_json(logfile, capsys):
    assert main(["analyze", str(logfile), "--json"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["summary"]["total_requests"] == 3
    assert data["status_categories"]["5xx"] == 1


def test_errors_filter_and_limit(logfile, capsys):
    assert main(["errors", str(logfile), "--status", "500", "--limit", "1"]) == 0
    output = capsys.readouterr().out
    assert "500" in output and "/login" in output
    assert "404" not in output


def test_no_matching_errors(logfile, capsys):
    assert main(["errors", str(logfile), "--status", "501"]) == 0
    assert "No matching errors" in capsys.readouterr().out


def test_top(logfile, capsys):
    assert main(["top", str(logfile), "--limit", "1"]) == 0
    output = capsys.readouterr().out
    assert "/users" in output
    assert "/login" not in output


def test_export_json(logfile, tmp_path, capsys):
    dest = tmp_path / "report.json"
    assert main(["report", str(logfile), "--output", str(dest)]) == 0
    saved = json.loads(dest.read_text(encoding="utf-8"))
    assert saved["summary"]["error_requests"] == 2
    assert saved["endpoints"][0] == {"path": "/users", "requests": 2}


def test_export_csv(logfile, tmp_path):
    dest = tmp_path / "report.csv"
    assert main(["report", str(logfile), "--output", str(dest)]) == 0
    with dest.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert {"section": "endpoint", "name": "/users", "value": "2"} in rows


def test_missing_file_returns_exit_code_2(tmp_path, capsys):
    assert main(["analyze", str(tmp_path / "missing.jsonl")]) == 2
    assert "logpilot: error:" in capsys.readouterr().err


def test_malformed_line_returns_exit_code_2(tmp_path, capsys):
    path = tmp_path / "bad.jsonl"
    path.write_text("not JSON\n", encoding="utf-8")
    assert main(["analyze", str(path)]) == 2
    assert "line 1" in capsys.readouterr().err


def test_invalid_output_format(logfile, tmp_path, capsys):
    assert main(["report", str(logfile), "--output", str(tmp_path / "x.txt")]) == 2
    assert "Output must use" in capsys.readouterr().err


def test_reject_zero_limit(logfile):
    with pytest.raises(SystemExit) as error:
        main(["top", str(logfile), "--limit", "0"])
    assert error.value.code == 2


def test_module_entry_point(logfile):
    result = subprocess.run(
        [sys.executable, "-m", "logpilot", "analyze", str(logfile)],
        capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0
    assert "Total requests:       3" in result.stdout
