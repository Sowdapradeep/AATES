# ADR-006: Scheduler Abstraction

## Status
Approved

## Context
AATES requires executing recurring production cycles, budget checks, and publishing sweeps according to cron schedules.

## Decision
Define an abstract `SchedulerProvider` interface. The foundation exposes an APScheduler implementation, which stores task status and history in the database.

## Alternatives
- **Celery Beat**: Rejected due to high setup complexity.

## Consequences
- Simple scheduling configuration.
- Business logic is isolated from scheduler internals.

## Future Migration Path
Migrate to AWS EventBridge or Temporal cron triggers.
