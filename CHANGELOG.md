# Changelog

All notable changes to the AATES project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.1-pacing-versioning] - 2026-07-15

### Added
- YAML-driven Output Profiles (`knowledge/output_profiles.yaml`) configuring Reels/Shorts aspect ratios, target resolutions, and loudness limits.
- YAML-driven Production Profiles (`knowledge/production_profiles.yaml`) configuring cinematic/thriller camera panning settings and shot frequencies.
- `SceneTimingEngine` calculating scaled scene durations within maximum target runtime limits.
- `MediaVersioningTracker` executing incremental version cloning and parent-child iteration tracking.
- `ProductionWorkflowRecovery` implementing checkpoint caching to prevent duplicate asset generation.
- Render manifest compiled specifications supporting dynamic 9:16 aspect ratio variables.

## [0.3.0-production] - 2026-07-15

### Added
- Standardized `StoryboardPanel`, `ShotPlan`, `CameraInstruction`, `CinematographySpec`, and `EnvironmentSpec` DTOs.
- Storyboard Engine, Shot Planner, Camera Director, Cinematography Engine, and Environment Planner classes.
- Provider-independent interfaces and mock adapters for Image, Video, Voice, Music, and Rendering (FFmpeg) engines.
- Parent-child self-referential asset lineage, checksum, and workflow ID columns added to the database `Asset` schema.
- Image Engine with character consistency seed-profile locks mapping.
- Dialogue voice synthesis, thematic music soundtrack, and library SFX audio generators.
- Subtitle Engine generating Tamil SRT timing files.
- `AutomatedQAEngine` running Quality Gates check loops (Visual, consistency, audio speed ratios, subtitle syntax, and profanity safety lists).
- `RenderManifestCompiler` compiling Scene Packages timelines and metadata configurations.
- `FFmpegRenderingEngine` compiling scene audio-video tracks and merging them into the final compiled Master Reel.
- FastAPI routes mounted under `/v1/production` exposing storyboard generators, TTS synthesizers, QA checkers, manifest compiling, and rendering.
- Next.js Dashboard extended with **Standardized Production Studio Dashboard** rendering queues, provider fees, storyboards, QA logs, manifestations, and lineages.
- Automated API test suite covering full production workflows passing successfully (16/16 tests).

## [0.2.1-blueprint] - 2026-07-15

### Added
- Standardized `ProductionBlueprint` and `SceneBlueprint` DTO contracts for media-independent film packages.
- `ProductionBlueprintGenerator` class compiling characters, costumes, camera intents, and slang-adapted dialogues into a standard blueprint.
- FastAPI routes mounted under `/v1/` for blueprint generation and retrieval.
- Next.js Dashboard extended with **Standardized Production Blueprint Viewer** tab rendering active scene parameters.
- Automated API test suite covering blueprint validation passing successfully.

## [0.2.0-creative] - 2026-07-15

### Added
- Standardized `AgentBase` abstract framework implementing lifecycle, context injection, and decision logging methods.
- Executive Council agents classes (CEO, Creative, Production, Technology, Analytics, Business) registered on start with the `RuntimeAgentRegistry`.
- `MemoryManager` class separating ephemeral Working memory from permanent DB state models and episodic assets registry.
- `StoryBibleEngine` class managing versioned, auditable Story Bible updates and delta change tracking records.
- `DecisionEngine` class retrieving explainability logs joined with confidence metrics.
- Universe, Character, Villain, Organization, Location, and Relationship generator engines updating the Story Bible.
- Story Arcs, Conflicts, Plot Points, Twists, and Foreshadowing engines.
- `TamilNarrativeEngine` and dialogue planners injecting regional slang vocabularies based on Knowledge templates.
- `ContinuityValidator` and `CanonValidator` checking script proposals against Story Bible rules.
- FastAPI routes mounted under `/v1/` exposing planners, decision explainability, and validation checks.
- Next.js dashboard extended with Universe Explorer, Characters list, Relationship Graph, Story Arcs, Timeline Beats, and compliance score metrics.

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
