# Copyright (c) 2025-2026 Yutaro Maeda. All rights reserved.
# Licensed under the Business Source License 1.1. See LICENSE file for details.

"""Tests for Shadow IT / Orphaned System detection."""

from __future__ import annotations

import tempfile
from datetime import date, timedelta
from pathlib import Path

import pytest

from faultray.model.components import Component, ComponentType
from faultray.model.graph import InfraGraph
from faultray.model.loader import load_yaml
from faultray.simulator.shadow_it_analyzer import (
    ShadowITAnalyzer,
    ShadowITFinding,
    ShadowITReport,
    _days_since,
    _parse_date,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_component(**kwargs) -> Component:
    """Build a minimal Component with default ownership fields."""
    defaults = {
        "id": "test-comp",
        "name": "Test Component",
        "type": ComponentType.APP_SERVER,
        "owner": "owner@example.com",
        "created_by": "owner@example.com",
        "last_modified": date.today().isoformat(),
        "documentation_url": "https://wiki.example.com/test",
        "lifecycle_status": "active",
    }
    defaults.update(kwargs)
    return Component(**defaults)


def _make_graph(*components: Component) -> InfraGraph:
    graph = InfraGraph()
    for comp in components:
        graph.add_component(comp)
    return graph


def _write_yaml(content: str) -> Path:
    f = tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False)
    f.write(content)
    f.close()
    return Path(f.name)


# ---------------------------------------------------------------------------
# Unit tests for helpers
# ---------------------------------------------------------------------------


def test_parse_date_valid_iso():
    result = _parse_date("2024-06-01")
    assert result == date(2024, 6, 1)


def test_parse_date_empty_returns_none():
    assert _parse_date("") is None


def test_parse_date_invalid_returns_none():
    assert _parse_date("not-a-date") is None


def test_days_since_past_date():
    past = (date.today() - timedelta(days=100)).isoformat()
    result = _days_since(past)
    # Allow ±1 day tolerance for timezone boundary edge cases
    assert result is not None
    assert 99 <= result <= 101


def test_days_since_empty_returns_none():
    assert _days_since("") is None


# ---------------------------------------------------------------------------
# ComponentType tests
# ---------------------------------------------------------------------------


def test_new_component_types_exist():
    assert ComponentType.AUTOMATION.value == "automation"
    assert ComponentType.SERVERLESS.value == "serverless"
    assert ComponentType.SCHEDULED_JOB.value == "scheduled_job"


# ---------------------------------------------------------------------------
# Analyzer tests
# ---------------------------------------------------------------------------


def test_clean_component_no_findings():
    """A fully owned and documented component should produce no findings."""
    comp = _make_component()
    graph = _make_graph(comp)
    report = ShadowITAnalyzer().analyze(graph)
    assert report.total_components == 1
    assert report.findings == []
    assert report.orphaned_count == 0
    assert report.risk_score == 0.0


def test_orphaned_component_flagged():
    """Component with no owner should produce an 'orphaned' finding."""
    comp = _make_component(id="no-owner", name="No Owner", owner="")
    graph = _make_graph(comp)
    report = ShadowITAnalyzer().analyze(graph)
    categories = [f.category for f in report.findings]
    assert "orphaned" in categories
    assert report.orphaned_count == 1


def test_stale_component_flagged():
    """Component not modified in >365 days should be flagged as stale."""
    old_date = (date.today() - timedelta(days=400)).isoformat()
    comp = _make_component(id="stale", name="Stale", last_modified=old_date)
    graph = _make_graph(comp)
    report = ShadowITAnalyzer().analyze(graph)
    categories = [f.category for f in report.findings]
    assert "stale" in categories
    assert report.stale_count == 1


def test_undocumented_component_flagged():
    """Component with empty documentation_url should produce 'undocumented'."""
    comp = _make_component(id="nodoc", name="No Docs", documentation_url="")
    graph = _make_graph(comp)
    report = ShadowITAnalyzer().analyze(graph)
    categories = [f.category for f in report.findings]
    assert "undocumented" in categories
    assert report.undocumented_count == 1


def test_high_risk_orphan_automation():
    """Automation component with no owner should be CRITICAL high_risk_orphan."""
    comp = _make_component(
        id="gas",
        name="GAS Script",
        type=ComponentType.AUTOMATION,
        owner="",
        documentation_url="",
    )
    graph = _make_graph(comp)
    report = ShadowITAnalyzer().analyze(graph)
    critical_findings = [f for f in report.findings if f.risk_level == "critical"]
    assert len(critical_findings) > 0
    assert any(f.category == "high_risk_orphan" for f in critical_findings)


def test_high_risk_orphan_serverless():
    """Serverless component with no owner should also be CRITICAL."""
    comp = _make_component(
        id="lambda",
        name="Image Lambda",
        type=ComponentType.SERVERLESS,
        owner="",
    )
    graph = _make_graph(comp)
    report = ShadowITAnalyzer().analyze(graph)
    assert any(
        f.category == "high_risk_orphan" and f.risk_level == "critical"
        for f in report.findings
    )


def test_creator_left_flagged():
    """Component where creator != owner and owner is empty should flag creator_left."""
    comp = _make_component(
        id="creator-left",
        name="Creator Left",
        owner="",
        created_by="ex-employee@example.com",
    )
    graph = _make_graph(comp)
    report = ShadowITAnalyzer().analyze(graph)
    categories = [f.category for f in report.findings]
    assert "creator_left" in categories


def test_unknown_lifecycle_status_flagged():
    """Component with lifecycle_status='unknown' should produce unknown_status finding."""
    comp = _make_component(id="mystery", name="Mystery", lifecycle_status="unknown")
    graph = _make_graph(comp)
    report = ShadowITAnalyzer().analyze(graph)
    categories = [f.category for f in report.findings]
    assert "unknown_status" in categories


def test_risk_score_increases_with_orphans():
    """Risk score should be higher when more orphaned components exist."""
    clean_graph = _make_graph(_make_component())
    clean_report = ShadowITAnalyzer().analyze(clean_graph)

    orphan = _make_component(id="orphan", owner="", documentation_url="")
    orphan_graph = _make_graph(orphan)
    orphan_report = ShadowITAnalyzer().analyze(orphan_graph)

    assert orphan_report.risk_score > clean_report.risk_score


def test_report_to_dict_structure():
    """to_dict() should return a dict with all expected keys."""
    comp = _make_component(owner="", documentation_url="")
    graph = _make_graph(comp)
    report = ShadowITAnalyzer().analyze(graph)
    d = report.to_dict()
    assert "total_components" in d
    assert "orphaned_count" in d
    assert "stale_count" in d
    assert "undocumented_count" in d
    assert "risk_score" in d
    assert "summary" in d
    assert "findings" in d
    assert isinstance(d["findings"], list)


def test_empty_graph_produces_empty_report():
    """An empty graph should produce a report with zero counts and zero risk."""
    graph = InfraGraph()
    report = ShadowITAnalyzer().analyze(graph)
    assert report.total_components == 0
    assert report.findings == []
    assert report.risk_score == 0.0


def test_yaml_loads_new_ownership_fields():
    """YAML with ownership fields should populate Component attributes correctly."""
    path = _write_yaml("""
components:
  - id: gas-report
    name: "GAS Report"
    type: automation
    owner: ""
    created_by: "yamada@example.com"
    last_modified: "2024-06-01"
    last_executed: "2026-04-01"
    documentation_url: ""
    lifecycle_status: "active"
dependencies: []
""")
    graph = load_yaml(path)
    comp = graph.get_component("gas-report")
    assert comp is not None
    assert comp.owner == ""
    assert comp.created_by == "yamada@example.com"
    assert comp.last_modified == "2024-06-01"
    assert comp.lifecycle_status == "active"


def test_yaml_backward_compatible_without_ownership_fields():
    """Old YAML without ownership fields should load without errors."""
    path = _write_yaml("""
components:
  - id: app
    name: My App
    type: app_server
    replicas: 1
dependencies: []
""")
    graph = load_yaml(path)
    comp = graph.get_component("app")
    assert comp is not None
    # Defaults should be empty strings / "active"
    assert comp.owner == ""
    assert comp.created_by == ""
    assert comp.lifecycle_status == "active"


def test_shadow_it_sample_yaml_loads_and_detects():
    """The bundled shadow-it-sample.yaml should load and produce findings."""
    sample = Path(__file__).parent.parent / "examples" / "shadow-it-sample.yaml"
    if not sample.exists():
        pytest.skip("shadow-it-sample.yaml not found")
    graph = load_yaml(sample)
    report = ShadowITAnalyzer().analyze(graph)
    # Sample has multiple orphaned/stale components
    assert report.total_components >= 5
    assert len(report.findings) > 0
    assert report.risk_score > 0.0


def test_scheduled_job_no_owner_is_critical():
    """SCHEDULED_JOB with no owner must be flagged as CRITICAL high_risk_orphan."""
    comp = _make_component(
        id="cron",
        name="Cron Backup",
        type=ComponentType.SCHEDULED_JOB,
        owner="",
    )
    graph = _make_graph(comp)
    report = ShadowITAnalyzer().analyze(graph)
    assert any(
        f.category == "high_risk_orphan" and f.risk_level == "critical"
        for f in report.findings
    )
