# ADR-003: Workflow Engine Architecture

## Status
Approved

## Context
AATES tasks (Universe Creation, Episode Production) are long-running, multi-step asynchronous processes that need states tracked, checkpoints set, and retry capability on failure.

## Decision
We reserve a Workflow Engine structure. Workflows will be defined in a graph structure (WorkflowDefinitions) and run by an Execution Engine. Running states are stored in WorkflowExecutions with checkpoints.

## Alternatives
- **Ad-hoc Cron Scripts**: Rejected because they do not support state recovery and step-by-step audit.

## Consequences
- Full visibility into agent workflows.
- Fault-tolerant pipeline executions with state checkpoints.

## Future Migration Path
Can migrate backend orchestrator to Temporal or AWS Step Functions if scale grows.
