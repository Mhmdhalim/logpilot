import json
from models import LogEntry, Method
from datetime import datetime, timezone

def parse_log_entry(row: str) -> LogEntry:
    try:
        data = json.loads(row)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON format: {e.msg}")
    
    if not isinstance(data, dict):
        raise TypeError(f"Parsed JSON is not a dictionary; expected a {type(data).__name__} with log entry fields.")
    
    required_fields = ['timestamp', 'method', 'url', 'status_code', 'response_time_ms']
    for field in required_fields:
        if field not in data:
            raise KeyError(f"Missing required field: '{field}'")
    try:
        method = Method(data['method'])
    except ValueError:
        raise ValueError(f"Invalid HTTP method: '{data['method']}'")
    if not (100 <= data['status'] <= 599):
        raise ValueError(f"Invalid status code: '{data['status']}'")
    
    if type(data['duration_ms']) is not int:
        raise TypeError(f"Invalid duration format: '{data['duration_ms']}'")
    if data['duration_ms'] < 0:
        raise ValueError(f"Duration must be non-negative: '{data['duration_ms']}'")
    
    if not isinstance(data['path'], str) or not data['path']:
        raise TypeError(f"Invalid path format: '{data['path']}'")
    
    try:
        ts = datetime.fromisoformat(data['timestamp'].replace("Z", "+00:00"))
    except ValueError:
        raise ValueError(f"Invalid timestamp format: '{data['timestamp']}'")
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)    
    else:
        ts = ts.astimezone(timezone.utc)
        
    return LogEntry(
        timestamp=ts,
        method=method,
        path=data['path'],
        status=data['status'],
        duration_ms=data['duration_ms'],
    )
