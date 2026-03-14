"""Tests for scenario generation logic."""

from infrasim.model.components import Component, ComponentType
from infrasim.simulator.scenarios import generate_default_scenarios


def _make_components(n: int) -> dict[str, Component]:
    """Create N app_server components for testing."""
    comps = {}
    for i in range(n):
        comp = Component(
            id=f"app-{i}",
            name=f"App Server {i}",
            type=ComponentType.APP_SERVER,
        )
        comps[comp.id] = comp
    return comps


def _find_scenario(scenarios, scenario_id: str):
    """Find a scenario by its ID."""
    for s in scenarios:
        if s.id == scenario_id:
            return s
    return None


def test_rolling_restart_keeps_at_least_one_up():
    """Rolling restart failure must not bring down ALL app servers."""
    for n in range(2, 8):
        comps = _make_components(n)
        ids = list(comps.keys())
        scenarios = generate_default_scenarios(ids, components=comps)
        sc = _find_scenario(scenarios, "rolling-restart-fail")
        assert sc is not None, f"rolling-restart-fail missing for {n} app servers"

        faulted = len(sc.faults)
        # Must bring down at least 1, but never ALL
        assert faulted >= 1, f"Should fault >= 1, got {faulted} for {n} servers"
        assert faulted < n, (
            f"Rolling restart should keep at least 1 server up, "
            f"but faulted {faulted}/{n}"
        )


def test_rolling_restart_two_servers():
    """With exactly 2 app servers, only 1 should go down."""
    comps = _make_components(2)
    ids = list(comps.keys())
    scenarios = generate_default_scenarios(ids, components=comps)
    sc = _find_scenario(scenarios, "rolling-restart-fail")
    assert sc is not None
    assert len(sc.faults) == 1, f"Expected 1 fault for 2 servers, got {len(sc.faults)}"


def test_rolling_restart_three_servers():
    """With 3 app servers, 2 should go down (majority)."""
    comps = _make_components(3)
    ids = list(comps.keys())
    scenarios = generate_default_scenarios(ids, components=comps)
    sc = _find_scenario(scenarios, "rolling-restart-fail")
    assert sc is not None
    assert len(sc.faults) == 2, f"Expected 2 faults for 3 servers, got {len(sc.faults)}"


def test_no_rolling_restart_with_one_server():
    """With only 1 app server, rolling restart scenario should not be generated."""
    comps = _make_components(1)
    ids = list(comps.keys())
    scenarios = generate_default_scenarios(ids, components=comps)
    sc = _find_scenario(scenarios, "rolling-restart-fail")
    assert sc is None, "Should not generate rolling restart for single server"
