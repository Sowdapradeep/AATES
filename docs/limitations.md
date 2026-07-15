# AATES Known Limitations & Deferred Features

This document outlines the limitations and deferred features for the **Monolith Foundation (Phase 1)**.

## 1. Database & Local Testing
- **Local SQLite Fallback**: SQLite is used for local tests (`pytest`) because Postgres is not required for logic tests. A custom compilation decorator compiles `JSONB` columns to standard SQLite `JSON` strings.
- **Alembic Postgres Dialect**: Alembic scripts are configured for PostgreSQL (using UUID and JSONB dialects). Running them against SQLite is not recommended.

## 2. Infrastructure & Docker
- **Local Docker Daemon**: The local Windows developer environment lacks a running Docker daemon. Dockerfiles and Compose files were validated for syntax and schemas, but containers have not been run locally.
- **AWS Terraform Deployment**: Terraform files validate structure, but provisioning has not been completed. This is a deferred task for the cloud build phase.

## 3. Pluggable Providers & Skeletons
- **AI Models (LLMs, Video, Voice)**: External AI services are isolated behind abstract interfaces (like `LLMProvider`). Skeletons return static mock strings.
- **AWS S3 Storage**: `AmazonS3Storage` uses console log statements. Real uploads are deferred to Phase 2.
- **Event Bus & Scheduler**: APScheduler and asyncio event buses are configured for single-process monolith queues. Multi-process clustering (Redis event bus, AWS EventBridge) is deferred.
