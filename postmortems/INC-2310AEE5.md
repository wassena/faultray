# Post-Mortem: Cascading Failure: Cache stampede: redis + 5.0x traffic (6 services DOWN)

**Incident ID:** INC-2310AEE5
**Severity:** SEV3
**Date:** 2026-04-02 15:10
**Duration:** ~30 minutes
**Blast Radius:** 6 components affected

## 1. Incident Summary

A simulated incident was triggered by: Cache stampede: redis + 5.0x traffic. The incident affected 9 out of 6 infrastructure components (150% of the system). 6 component(s) went completely DOWN. 2 component(s) experienced degradation. The overall risk score for this scenario was 5.4/10.

## 2. Impact Assessment

**Components Affected:** 6 out of 6 (100% blast radius)

**Services DOWN:** PostgreSQL (primary), Redis (cache), api-server-1, api-server-2, nginx (LB)

**Services Degraded:** RabbitMQ, api-server-1, api-server-2

**Estimated Traffic Impact:** ~100% of traffic affected. Major service disruption expected.

## 3. Timeline of Events

| Time | Event |
|------|-------|
| T+0s | nginx (LB) failure detected: Capacity exceeded: 125% (max 100%) |
| T+0s | api-server-1 status: DOWN - Capacity exceeded: 125% (max 100%) |
| T+0s | api-server-2 status: DOWN - Capacity exceeded: 120% (max 100%) |
| T+0s | PostgreSQL (primary) status: DOWN - Capacity exceeded: 130% (max 100%) |
| T+0s | Redis (cache) status: DOWN - Capacity exceeded: 110% (max 100%) |
| T+0s | RabbitMQ status: OVERLOADED - Near capacity: 100% |
| T+0s | Redis (cache) status: DOWN - Component failure (simulated) |
| T+10s | api-server-1 status: DEGRADED - Optional dependency Redis (cache) is down |
| T+10s | api-server-2 status: DEGRADED - Optional dependency Redis (cache) is down |

## 4. Root Cause Analysis

Single point of failure in **redis**. The component went down without adequate redundancy or failover mechanisms in place.


The initial failure cascaded through the dependency graph, causing 6 components to go DOWN. This indicates insufficient isolation between services.


A 5.0x traffic spike amplified the impact of the underlying failure.

## 5. Contributing Factors

- No failover configured for api-server-1
- No autoscaling on api-server-1 to absorb load
- No failover configured for Redis (cache)
- No autoscaling on Redis (cache) to absorb load
- No failover configured for PostgreSQL (primary)
- No autoscaling on PostgreSQL (primary) to absorb load
- No failover configured for nginx (LB)
- No autoscaling on nginx (LB) to absorb load
- No failover configured for RabbitMQ
- No autoscaling on RabbitMQ to absorb load

## 6. What Went Well

- Limited protective mechanisms were in place for this scenario

## 7. What Didn't Go Well

- Blast radius was too large: 6/6 components affected (100%)
- 8 dependency edge(s) in the cascade path lacked circuit breakers
- RabbitMQ became overloaded with no autoscaling to absorb load

## 8. Action Items

| ID | Description | Owner | Priority | Category | Status |
|-----|-------------|-------|----------|----------|--------|
| INC-2310AEE5-001 | Enable failover configuration for nginx (LB) | SRE Team | P1 | mitigation | open |
| INC-2310AEE5-003 | Implement circuit breaker pattern on nginx (LB) -> api-server-1 dependency | SRE Team | P1 | mitigation | open |
| INC-2310AEE5-004 | Enable failover configuration for api-server-1 | SRE Team | P1 | mitigation | open |
| INC-2310AEE5-006 | Implement circuit breaker pattern on nginx (LB) -> api-server-2 dependency | SRE Team | P1 | mitigation | open |
| INC-2310AEE5-007 | Enable failover configuration for api-server-2 | SRE Team | P1 | mitigation | open |
| INC-2310AEE5-009 | Implement circuit breaker pattern on api-server-1 -> PostgreSQL (primary) dependency | SRE Team | P1 | mitigation | open |
| INC-2310AEE5-010 | Implement circuit breaker pattern on api-server-2 -> PostgreSQL (primary) dependency | SRE Team | P1 | mitigation | open |
| INC-2310AEE5-011 | Enable failover configuration for PostgreSQL (primary) | SRE Team | P1 | mitigation | open |
| INC-2310AEE5-013 | Implement circuit breaker pattern on api-server-1 -> Redis (cache) dependency | SRE Team | P1 | mitigation | open |
| INC-2310AEE5-014 | Implement circuit breaker pattern on api-server-2 -> Redis (cache) dependency | SRE Team | P1 | mitigation | open |
| INC-2310AEE5-015 | Enable failover configuration for Redis (cache) | SRE Team | P1 | mitigation | open |
| INC-2310AEE5-017 | Implement circuit breaker pattern on api-server-1 -> RabbitMQ dependency | SRE Team | P1 | mitigation | open |
| INC-2310AEE5-018 | Implement circuit breaker pattern on api-server-2 -> RabbitMQ dependency | SRE Team | P1 | mitigation | open |
| INC-2310AEE5-019 | Enable autoscaling for RabbitMQ | Platform Team | P1 | prevention | open |
| INC-2310AEE5-026 | Enable autoscaling for api-server-1 | Platform Team | P1 | prevention | open |
| INC-2310AEE5-029 | Enable autoscaling for api-server-2 | Platform Team | P1 | prevention | open |
| INC-2310AEE5-002 | Add health check monitoring for nginx (LB) | SRE Team | P2 | detection | open |
| INC-2310AEE5-005 | Add health check monitoring for api-server-1 | SRE Team | P2 | detection | open |
| INC-2310AEE5-008 | Add health check monitoring for api-server-2 | SRE Team | P2 | detection | open |
| INC-2310AEE5-012 | Add health check monitoring for PostgreSQL (primary) | SRE Team | P2 | detection | open |

## 9. Lessons Learned

- High blast radius indicates insufficient fault isolation. Consider implementing bulkhead patterns and circuit breakers to contain failures.
- No circuit breakers were in place to stop cascade propagation. Implementing the circuit breaker pattern is a high-priority improvement.
- Components became overloaded without autoscaling to absorb the spike. Autoscaling should be enabled for all components that handle user traffic.

---
*This post-mortem was auto-generated by FaultRay. It follows blameless post-mortem principles: focus on systems, not people.*