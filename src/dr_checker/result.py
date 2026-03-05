from dataclasses import dataclass
from typing import Optional, Dict, Any


class Status:
    PASS = "PASS"
    FAIL = "FAIL"
    SKIP = "SKIP"
    WARN = "WARN"
    ERROR = "ERROR"


class Severity:
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    CRITICAL = "CRITICAL"


@dataclass
class CheckResult:
    """
    A single check outcome.

    status:
      PASS  - check succeeded
      FAIL  - check failed (readiness problem)
      SKIP  - check not applicable (disabled/dep not met)
      WARN  - non-blocking issue
      ERROR - unexpected exception during execution
    """
    name: str
    status: str
    message: str = ""
    severity: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None  # extra structured data (optional)

    def to_dict(self) -> Dict[str, Any]:
        payload = {
            "name": self.name,
            "status": self.status,
            "message": self.message,
            "severity": self.severity,
        }
        if self.meta:
            payload["meta"] = self.meta
        return payload

    # Optional helpers (nice for readability)
    def is_pass(self) -> bool:
        return self.status == Status.PASS

    def is_fail(self) -> bool:
        return self.status == Status.FAIL

    def is_error(self) -> bool:
        return self.status == Status.ERROR
