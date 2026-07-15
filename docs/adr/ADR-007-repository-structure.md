# ADR-007: Repository Pattern and Directory Structure

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
