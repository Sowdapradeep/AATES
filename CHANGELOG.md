# Changelog

All notable changes to the AATES project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0-foundation] - 2026-07-15

### Added
- Complete DDD-aligned directory structure initialized with `.gitkeep` placeholders.
- 9 Architectural Decision Records (ADRs) inside `docs/adr/` capturing all foundational decisions.
- Multi-settings environment-driven configuration parser using `pydantic-settings`.
- Structured JSON logger mapping Correlation ID, Request ID, User ID, Workflow ID, Episode ID, and Universe ID.
- SQLAlchemy 2.0 schemas for 30+ tables (Access Control, Budgets, Jobs, System Map, Decisions).
- Custom SQLAlchemy SQLite compiler converting PostgreSQL `JSONB` to `JSON` for unit test compatibility.
- Pluggable provider interfaces (`StorageProvider`, `EventBus`, `SchedulerProvider`, `LLMProvider`, `RuntimeContext`, `LifecycleComponent`).
- Skeletons for OpenAI, Gemini, LocalStorage, AmazonS3Storage, MemoryEventBus, RedisEventBus, and APScheduler.
- FastAPI server setup on `/v1/` version-first routes, secure HttpOnly cookie login, and permission-based RBAC guards.
- Kubernetes-standard health checks (`/health`, `/live`, `/ready` status-aware, and `/metrics` telemetry endpoints).
- Next.js dashboard shell with App Router, custom glassmorphism styles, navigation sidebar, jobs panel, logs console, profile settings, and a node-based System Map page.
- Multi-stage Dockerfiles (`Dockerfile.api`, `Dockerfile.worker`, `Dockerfile.dashboard`) and `docker-compose.yml`.
- Terraform templates provisioning EC2, S3 assets, security groups, IAM roles, and CloudWatch.
- GitHub Actions CI workflow script.
- Local SQLite integration tests verification passing successfully (4/4 tests).
