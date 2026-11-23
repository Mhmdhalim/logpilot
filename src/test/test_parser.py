from logpilot.parser import parse_log_entry

row = (
    '{"timestamp": "2026-11-18T10:00:00Z", '
    '"method": "GET", '
    '"path": "/api/users", '
    '"status": 200, '
    '"duration_ms": 45.5}'
)

entry = parse_log_entry(row)

print(entry)
print(entry.status)
print(entry.duration_ms)