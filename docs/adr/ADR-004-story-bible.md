# ADR-004: Story Bible Module

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
