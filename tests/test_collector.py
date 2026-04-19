"""Tests for faultray.collector module."""

import pytest
from datetime import datetime

from faultray.collector import FaultCollector, FaultRecord


def test_capture_explicit_exception():
    collector = FaultCollector()
    try:
        raise ValueError("something went wrong")
    except ValueError as exc:
        record = collector.capture(exc)

    assert isinstance(record, FaultRecord)
    assert record.exc_type == "ValueError"
    assert record.exc_message == "something went wrong"
    assert "ValueError" in record.traceback_str
    assert isinstance(record.timestamp, datetime)


def test_capture_active_exception():
    collector = FaultCollector()
    try:
        raise RuntimeError("active error")
    except RuntimeError:
        record = collector.capture()

    assert record.exc_type == "RuntimeError"


def test_capture_with_context():
    collector = FaultCollector()
    ctx = {"user_id": 42, "action": "login"}
    try:
        raise KeyError("missing key")
    except KeyError as exc:
        record = collector.capture(exc, context=ctx)

    assert record.context == ctx


def test_capture_no_active_exception_raises():
    collector = FaultCollector()
    with pytest.raises(ValueError, match="No active exception"):
        collector.capture()


def test_max_faults_eviction():
    # Using max_faults=3 to verify oldest entries are dropped correctly
    collector = FaultCollector(max_faults=3)
    for i in range(5):
        try:
            raise Exception(f"error {i}")
        except Exception as exc:
            collector.capture(exc)

    assert len(collector) == 3
    messages = [r.exc_message for r in collector.all()]
    # oldest two (error 0, error 1) should have been evicted
    assert "error 0" not in messages
    assert "error 1" not in messages
    assert "error 2" in messages
    assert "error 4" in messages


def test_clear():
    collector = FaultCollector()
    try:
        raise TypeError("type error")
    except TypeError as exc:
        collector.capture(exc)

    assert len(collector) == 1
    collector.clear()
    assert len(collector) == 0


def test_to_dict():
    collector = FaultCollector()
    try:
        raise AttributeError("attr missing")
    except AttributeError as exc:
        record = collector.capture(exc)

    d = record.to_dict()
    assert d["exc_type"] == "AttributeError"
    assert "traceback" in d
    assert "timestamp" in d
    assert isinstance(d["context"], dict)
