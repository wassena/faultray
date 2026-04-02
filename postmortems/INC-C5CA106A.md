# Post-Mortem: Cascading Failure: Triple failure: postgres + redis + rabbitmq (3 services DOWN)

**Incident ID:** INC-C5CA106A
**Severity:** SEV3
**Date:** 2026-04-02 15:10
**Duration:** ~31 minutes
**Blast Radius:** 5 components affected

## 1. Incident Summary

A simulated incident was triggered by: Triple failure: postgres + redis + rabbitmq. The incident affected 9 out of 6 infrastructure components (150% of the system). 3 component(s) went completely DOWN. 6 component(s) experienced degradation. The overall risk score for this scenario was 4.0/10.

## 2. Impact Assessment

**Components Affected:** 5 out of 6 (83% blast radius)

**Services DOWN:** PostgreSQL (primary), RabbitMQ, Redis (cache)

**Services Degraded:** api-server-1, api-server-2

**Estimated Traffic Impact:** ~83% of traffic affected. Major service disruption expected.

**Dependent Services:** 2 additional service(s) potentially experiencing degradation due to upstream failures.

## 3. Timeline of Events

| Time | Event |
|------|-------|
| T+0s | PostgreSQL (primary) failure detected: Component failure (simulated) |
| T+0s | Redis (cache) status: DOWN - Component failure (simulated) |
| T+0s | RabbitMQ status: DOWN - Component failure (simulated) |
| T+5s | api-server-1 status: DEGRADED - Dependency PostgreSQL (primary) is down, remaining replicas handling load (2 left) |
| T+5s | api-server-2 status: DEGRADED - Dependency PostgreSQL (primary) is down, remaining replicas handling load (2 left) |
| T+10s | api-server-1 status: DEGRADED - Optional dependency Redis (cache) is down |
| T+10s | api-server-2 status: DEGRADED - Optional dependency Redis (cache) is down |
| T+1m | api-server-1 status: DEGRADED - Async dependency RabbitMQ is down, queue building up |
| T+1m | api-server-2 status: DEGRADED - Async dependency RabbitMQ is down, queue building up |

## 4. Root Cause Analysis

Single point of failure in **postgres**. The component went down without adequate redundancy or failover mechanisms in place.

Single point of failure in **redis**. The component went down without adequate redundancy or failover mechanisms in place.

Single point of failure in **rabbitmq**. The component went down without adequate redundancy or failover mechanisms in place.


The initial failure cascaded through the dependency graph, causing 3 components to go DOWN. This indicates insufficient isolation between services.

## 5. Contributing Factors

- No failover configured for api-server-1
- No autoscaling on api-server-1 to absorb load
- No failover configured for Redis (cache)
- No autoscaling on Redis (cache) to absorb load
- No failover configured for PostgreSQL (primary)
- No autoscaling on PostgreSQL (primary) to absorb load
- No failover configured for RabbitMQ
- No autoscaling on RabbitMQ to absorb load
- No failover configured for api-server-2
- No autoscaling on api-server-2 to absorb load

## 6. What Went Well

- 1 component(s) remained unaffected, indicating some degree of fault isolation

## 7. What Didn't Go Well

- Blast radius was too large: 5/6 components affected (83%)
- 6 dependency edge(s) in the cascade path lacked circuit breakers

## 8. Action Items

| ID | Description | Owner | Priority | Category | Status |
|-----|-------------|-------|----------|----------|--------|
| INC-C5CA106A-001 | Implement circuit breaker pattern on api-server-1 -> PostgreSQL (primary) dependency | SRE Team | P1 | mitigation | open |
| INC-C5CA106A-002 | Implement circuit breaker pattern on api-server-2 -> PostgreSQL (primary) dependency | SRE Team | P1 | mitigation | open |
| INC-C5CA106A-003 | Enable failover configuration for PostgreSQL (primary) | SRE Team | P1 | mitigation | open |
| INC-C5CA106A-005 | Enable autoscaling for api-server-1 | Platform Team | P1 | prevention | open |
| INC-C5CA106A-007 | Enable autoscaling for api-server-2 | Platform Team | P1 | prevention | open |
| INC-C5CA106A-009 | Implement circuit breaker pattern on api-server-1 -> Redis (cache) dependency | SRE Team | P1 | mitigation | open |
| INC-C5CA106A-010 | Implement circuit breaker pattern on api-server-2 -> Redis (cache) dependency | SRE Team | P1 | mitigation | open |
| INC-C5CA106A-011 | Enable failover configuration for Redis (cache) | SRE Team | P1 | mitigation | open |
| INC-C5CA106A-017 | Implement circuit breaker pattern on api-server-1 -> RabbitMQ dependency | SRE Team | P1 | mitigation | open |
| INC-C5CA106A-018 | Implement circuit breaker pattern on api-server-2 -> RabbitMQ dependency | SRE Team | P1 | mitigation | open |
| INC-C5CA106A-019 | Enable failover configuration for RabbitMQ | SRE Team | P1 | mitigation | open |
| INC-C5CA106A-004 | Add health check monitoring for PostgreSQL (primary) | SRE Team | P2 | detection | open |
| INC-C5CA106A-006 | Add health check monitoring for api-server-1 | SRE Team | P2 | detection | open |
| INC-C5CA106A-008 | Add health check monitoring for api-server-2 | SRE Team | P2 | detection | open |
| INC-C5CA106A-012 | Add health check monitoring for Redis (cache) | SRE Team | P2 | detection | open |
| INC-C5CA106A-020 | Add health check monitoring for RabbitMQ | SRE Team | P2 | detection | open |

## 9. Lessons Learned

- High blast radius indicates insufficient fault isolation. Consider implementing bulkhead patterns and circuit breakers to contain failures.
- No circuit breakers were in place to stop cascade propagation. Implementing the circuit breaker pattern is a high-priority improvement.

---
*This post-mortem was auto-generated by FaultRay. It follows blameless post-mortem principles: focus on systems, not people.*