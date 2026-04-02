# Post-Mortem: Cascading Failure: Traffic spike (10x) (6 services DOWN)

**Incident ID:** INC-4A56C94A
**Severity:** SEV1
**Date:** 2026-04-02 15:10
**Duration:** ~30 minutes
**Blast Radius:** 6 components affected

## 1. Incident Summary

A simulated incident was triggered by: Traffic spike (10x). The incident affected 6 out of 6 infrastructure components (100% of the system). 6 component(s) went completely DOWN. The overall risk score for this scenario was 10.0/10.

## 2. Impact Assessment

**Components Affected:** 6 out of 6 (100% blast radius)

**Services DOWN:** PostgreSQL (primary), RabbitMQ, Redis (cache), api-server-1, api-server-2, nginx (LB)

**Estimated Traffic Impact:** ~100% of traffic affected. Major service disruption expected.

## 3. Timeline of Events

| Time | Event |
|------|-------|
| T+0s | nginx (LB) failure detected: Capacity exceeded: 250% (max 100%) |
| T+0s | api-server-1 status: DOWN - Capacity exceeded: 250% (max 100%) |
| T+0s | api-server-2 status: DOWN - Capacity exceeded: 240% (max 100%) |
| T+0s | PostgreSQL (primary) status: DOWN - Capacity exceeded: 260% (max 100%) |
| T+0s | Redis (cache) status: DOWN - Capacity exceeded: 220% (max 100%) |
| T+0s | RabbitMQ status: DOWN - Capacity exceeded: 200% (max 100%) |

## 4. Root Cause Analysis


The initial failure cascaded through the dependency graph, causing 6 components to go DOWN. This indicates insufficient isolation between services.


A 10.0x traffic spike amplified the impact of the underlying failure.

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

## 8. Action Items

| ID | Description | Owner | Priority | Category | Status |
|-----|-------------|-------|----------|----------|--------|
| INC-4A56C94A-001 | Enable failover configuration for nginx (LB) | SRE Team | P1 | mitigation | open |
| INC-4A56C94A-003 | Implement circuit breaker pattern on nginx (LB) -> api-server-1 dependency | SRE Team | P1 | mitigation | open |
| INC-4A56C94A-004 | Enable failover configuration for api-server-1 | SRE Team | P1 | mitigation | open |
| INC-4A56C94A-006 | Implement circuit breaker pattern on nginx (LB) -> api-server-2 dependency | SRE Team | P1 | mitigation | open |
| INC-4A56C94A-007 | Enable failover configuration for api-server-2 | SRE Team | P1 | mitigation | open |
| INC-4A56C94A-009 | Implement circuit breaker pattern on api-server-1 -> PostgreSQL (primary) dependency | SRE Team | P1 | mitigation | open |
| INC-4A56C94A-010 | Implement circuit breaker pattern on api-server-2 -> PostgreSQL (primary) dependency | SRE Team | P1 | mitigation | open |
| INC-4A56C94A-011 | Enable failover configuration for PostgreSQL (primary) | SRE Team | P1 | mitigation | open |
| INC-4A56C94A-013 | Implement circuit breaker pattern on api-server-1 -> Redis (cache) dependency | SRE Team | P1 | mitigation | open |
| INC-4A56C94A-014 | Implement circuit breaker pattern on api-server-2 -> Redis (cache) dependency | SRE Team | P1 | mitigation | open |
| INC-4A56C94A-015 | Enable failover configuration for Redis (cache) | SRE Team | P1 | mitigation | open |
| INC-4A56C94A-017 | Implement circuit breaker pattern on api-server-1 -> RabbitMQ dependency | SRE Team | P1 | mitigation | open |
| INC-4A56C94A-018 | Implement circuit breaker pattern on api-server-2 -> RabbitMQ dependency | SRE Team | P1 | mitigation | open |
| INC-4A56C94A-019 | Enable failover configuration for RabbitMQ | SRE Team | P1 | mitigation | open |
| INC-4A56C94A-002 | Add health check monitoring for nginx (LB) | SRE Team | P2 | detection | open |
| INC-4A56C94A-005 | Add health check monitoring for api-server-1 | SRE Team | P2 | detection | open |
| INC-4A56C94A-008 | Add health check monitoring for api-server-2 | SRE Team | P2 | detection | open |
| INC-4A56C94A-012 | Add health check monitoring for PostgreSQL (primary) | SRE Team | P2 | detection | open |
| INC-4A56C94A-016 | Add health check monitoring for Redis (cache) | SRE Team | P2 | detection | open |
| INC-4A56C94A-020 | Add health check monitoring for RabbitMQ | SRE Team | P2 | detection | open |

## 9. Lessons Learned

- High blast radius indicates insufficient fault isolation. Consider implementing bulkhead patterns and circuit breakers to contain failures.
- No circuit breakers were in place to stop cascade propagation. Implementing the circuit breaker pattern is a high-priority improvement.

---
*This post-mortem was auto-generated by FaultRay. It follows blameless post-mortem principles: focus on systems, not people.*