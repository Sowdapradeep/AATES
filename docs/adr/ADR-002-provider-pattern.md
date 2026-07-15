# ADR-002: Vendor-Agnostic Provider Pattern

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
