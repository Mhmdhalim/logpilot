from dataclasses import dataclass
from datatime import datetime
from enum import Enum

class Method(Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    
@dataclass
class LogEntry:
    timestamp: datetime
    method: Method
    path: str
    status: int
    duration_ms: float
