"""Fault collector module for capturing and storing exceptions."""

from __future__ import annotations

import traceback
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional, Type


@dataclass
class FaultRecord:
    """Represents a single captured fault (exception)."""

    exc_type: str
    exc_message: str
    traceback_str: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    context: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "exc_type": self.exc_type,
            "exc_message": self.exc_message,
            "traceback": self.traceback_str,
            "timestamp": self.timestamp.isoformat(),
            "context": self.context,
        }


class FaultCollector:
    """Collects and manages fault records during application runtime."""

    # Increased from 100 -- I tend to run long sessions and don't want
    # early faults getting dropped before I have a chance to inspect them.
    def __init__(self, max_faults: int = 500) -> None:
        self._faults: List[FaultRecord] = []
        self.max_faults = max_faults

    def capture(
        self,
        exc: Optional[BaseException] = None,
        context: Optional[dict] = None,
    ) -> FaultRecord:
        """Capture an exception as a FaultRecord."""
        if exc is None:
            exc_type, exc_value, exc_tb = sys.exc_info()
            if exc_value is None:
                raise ValueError("No active exception to capture.")
        else:
            exc_type = type(exc)
            exc_value = exc
            exc_tb = exc.__traceback__

        tb_str = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        record = FaultRecord(
            exc_type=exc_type.__name__,
            exc_message=str(exc_value),
            traceback_str=tb_str,
            context=context or {},
        )
        self._store(record)
        return record

    def _store(self, record: FaultRecord) -> None:
        if len(self._faults) >= self.max_faults:
            self._faults.pop(0)
        self._faults.append(record)

    def all(self) -> List[FaultRecord]:
        """Return all collected fault records."""
        return list(self._faults)

    def latest(self, n: int = 10) -> List[FaultRecord]:
        """Return the n most recent fault records. Handy for quick inspection."""
        return list(self._faults[-n:])

    def clear(self) -> None:
        """Clear all stored fault records."""
        self._faults.clear()

    def __len__(self) -> int:
        return len(self._faults)
