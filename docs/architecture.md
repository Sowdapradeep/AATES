# AATES Foundation Architecture Guide

## System Topology
AATES (Autonomous AI Tamil Entertainment Studio) is structured as a **Modular Monolith**. It runs as a single process for simple orchestration but enforces strict code boundaries by forcing all inter-module communication to pass through the Event Bus or Runtime Layer.

```text
  [ Next.js Dashboard Client ]
               │ (HttpOnly JWT Cookies)
               ▼
      [ FastAPI Web Engine ] ──► [ Runtime Layer (Orchestration) ]
               │                                │
               ▼                                ▼
     [ PostgreSQL Database ]         [ Pluggable Providers ]
                                     (S3, LLM, EventBus, Scheduler)
```

## Core Modules & Abstractions
1. **Runtime Layer (`runtime/`)**: acts as the platform operating system. Dynamic components inherit lifecycle controls and run inside isolated context wrappers.
2. **Contracts (`contracts/`)**: houses abstract schemas, payload interfaces, and DTO definitions. No two modules may share raw internal models.
3. **Providers (`providers/`)**: agnostic adapters wrapping external vendor tools (LLM interfaces, S3 objects APIs, APScheduler).
4. **Domains (`domains/`)**: localized business definitions representing users, stories, universes, and publishers.

## Database Schemas
All tables are registered on SQLAlchemy 2.0 schemas:
- **Authentication**: Users, Roles, Permissions, user_roles, role_permissions.
- **Workflow & Schedulers**: Jobs, SystemStates, FeatureFlags, WorkflowDefinitions, WorkflowExecutions.
- **Asset Trackers**: Assets, Budgets, ProviderCosts, EpisodeCosts, DailyCosts, MonthlyCosts.
- **Production Pipelines**: ProductionQueue, ProductionTasks, ProductionHistories.
- **Agent Decision Audits**: DecisionLogs, DecisionReasons, DecisionConfidences.
