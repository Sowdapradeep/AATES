# ADR-001: Modular Monolith Architecture

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
