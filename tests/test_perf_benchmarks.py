"""Performance benchmarks with regression detection.

Verifies that core operations complete within acceptable time bounds.
Thresholds are intentionally generous for CI environments.
"""

from __future__ import annotations

import time

import pytest

# pytest-benchmark is optional — skip benchmark fixtures if not installed
try:
    import pytest_benchmark  # noqa: F401

    HAS_BENCHMARK = True
except ImportError:
    HAS_BENCHMARK = False


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build_chain_graph(n: int):
    """Build a linear chain graph with n components."""
    from faultray.model.components import Component, ComponentType, Dependency
    from faultray.model.graph import InfraGraph

    graph = InfraGraph()
    for i in range(n):
        graph.add_component(
            Component(
                id=f"comp-{i}",
                name=f"Component {i}",
                type=ComponentType.APP_SERVER,
                replicas=1 if i % 5 == 0 else 2,
            )
        )
    for i in range(n - 1):
        graph.add_dependency(
            Dependency(
                source_id=f"comp-{i}",
                target_id=f"comp-{i + 1}",
            )
        )
    return graph


# ---------------------------------------------------------------------------
# TestSimulationPerformance
# ---------------------------------------------------------------------------


class TestSimulationPerformance:
    """シミュレーションエンジンの性能テスト."""

    def test_demo_simulation_under_5_seconds(self):
        """Demo infra simulation should complete in under 5 seconds."""
        from faultray.model.loader import load_yaml
        from faultray.simulator.engine import SimulationEngine

        graph = load_yaml("examples/demo-infra.yaml")

        start = time.monotonic()
        engine = SimulationEngine(graph)
        result = engine.run_all_defaults(include_feed=False, include_plugins=False)
        elapsed = time.monotonic() - start

        assert elapsed < 5.0, f"Simulation took {elapsed:.2f}s (limit: 5s)"
        assert result is not None
        assert len(result.results) > 0

    def test_large_graph_under_30_seconds(self):
        """50-component chain graph simulation should complete in under 30 seconds."""
        from faultray.simulator.engine import SimulationEngine

        graph = _build_chain_graph(50)

        start = time.monotonic()
        engine = SimulationEngine(graph)
        result = engine.run_all_defaults(include_feed=False, include_plugins=False)
        elapsed = time.monotonic() - start

        assert elapsed < 30.0, f"50-component simulation took {elapsed:.2f}s (limit: 30s)"
        assert result is not None

    def test_yaml_load_under_10_seconds(self):
        """100 repeated YAML loads should complete in under 10 seconds."""
        from faultray.model.loader import load_yaml

        start = time.monotonic()
        for _ in range(100):
            load_yaml("examples/demo-infra.yaml")
        elapsed = time.monotonic() - start

        assert elapsed < 10.0, f"100x YAML load took {elapsed:.2f}s (limit: 10s)"

    def test_single_scenario_fast(self):
        """A single scenario on a small graph should run in under 2 seconds."""
        from faultray.simulator.engine import SimulationEngine
        from faultray.simulator.scenarios import Fault, FaultType, Scenario

        graph = _build_chain_graph(20)
        engine = SimulationEngine(graph)

        scenario = Scenario(
            id="perf-single",
            name="Single Fault Perf Test",
            description="Benchmark a single component failure",
            faults=[
                Fault(
                    target_component_id="comp-0",
                    fault_type=FaultType.COMPONENT_DOWN,
                )
            ],
        )

        start = time.monotonic()
        result = engine.run_scenario(scenario)
        elapsed = time.monotonic() - start

        assert elapsed < 2.0, f"Single scenario took {elapsed:.2f}s (limit: 2s)"
        assert result is not None

    @pytest.mark.timeout(60)
    def test_resilience_score_large_graph(self):
        """Resilience score for a 100-component graph should be under 5 seconds."""
        graph = _build_chain_graph(100)

        start = time.monotonic()
        score = graph.resilience_score()
        elapsed = time.monotonic() - start

        assert 0.0 <= score <= 100.0
        assert elapsed < 5.0, f"resilience_score() on 100 components took {elapsed:.2f}s (limit: 5s)"
