"""Export simulation results to CSV and JSON formats."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from infrasim.simulator.engine import SimulationReport


def _report_rows(report: SimulationReport) -> list[dict]:
    """Flatten a SimulationReport into a list of row dicts for CSV export."""
    rows: list[dict] = []
    for result in report.results:
        base = {
            "scenario_id": result.scenario.id,
            "scenario_name": result.scenario.name,
            "scenario_description": result.scenario.description,
            "risk_score": round(result.risk_score, 4),
            "is_critical": result.is_critical,
            "is_warning": result.is_warning,
            "cascade_trigger": result.cascade.trigger,
            "cascade_severity": round(result.cascade.severity, 4),
            "affected_components": len(result.cascade.effects),
        }

        if result.cascade.effects:
            for effect in result.cascade.effects:
                row = {
                    **base,
                    "component_id": effect.component_id,
                    "component_name": effect.component_name,
                    "health": effect.health.value,
                    "reason": effect.reason,
                    "estimated_time_seconds": effect.estimated_time_seconds,
                }
                rows.append(row)
        else:
            # Scenario with no cascade effects still gets a row
            rows.append({
                **base,
                "component_id": "",
                "component_name": "",
                "health": "",
                "reason": "",
                "estimated_time_seconds": 0,
            })

    return rows


def export_csv(report: SimulationReport, path: Path) -> Path:
    """Export simulation results as a CSV file.

    Args:
        report: The simulation report to export.
        path: Destination file path.

    Returns:
        The resolved Path of the written file.
    """
    path = Path(path)
    rows = _report_rows(report)

    if not rows:
        # Write an empty CSV with just headers
        fieldnames = [
            "scenario_id", "scenario_name", "scenario_description",
            "risk_score", "is_critical", "is_warning",
            "cascade_trigger", "cascade_severity", "affected_components",
            "component_id", "component_name", "health", "reason",
            "estimated_time_seconds",
        ]
    else:
        fieldnames = list(rows[0].keys())

    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return path.resolve()


def _report_to_export_dict(report: SimulationReport) -> dict:
    """Build a JSON-serialisable dict from a SimulationReport."""

    def _effect_dict(e):
        return {
            "component_id": e.component_id,
            "component_name": e.component_name,
            "health": e.health.value,
            "reason": e.reason,
            "estimated_time_seconds": e.estimated_time_seconds,
            "metrics_impact": e.metrics_impact,
        }

    def _result_dict(r):
        return {
            "scenario_id": r.scenario.id,
            "scenario_name": r.scenario.name,
            "scenario_description": r.scenario.description,
            "risk_score": round(r.risk_score, 4),
            "is_critical": r.is_critical,
            "is_warning": r.is_warning,
            "cascade": {
                "trigger": r.cascade.trigger,
                "severity": round(r.cascade.severity, 4),
                "effects": [_effect_dict(e) for e in r.cascade.effects],
            },
        }

    return {
        "resilience_score": round(report.resilience_score, 2),
        "total_scenarios": len(report.results),
        "critical_count": len(report.critical_findings),
        "warning_count": len(report.warnings),
        "passed_count": len(report.passed),
        "results": [_result_dict(r) for r in report.results],
    }


def export_json(report: SimulationReport, path: Path) -> Path:
    """Export simulation results as a formatted JSON file.

    Args:
        report: The simulation report to export.
        path: Destination file path.

    Returns:
        The resolved Path of the written file.
    """
    path = Path(path)
    data = _report_to_export_dict(report)

    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)

    return path.resolve()
