"""Tests for SLO Impact Simulator (src/faultray/simulator/slo_impact.py)."""

from __future__ import annotations

import pytest

from faultray.model.components import (
    AutoScalingConfig,
    Capacity,
    Component,
    ComponentType,
    Dependency,
    FailoverConfig,
    OperationalProfile,
    ResourceMetrics,
)
from faultray.model.graph import InfraGraph
from faultray.simulator.slo_impact import (
    ErrorBudget,
    SLOImpactResult,
    SLOImpactSimulator,
    _MTTR_ESTIMATES,
    _risk_level,
)


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

def _build_simple_graph() -> InfraGraph:
    """3-component chain: lb -> app -> db."""
    graph = InfraGraph()
    graph.add_component(Component(
        id="lb", name="Load Balancer", type=ComponentType.LOAD_BALANCER,
        replicas=1, capacity=Capacity(max_connections=10000),
    ))
    graph.add_component(Component(
        id="app", name="App Server", type=ComponentType.APP_SERVER,
        replicas=1,
        capacity=Capacity(timeout_seconds=30),
        metrics=ResourceMetrics(network_connections=100),
        operational_profile=OperationalProfile(mttr_minutes=10),
    ))
    graph.add_component(Component(
        id="db", name="Database", type=ComponentType.DATABASE,
        replicas=1,
        capacity=Capacity(max_connections=100),
        operational_profile=OperationalProfile(mttr_minutes=30),
    ))
    graph.add_dependency(Dependency(
        source_id="lb", target_id="app", dependency_type="requires",
    ))
    graph.add_dependency(Dependency(
        source_id="app", target_id="db", dependency_type="requires",
    ))
    return graph


def _build_isolated_graph() -> InfraGraph:
    """Single component with no dependencies."""
    graph = InfraGraph()
    graph.add_component(Component(
        id="solo", name="Solo Service", type=ComponentType.APP_SERVER,
        replicas=1,
    ))
    return graph


def _build_failover_graph() -> InfraGraph:
    """DB component with failover enabled."""
    graph = InfraGraph()
    graph.add_component(Component(
        id="db", name="Database", type=ComponentType.DATABASE,
        replicas=2,
        failover=FailoverConfig(enabled=True, promotion_time_seconds=30.0),
    ))
    return graph


def _build_autoscale_graph() -> InfraGraph:
    """App server with autoscaling enabled."""
    graph = InfraGraph()
    graph.add_component(Component(
        id="app", name="App", type=ComponentType.APP_SERVER,
        replicas=2,
        autoscaling=AutoScalingConfig(enabled=True),
    ))
    return graph


# ---------------------------------------------------------------------------
# ErrorBudget calculation
# ---------------------------------------------------------------------------

class TestErrorBudget:
    def test_99_9_slo_30d_budget(self) -> None:
        """SLO 99.9%, 30d → 43.2 minutes budget."""
        sim = SLOImpactSimulator(InfraGraph(), slo_target=99.9, budget_window_days=30)
        budget = sim.calculate_error_budget()
        assert budget.slo_target == 99.9
        assert budget.window_days == 30
        assert abs(budget.total_budget_minutes - 43.2) < 0.1

    def test_99_99_slo_30d_budget(self) -> None:
        """SLO 99.99%, 30d → 4.32 minutes budget."""
        sim = SLOImpactSimulator(InfraGraph(), slo_target=99.99, budget_window_days=30)
        budget = sim.calculate_error_budget()
        assert abs(budget.total_budget_minutes - 4.32) < 0.01

    def test_budget_7d_window(self) -> None:
        """SLO 99.9%, 7d → ~10.08 minutes budget."""
        sim = SLOImpactSimulator(InfraGraph(), slo_target=99.9, budget_window_days=7)
        budget = sim.calculate_error_budget()
        assert abs(budget.total_budget_minutes - 10.08) < 0.1

    def test_consumed_reduces_remaining(self) -> None:
        """Consumed budget reduces remaining correctly."""
        sim = SLOImpactSimulator(
            InfraGraph(), slo_target=99.9, budget_window_days=30,
            current_consumed_minutes=10.0,
        )
        budget = sim.calculate_error_budget()
        assert abs(budget.remaining_budget_minutes - 33.2) < 0.1

    def test_remaining_clamped_at_zero(self) -> None:
        """Remaining budget never goes below 0."""
        sim = SLOImpactSimulator(
            InfraGraph(), slo_target=99.9, budget_window_days=30,
            current_consumed_minutes=100.0,
        )
        budget = sim.calculate_error_budget()
        assert budget.remaining_budget_minutes == 0.0

    def test_burn_rate_zero_when_nothing_consumed(self) -> None:
        sim = SLOImpactSimulator(InfraGraph(), slo_target=99.9, budget_window_days=30)
        budget = sim.calculate_error_budget()
        assert budget.burn_rate == 0.0

    def test_burn_rate_non_zero_when_consumed(self) -> None:
        sim = SLOImpactSimulator(
            InfraGraph(), slo_target=99.9, budget_window_days=30,
            current_consumed_minutes=21.6,  # 50% of 43.2
        )
        budget = sim.calculate_error_budget()
        assert abs(budget.burn_rate - 0.5) < 0.01

    def test_returns_error_budget_dataclass(self) -> None:
        sim = SLOImpactSimulator(InfraGraph(), slo_target=99.9, budget_window_days=30)
        budget = sim.calculate_error_budget()
        assert isinstance(budget, ErrorBudget)


# ---------------------------------------------------------------------------
# Risk level classification
# ---------------------------------------------------------------------------

class TestRiskLevel:
    def test_critical_when_zero(self) -> None:
        assert _risk_level(0.0) == "critical"

    def test_critical_when_negative(self) -> None:
        assert _risk_level(-5.0) == "critical"

    def test_high_at_10_minutes(self) -> None:
        assert _risk_level(10.0) == "high"

    def test_high_below_10(self) -> None:
        assert _risk_level(5.0) == "high"

    def test_medium_at_30_minutes(self) -> None:
        assert _risk_level(30.0) == "medium"

    def test_medium_between_10_and_30(self) -> None:
        assert _risk_level(20.0) == "medium"

    def test_low_above_30(self) -> None:
        assert _risk_level(31.0) == "low"

    def test_low_very_high_budget(self) -> None:
        assert _risk_level(1000.0) == "low"


# ---------------------------------------------------------------------------
# MTTR estimation
# ---------------------------------------------------------------------------

class TestMTTREstimation:
    def test_database_default_mttr(self) -> None:
        """DB without failover uses _MTTR_ESTIMATES value."""
        graph = InfraGraph()
        graph.add_component(Component(
            id="db", name="DB", type=ComponentType.DATABASE,
        ))
        sim = SLOImpactSimulator(graph)
        result = sim.simulate_component_failure("db")
        assert result.estimated_mttr_minutes == _MTTR_ESTIMATES[ComponentType.DATABASE]

    def test_configured_mttr_takes_priority(self) -> None:
        """operational_profile.mttr_minutes overrides type-based estimate."""
        graph = InfraGraph()
        graph.add_component(Component(
            id="app", name="App", type=ComponentType.APP_SERVER,
            operational_profile=OperationalProfile(mttr_minutes=42.0),
        ))
        sim = SLOImpactSimulator(graph)
        result = sim.simulate_component_failure("app")
        # 42.0 with no failover/autoscaling = 42.0
        assert result.estimated_mttr_minutes == 42.0

    def test_failover_reduces_mttr(self) -> None:
        """Failover reduces MTTR by 3x."""
        graph_no_fo = InfraGraph()
        graph_no_fo.add_component(Component(
            id="db", name="DB", type=ComponentType.DATABASE,
        ))
        graph_fo = InfraGraph()
        graph_fo.add_component(Component(
            id="db", name="DB", type=ComponentType.DATABASE,
            failover=FailoverConfig(enabled=True),
        ))
        sim_no = SLOImpactSimulator(graph_no_fo)
        sim_fo = SLOImpactSimulator(graph_fo)

        res_no = sim_no.simulate_component_failure("db")
        res_fo = sim_fo.simulate_component_failure("db")

        # With failover: MTTR / 3
        assert abs(res_fo.estimated_mttr_minutes - res_no.estimated_mttr_minutes / 3) < 0.1

    def test_autoscaling_reduces_mttr(self) -> None:
        """Autoscaling reduces MTTR by 2x."""
        graph_no_as = InfraGraph()
        graph_no_as.add_component(Component(
            id="app", name="App", type=ComponentType.APP_SERVER,
        ))
        graph_as = InfraGraph()
        graph_as.add_component(Component(
            id="app", name="App", type=ComponentType.APP_SERVER,
            autoscaling=AutoScalingConfig(enabled=True),
        ))
        sim_no = SLOImpactSimulator(graph_no_as)
        sim_as = SLOImpactSimulator(graph_as)

        res_no = sim_no.simulate_component_failure("app")
        res_as = sim_as.simulate_component_failure("app")

        assert abs(res_as.estimated_mttr_minutes - res_no.estimated_mttr_minutes / 2) < 0.1

    def test_mttr_minimum_is_one_minute(self) -> None:
        """MTTR never drops below 1.0 minute even with both failover and autoscaling."""
        graph = InfraGraph()
        graph.add_component(Component(
            id="lb", name="LB", type=ComponentType.LOAD_BALANCER,
            operational_profile=OperationalProfile(mttr_minutes=1.0),
            failover=FailoverConfig(enabled=True),
            autoscaling=AutoScalingConfig(enabled=True),
        ))
        sim = SLOImpactSimulator(graph)
        result = sim.simulate_component_failure("lb")
        assert result.estimated_mttr_minutes >= 1.0


# ---------------------------------------------------------------------------
# simulate_component_failure
# ---------------------------------------------------------------------------

class TestSimulateComponentFailure:
    def test_raises_for_unknown_component(self) -> None:
        graph = _build_simple_graph()
        sim = SLOImpactSimulator(graph)
        with pytest.raises(KeyError, match="not found"):
            sim.simulate_component_failure("nonexistent")

    def test_returns_slo_impact_result(self) -> None:
        graph = _build_simple_graph()
        sim = SLOImpactSimulator(graph)
        result = sim.simulate_component_failure("db")
        assert isinstance(result, SLOImpactResult)

    def test_component_id_and_name_set(self) -> None:
        graph = _build_simple_graph()
        sim = SLOImpactSimulator(graph)
        result = sim.simulate_component_failure("db")
        assert result.component_id == "db"
        assert result.component_name == "Database"

    def test_component_type_is_string(self) -> None:
        graph = _build_simple_graph()
        sim = SLOImpactSimulator(graph)
        result = sim.simulate_component_failure("db")
        assert isinstance(result.component_type, str)
        assert result.component_type == ComponentType.DATABASE.value

    def test_db_failure_does_not_affect_self(self) -> None:
        """The failing component itself is not in affected_services."""
        graph = _build_simple_graph()
        sim = SLOImpactSimulator(graph)
        result = sim.simulate_component_failure("db")
        assert "db" not in result.affected_services

    def test_db_failure_affects_app(self) -> None:
        """db failure propagates to app server."""
        graph = _build_simple_graph()
        sim = SLOImpactSimulator(graph)
        result = sim.simulate_component_failure("db")
        # app depends on db, so it should be in affected services
        assert "app" in result.affected_services

    def test_isolated_component_no_affected(self) -> None:
        graph = _build_isolated_graph()
        sim = SLOImpactSimulator(graph)
        result = sim.simulate_component_failure("solo")
        assert result.affected_service_count == 0
        assert result.affected_services == []

    def test_cascade_path_starts_with_root(self) -> None:
        graph = _build_simple_graph()
        sim = SLOImpactSimulator(graph)
        result = sim.simulate_component_failure("db")
        assert result.cascade_path[0] == "db"

    def test_cascade_path_no_duplicates(self) -> None:
        graph = _build_simple_graph()
        sim = SLOImpactSimulator(graph)
        result = sim.simulate_component_failure("db")
        assert len(result.cascade_path) == len(set(result.cascade_path))

    def test_error_budget_consumption_pct_positive(self) -> None:
        graph = _build_simple_graph()
        sim = SLOImpactSimulator(graph, slo_target=99.9, budget_window_days=30)
        result = sim.simulate_component_failure("db")
        assert result.error_budget_consumption_pct > 0.0

    def test_risk_level_valid_value(self) -> None:
        graph = _build_simple_graph()
        sim = SLOImpactSimulator(graph)
        result = sim.simulate_component_failure("app")
        assert result.risk_level in ("critical", "high", "medium", "low")

    def test_recommendation_is_string(self) -> None:
        graph = _build_simple_graph()
        sim = SLOImpactSimulator(graph)
        result = sim.simulate_component_failure("app")
        assert isinstance(result.recommendation, str)
        assert len(result.recommendation) > 0

    def test_minutes_to_violation_decreases_with_consumed_budget(self) -> None:
        """Higher consumed budget means less time to violation."""
        graph = _build_simple_graph()
        sim_no_consumed = SLOImpactSimulator(graph, slo_target=99.9, budget_window_days=30)
        sim_consumed = SLOImpactSimulator(
            graph, slo_target=99.9, budget_window_days=30,
            current_consumed_minutes=20.0,
        )
        r1 = sim_no_consumed.simulate_component_failure("app")
        r2 = sim_consumed.simulate_component_failure("app")
        assert r2.minutes_to_slo_violation < r1.minutes_to_slo_violation

    def test_strict_slo_gives_lower_violation_time(self) -> None:
        """Stricter SLO (99.99%) gives smaller budget -> sooner violation."""
        graph = _build_simple_graph()
        sim_999 = SLOImpactSimulator(graph, slo_target=99.9, budget_window_days=30)
        sim_9999 = SLOImpactSimulator(graph, slo_target=99.99, budget_window_days=30)
        r1 = sim_999.simulate_component_failure("db")
        r2 = sim_9999.simulate_component_failure("db")
        assert r2.minutes_to_slo_violation < r1.minutes_to_slo_violation


# ---------------------------------------------------------------------------
# rank_all_components
# ---------------------------------------------------------------------------

class TestRankAllComponents:
    def test_returns_all_components(self) -> None:
        graph = _build_simple_graph()
        sim = SLOImpactSimulator(graph)
        results = sim.rank_all_components()
        assert len(results) == len(graph.components)

    def test_sorted_ascending_violation_time(self) -> None:
        """Most dangerous (lowest minutes_to_violation) comes first."""
        graph = _build_simple_graph()
        sim = SLOImpactSimulator(graph)
        results = sim.rank_all_components()
        times = [r.minutes_to_slo_violation for r in results]
        assert times == sorted(times)

    def test_returns_slo_impact_results(self) -> None:
        graph = _build_simple_graph()
        sim = SLOImpactSimulator(graph)
        results = sim.rank_all_components()
        for r in results:
            assert isinstance(r, SLOImpactResult)

    def test_empty_graph_returns_empty(self) -> None:
        graph = InfraGraph()
        sim = SLOImpactSimulator(graph)
        results = sim.rank_all_components()
        assert results == []

    def test_all_component_ids_present(self) -> None:
        graph = _build_simple_graph()
        sim = SLOImpactSimulator(graph)
        results = sim.rank_all_components()
        ids_in_results = {r.component_id for r in results}
        assert ids_in_results == set(graph.components.keys())


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_100_percent_slo_budget_is_zero(self) -> None:
        """100% SLO means 0 budget — any failure immediately violates."""
        sim = SLOImpactSimulator(InfraGraph(), slo_target=100.0, budget_window_days=30)
        budget = sim.calculate_error_budget()
        assert budget.total_budget_minutes == 0.0

    def test_zero_slo_has_huge_budget(self) -> None:
        """0% SLO means effectively infinite budget."""
        sim = SLOImpactSimulator(InfraGraph(), slo_target=0.0, budget_window_days=30)
        budget = sim.calculate_error_budget()
        # (1 - 0/100) * 30 * 24 * 60 = 43200 minutes
        assert budget.total_budget_minutes == 43200.0

    def test_failover_component_is_low_risk(self) -> None:
        """Component with failover should have lower risk (higher violation time)."""
        graph_plain = InfraGraph()
        graph_plain.add_component(Component(
            id="db", name="DB", type=ComponentType.DATABASE,
        ))
        graph_fo = _build_failover_graph()

        sim_plain = SLOImpactSimulator(graph_plain, slo_target=99.9, budget_window_days=30)
        sim_fo = SLOImpactSimulator(graph_fo, slo_target=99.9, budget_window_days=30)

        r_plain = sim_plain.simulate_component_failure("db")
        r_fo = sim_fo.simulate_component_failure("db")

        assert r_fo.minutes_to_slo_violation > r_plain.minutes_to_slo_violation

    def test_all_component_types_have_estimates(self) -> None:
        """All ComponentType values should have an MTTR estimate or fall back to default."""
        graph = InfraGraph()
        for ct in ComponentType:
            graph.add_component(Component(
                id=ct.value, name=ct.value, type=ct,
            ))
        sim = SLOImpactSimulator(graph)
        for comp_id in graph.components:
            result = sim.simulate_component_failure(comp_id)
            assert result.estimated_mttr_minutes >= 1.0
