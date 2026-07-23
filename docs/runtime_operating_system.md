# Phase 12 — Autonomous Runtime Operating System (AROS)

## Overview

Phase 12 transforms AATES from a triggered workflow application into a **continuously running Autonomous Runtime Operating System**. After boot, AROS requires no human prompts, no manual scheduling, and no manual workflow execution. It observes, thinks, plans, executes, learns, and improves — in an infinite loop.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                       StudioRuntime                         │
│                   (AROS Operating Kernel)                   │
│                                                             │
│   ┌──────────────┐    ┌───────────────────────────────┐    │
│   │   EventBus   │    │     ContinuousRuntimeLoop      │    │
│   └──────────────┘    │  Observe → Think → Plan        │    │
│                        │  Schedule → Execute → Review  │    │
│   ┌──────────────┐    │  Learn → Optimize → Sleep      │    │
│   │  Telemetry   │    └───────────────────────────────┘    │
│   └──────────────┘                                          │
│                        ┌───────────────────────────────┐    │
│   ┌──────────────┐    │    AutonomousScheduler         │    │
│   │  Supervisor  │    │  Time / Goal / Event /         │    │
│   │ (self-heal)  │    │  Budget / Resource / Retry     │    │
│   └──────────────┘    └───────────────────────────────┘    │
│                                                             │
│   ┌──────────────┐    ┌───────────────────────────────┐    │
│   │   Worker     │    │    DistributedQueue            │    │
│   │   Runtime    │    │  Priority / Retry /            │    │
│   │  7 Workers   │    │  Dead-Letter / Ack / Delayed   │    │
│   └──────────────┘    └───────────────────────────────┘    │
│                                                             │
│   ┌──────────────────────────────────────────────────┐    │
│   │              Autonomy Layer (Phase 11)            │    │
│   │   DecisionEngine / MissionEngine / GoalEngine    │    │
│   │   WorldModel / StrategicMemory / LifelongMemory  │    │
│   └──────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

---

## Boot Sequence

`StudioRuntime.boot()` initialises all subsystems in dependency order:

| Step | Subsystem | Description |
|---|---|---|
| 1 | Configuration | Load settings from `core.config` |
| 2 | Memory | WorldModel, StrategicMemory, LifelongMemory |
| 3 | Autonomy | DecisionEngine, MissionEngine, GoalEngine |
| 4 | Providers | Amazon Bedrock warm-up |
| 5 | Queue | DistributedQueue connect (Redis / memory) |
| 6 | Workers | Start all 7 long-running workers |
| 7 | Scheduler | AutonomousScheduler init |
| 8 | EventBus | Async pub/sub init |
| 9 | Telemetry | RuntimeTelemetry init |
| 10 | Supervisor | RuntimeSupervisor init |
| 11 | TriggerEngine | AutonomousTriggerEngine init |

---

## Continuous Runtime Loop

**File**: [`runtime/continuous_loop.py`](../runtime/continuous_loop.py)

The loop runs forever at a configurable tick rate (default 60s):

```
Observe    → Collect WorldModel snapshot, queue depths, worker status
Think      → Run DecisionEngine processing cycle
Plan       → AutonomousTriggerEngine evaluates mission/budget/capacity
Schedule   → Push approved productions to AutonomousScheduler
Execute    → Workers pull jobs autonomously (no explicit call needed)
Review     → Executive Council reviews completed episodes
Learn      → LearningEngine digests episode outcomes
Optimize   → ProductionOptimizer, ModelEvolution run
Sleep      → Wait tick_sec seconds
```

---

## Components

### StudioRuntime
**File**: [`runtime/studio_runtime.py`](../runtime/studio_runtime.py)  
The AROS operating kernel. Single boot point. Manages lifecycle, shutdown, and status.

### AutonomousScheduler
**File**: [`runtime/autonomous_scheduler.py`](../runtime/autonomous_scheduler.py)  
Budget-aware, resource-aware scheduler. Supports:
- **Time-based**: recurring interval scheduling
- **Goal-based**: productions driven by active goals
- **Event-based**: milestone/universe events
- **Retry scheduling**: exponential backoff (30s / 120s / 600s)
- **Delayed scheduling**: run_after timestamp

### GoalDispatcher
**File**: [`runtime/goal_dispatcher.py`](../runtime/goal_dispatcher.py)  
Converts mission goals to executable `WorkflowSpec` objects:
`Mission → Goal → Objective → Workflow → Episode → Scene → Task`

### WorkflowRuntime
**File**: [`runtime/workflow_runtime.py`](../runtime/workflow_runtime.py)  
Every workflow executes independently with full lifecycle control:
- `pause()` / `resume()` — suspend without losing state
- `cancel()` — graceful termination
- `restart()` — full reset from checkpoint
- Checkpoint on every step completion
- Timeout guard (default 5 min)
- Replay log for every step

### EpisodeRuntime
**File**: [`runtime/episode_runtime.py`](../runtime/episode_runtime.py)  
Isolated episode environment. Owns: story, memory, budget, assets, production queue, quality state. Failure in one episode **never** impacts another.

### UniverseRuntime / UniverseRegistry
**File**: [`runtime/universe_runtime.py`](../runtime/universe_runtime.py)  
Each universe owns: Story Bible, characters, memories, goals, budget, assets, analytics. Universes evolve independently via the `evolve(directive)` API.

### WorkerRuntime
**File**: [`runtime/worker_runtime.py`](../runtime/worker_runtime.py)  
7 long-running workers that stay alive continuously:

| Worker | Processes |
|---|---|
| ImageWorker | Image generation tasks |
| VideoWorker | Video assembly tasks |
| VoiceWorker | Voice generation tasks |
| MusicWorker | Music generation tasks |
| PublishingWorker | Publishing pipeline tasks |
| AnalyticsWorker | Analytics ingestion tasks |
| LearningWorker | Learning pipeline tasks |

### DistributedQueue
**File**: [`runtime/distributed_queue.py`](../runtime/distributed_queue.py)  
Priority queue with Redis Streams interface:
- Priority 0–10 (higher = first)
- Automatic retries with exponential backoff
- Dead-letter queue for exhausted retries
- Delayed jobs (run_after timestamp)
- Explicit ack/nack acknowledgements
- Future: Amazon SQS, Amazon EventBridge

### RuntimeCheckpoints
**File**: [`runtime/runtime_checkpoints.py`](../runtime/runtime_checkpoints.py)  
Persistent workflow checkpoints. Stores: step, assets, budget, decision, memory, queue position. On restart, execution resumes from the saved step. **Completed work is never regenerated.**

### RuntimeSupervisor
**File**: [`runtime/runtime_supervisor.py`](../runtime/runtime_supervisor.py)  
Self-healing supervisor. Detects and auto-recovers:
- Crashed worker tasks → automatic restart
- Workers with excessive errors → restart + counter reset
- Dead-letter queue growth → alert
- Bedrock provider outage → alert

### AutonomousTriggerEngine
**File**: [`runtime/autonomous_trigger_engine.py`](../runtime/autonomous_trigger_engine.py)  
The CEO never waits for a prompt. Each cycle evaluates mission, goals, budget, and capacity to determine whether new productions should start. No human interaction.

### EventBus
**File**: [`runtime/event_bus.py`](../runtime/event_bus.py)  
Async pub/sub bus decoupling runtime components. Designed for migration to Amazon EventBridge.

### RuntimeTelemetry
**File**: [`runtime/runtime_telemetry.py`](../runtime/runtime_telemetry.py)  
Tracks: CPU, memory, queue depth, workers, Bedrock calls, Bedrock latency, AWS costs, episodes produced, publish count, quality trends.

---

## API Routes

**Router**: [`apps/api/v1/runtime.py`](../apps/api/v1/runtime.py) — Prefix: `/v1/runtime`

| Route | Method | Description |
|---|---|---|
| `/status` | GET | Full AROS runtime status and uptime |
| `/workers` | GET | Worker pool status (7 workers) |
| `/workers/{type}/restart` | POST | Manually restart a worker |
| `/queues` | GET | Distributed queue status |
| `/queues/push` | POST | Push a job manually |
| `/checkpoints` | GET | List all workflow checkpoints |
| `/checkpoints/{id}` | GET | Get a specific checkpoint |
| `/scheduler` | GET | Scheduler status and upcoming jobs |
| `/replay` | POST | Replay a workflow from checkpoint |
| `/supervisor` | GET | Supervisor events and restarts |
| `/supervisor/health-check` | POST | Trigger a health check |
| `/metrics` | GET | Live runtime telemetry |

---

## Test Coverage

**File**: [`tests/test_runtime.py`](../tests/test_runtime.py) — **37 tests**

| Test | Component |
|---|---|
| `test_studio_runtime_instantiation` | StudioRuntime |
| `test_studio_runtime_status_before_boot` | StudioRuntime |
| `test_continuous_loop_one_tick` | ContinuousRuntimeLoop |
| `test_scheduler_schedule_and_drain` | AutonomousScheduler |
| `test_scheduler_budget_guard` | AutonomousScheduler |
| `test_scheduler_retry_with_backoff` | AutonomousScheduler |
| `test_goal_dispatcher_converts_goals` | GoalDispatcher |
| `test_workflow_runtime_execution` | WorkflowRuntime |
| `test_workflow_pause_resume` | WorkflowRuntime |
| `test_workflow_cancel` | WorkflowRuntime |
| `test_workflow_checkpoint` | WorkflowRuntime |
| `test_workflow_replay_log` | WorkflowRuntime |
| `test_episode_runtime_isolation` | EpisodeRuntime |
| `test_episode_runtime_budget_guard` | EpisodeRuntime |
| `test_universe_runtime_isolation` | UniverseRuntime |
| `test_universe_registry` | UniverseRegistry |
| `test_universe_character_retirement` | UniverseRuntime |
| `test_worker_runtime_all_workers_start` | WorkerRuntime |
| `test_worker_runtime_restart` | WorkerRuntime |
| `test_distributed_queue_priority_ordering` | DistributedQueue |
| `test_distributed_queue_ack` | DistributedQueue |
| `test_distributed_queue_nack_retry` | DistributedQueue |
| `test_distributed_queue_dead_letter` | DistributedQueue |
| `test_checkpoint_save_and_load` | RuntimeCheckpoints |
| `test_checkpoint_resume_never_regenerates` | RuntimeCheckpoints |
| `test_supervisor_health_check_runs` | RuntimeSupervisor |
| `test_supervisor_detects_dead_letter` | RuntimeSupervisor |
| `test_trigger_engine_generates_production` | AutonomousTriggerEngine |
| `test_event_bus_publish_subscribe` | EventBus |
| `test_telemetry_snapshot` | RuntimeTelemetry |
| `test_runtime_status_endpoint` | API |
| `test_runtime_workers_endpoint` | API |
| `test_runtime_queues_endpoint` | API |
| `test_runtime_checkpoints_endpoint` | API |
| `test_runtime_scheduler_endpoint` | API |
| `test_runtime_supervisor_endpoint` | API |
| `test_runtime_metrics_endpoint` | API |

---

## Deployment

To start AROS as a standalone process:

```python
import asyncio
from runtime.studio_runtime import studio_runtime

asyncio.run(studio_runtime.boot())
```

AROS boots, starts all workers, then enters the perpetual loop. It never stops unless sent `SIGINT` or `SIGTERM`.

The FastAPI application exposes the runtime via `/v1/runtime/*` endpoints — accessible to the dashboard without connecting directly to the runtime process.

---

## Test Results

```
python -m pytest tests/
104 passed, 160 warnings in ~30s
```

All tests pass. Full backward compatibility maintained. Zero regressions.
