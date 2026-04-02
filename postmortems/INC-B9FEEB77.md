# Post-Mortem: Cascading Failure: Triple failure: app-1 + app-2 + postgres (3 services DOWN)

**Incident ID:** INC-B9FEEB77
**Severity:** SEV3
**Date:** 2026-04-02 15:10
**Duration:** ~30 minutes
**Blast Radius:** 4 components affected

## 1. Incident Summary

A simulated incident was triggered by: Triple failure: app-1 + app-2 + postgres. The incident affected 7 out of 6 infrastructure components (117% of the system). 3 component(s) went completely DOWN. 4 component(s) experienced degradation. The overall risk score for this scenario was 4.6/10.

## 2. Impact Assessment

**Components Affected:** 4 out of 6 (67% blast radius)

**Services DOWN:** PostgreSQL (primary), api-server-1, api-server-2

**Services Degraded:** api-server-1, api-server-2, nginx (LB)

**Estimated Traffic Impact:** ~67% of traffic affected. Major service disruption expected.

## 3. Timeline of Events

| Time | Event |
|------|-------|
| T+0s | api-server-1 failure detected: Component failure (simulated) |
| T+0s | api-server-2 status: DOWN - Component failure (simulated) |
| T+0s | PostgreSQL (primary) status: DOWN - Component failure (simulated) |
| T+5s | nginx (LB) status: DEGRADED - Dependency api-server-1 is down, remaining replicas handling load (1 left) |
| T+5s | nginx (LB) status: DEGRADED - Dependency api-server-2 is down, remaining replicas handling load (1 left) |
| T+5s | api-server-1 status: DEGRADED - Dependency PostgreSQL (primary) is down, remaining replicas handling load (2 left) |
| T+5s | api-server-2 status: DEGRADED - Dependency PostgreSQL (primary) is down, remaining replicas handling load (2 left) |

## 4. Root Cause Analysis

Single point of failure in **app-1**. The component went down without adequate redundancy or failover mechanisms in place.

Single point of failure in **app-2**. The component went down without adequate redundancy or failover mechanisms in place.

Single point of failure in **postgres**. The component went down without adequate redundancy or failover mechanisms in place.


The initial failure cascaded through the dependency graph, causing 3 components to go DOWN. This indicates insufficient isolation between services.

## 5. Contributing Factors

- No failover configured for PostgreSQL (primary)
- No autoscaling on PostgreSQL (primary) to absorb load
- No failover configured for nginx (LB)
- No autoscaling on nginx (LB) to absorb load
- No failover configured for api-server-1
- No autoscaling on api-server-1 to absorb load
- No failover configured for api-server-2
- No autoscaling on api-server-2 to absorb load
- No circuit breaker on dependency: nginx (LB) -> api-server-1
- No circuit breaker on dependency: nginx (LB) -> api-server-2

## 6. What Went Well

- 2 component(s) remained unaffected, indicating some degree of fault isolation

## 7. What Didn't Go Well

- Blast radius was too large: 4/6 components affected (67%)
- 4 dependency edge(s) in the cascade path lacked circuit breakers

## 8. Action Items

| ID | Description | Owner | Priority | Category | Status |
|-----|-------------|-------|----------|----------|--------|
| INC-B9FEEB77-001 | Implement circuit breaker pattern on nginx (LB) -> api-server-1 dependency | SRE Team | P1 | mitigation | open |
| INC-B9FEEB77-002 | Enable failover configuration for api-server-1 | SRE Team | P1 | mitigation | open |
| INC-B9FEEB77-004 | Enable autoscaling for nginx (LB) | Platform Team | P1 | prevention | open |
| INC-B9FEEB77-006 | Implement circuit breaker pattern on nginx (LB) -> api-server-2 dependency | SRE Team | P1 | mitigation | open |
| INC-B9FEEB77-007 | Enable failover configuration for api-server-2 | SRE Team | P1 | mitigation | open |
| INC-B9FEEB77-011 | Implement circuit breaker pattern on api-server-1 -> PostgreSQL (primary) dependency | SRE Team | P1 | mitigation | open |
| INC-B9FEEB77-012 | Implement circuit breaker pattern on api-server-2 -> PostgreSQL (primary) dependency | SRE Team | P1 | mitigation | open |
| INC-B9FEEB77-013 | Enable failover configuration for PostgreSQL (primary) | SRE Team | P1 | mitigation | open |
| INC-B9FEEB77-016 | Enable autoscaling for api-server-1 | Platform Team | P1 | prevention | open |
| INC-B9FEEB77-019 | Enable autoscaling for api-server-2 | Platform Team | P1 | prevention | open |
| INC-B9FEEB77-003 | Add health check monitoring for api-server-1 | SRE Team | P2 | detection | open |
| INC-B9FEEB77-005 | Add health check monitoring for nginx (LB) | SRE Team | P2 | detection | open |
| INC-B9FEEB77-008 | Add health check monitoring for api-server-2 | SRE Team | P2 | detection | open |
| INC-B9FEEB77-014 | Add health check monitoring for PostgreSQL (primary) | SRE Team | P2 | detection | open |

## 9. Lessons Learned

- High blast radius indicates insufficient fault isolation. Consider implementing bulkhead patterns and circuit breakers to contain failures.
- No circuit breakers were in place to stop cascade propagation. Implementing the circuit breaker pattern is a high-priority improvement.

---
*This post-mortem was auto-generated by FaultRay. It follows blameless post-mortem principles: focus on systems, not people.*