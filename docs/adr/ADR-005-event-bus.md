# ADR-005: Event Bus Abstraction

## Status
Approved

## Context
Internal communication between modular monolith components should be async-first and event-driven to maintain loose coupling.

## Decision
Define an abstract `EventBus` class. Implement standard MemoryEventBus (in-process asyncio queues) for local execution, and RedisEventBus for clustered worker execution.

## Alternatives
- **Direct Method Invocation**: Rejected as it couples components.

## Consequences
- Publishers do not need to know who listens to their events.
- Decoupled modules ease horizontal scaling.

## Future Migration Path
Implement Amazon SQS or RabbitMQ EventBus implementations by extending `EventBus`.
