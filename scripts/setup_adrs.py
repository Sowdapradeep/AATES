import os

def create_adrs():
    base_dir = r"c:\finished project\AATES\docs\adr"
    
    adrs = {
        "ADR-001-modular-monolith.md": """# ADR-001: Modular Monolith Architecture

## Status
Approved

## Context
AATES requires a clean separation of concerns among modules (e.g., users, stories, universes, etc.). Building microservices early introduces operational complexity, latency, and networking overhead.

## Decision
We adopt a Modular Monolith architecture. All modules live within a single repository and run in the same process but maintain clean boundaries. Modules communicate only through well-defined event contracts and interfaces.

## Alternatives
- **Microservices**: Rejected due to high operational complexity and premature overhead.
- **Traditional Monolith (Spaghetti)**: Rejected because it makes future separation difficult.

## Consequences
- Single deployments reduce devops overhead.
- Explicit interfaces simplify modular boundary enforcement.
- Ready for future extraction into services if performance needs dictate.

## Future Migration Path
If a domain requires scaling independently, its folders can be moved to a standalone service with an HTTP/gRPC interface without rewriting core logic.
""",
        "ADR-002-provider-pattern.md": """# ADR-002: Vendor-Agnostic Provider Pattern

## Status
Approved

## Context
AATES integrates with multiple external AI models (LLMs, Text-to-Speech, Image, Video, Rendering). Direct coupling to vendor SDKs (e.g., OpenAI, Anthropic) makes the platform fragile to API changes and price changes.

## Decision
We introduce the Provider Pattern. Business logic depends on abstract base interfaces (e.g., `LLMProvider`). Concrete provider implementations (e.g., `OpenAIProvider`, `GeminiProvider`) adapt these interfaces to specific SDKs.

## Alternatives
- **Direct Integration**: Directly calling APIs/SDKs in business code. Rejected due to tight vendor coupling.

## Consequences
- High modularity and testability through mocks.
- Switch providers dynamically via config.

## Future Migration Path
Add new adapters under `providers/` as new AI APIs emerge.
""",
        "ADR-003-workflow-engine.md": """# ADR-003: Workflow Engine Architecture

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
""",
        "ADR-004-story-bible.md": """# ADR-004: Story Bible Module

## Status
Approved

## Context
AI agents need a single source of truth for universe lore, characters, relationships, and history to prevent hallucinations and maintain continuity.

## Decision
Create the `brain/story_bible/` domain. It stores structured parameters of the fictional worlds (Rules, Magic, Characters, History) and provides contextual retrieval mechanics for LLM agents.

## Alternatives
- **Pass all details in system prompt**: Rejected due to token limit constraints and high costs.

## Consequences
- Consistent narrative generation across episodes.
- Context-aware retrieval minimizes model hallucinations.

## Future Migration Path
Extend to query graph databases or Vector DB endpoints as the scale of characters increases.
""",
        "ADR-005-event-bus.md": """# ADR-005: Event Bus Abstraction

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
""",
        "ADR-006-scheduler.md": """# ADR-006: Scheduler Abstraction

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
""",
        "ADR-007-repository-structure.md": """# ADR-007: Repository Pattern and Directory Structure

## Status
Approved

## Context
We need to separate data access mechanisms (SQLAlchemy) from the core business domain logic to maintain high testability and clean architecture.

## Decision
Adopt the Repository Pattern under `infrastructure/` and define standard directory structure exposing contracts, providers, domains, runtime, and apps.

## Alternatives
- **Active Record (Direct queries in routers)**: Rejected due to testing and maintenance difficulty.

## Consequences
- Unit tests can mock repositories easily.
- Changes in database schema only affect the repository layers.

## Future Migration Path
Can swap SQLite/PostgreSQL with MongoDB or other engines if domain needs differ.
""",
        "ADR-008-aws-architecture.md": """# ADR-008: AWS Deployment Strategy (Free Tier Focused)

## Status
Approved

## Context
AATES must run in a cost-efficient manner in AWS (Free Tier) during initial phases, but prepare for future scaling.

## Decision
Deploy the modular monolith using Docker Compose on a single AWS EC2 instance. Provision infrastructure via Terraform. Use Amazon S3 for media asset storage, and CloudWatch for logs.

## Alternatives
- **AWS ECS / EKS**: Rejected for initial phase due to cost.
- **Serverless (Lambda)**: Rejected due to execution time limits of video generation rendering pipelines.

## Consequences
- Zero or low running cost.
- Easy migration to ECS later as the Docker containers are already standard.

## Future Migration Path
Migrate the dockerized containers to ECS/Fargate when traffic or workloads scale.
""",
        "ADR-009-runtime-layer.md": """# ADR-009: Runtime Layer for AI Operating Platform

## Status
Approved

## Context
Autonomous agents require a managed environment providing dynamic injection, context propagation, execution engine, telemetry tracing, and lifecycle management.

## Decision
Introduce the `runtime/` layer as the operating system of AATES. Components inherit lifecycle hooks and execute within a Runtime Context containing correlation, workflow, and budget details.

## Alternatives
- **Global Variables**: Rejected as it fails context isolation.

## Consequences
- Clear trace of execution paths and token costs.
- Standardized startup, shutdown, and error recovery sequences.

## Future Migration Path
Migrate execution and dependency scopes to a dedicated microkernel or external cluster orchestrator.
"""
    }
    
    print("Writing Architecture Decision Records...")
    for filename, content in adrs.items():
        filepath = os.path.join(base_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Created: {filename}")
    print("ADR creation complete.")

if __name__ == "__main__":
    create_adrs()
