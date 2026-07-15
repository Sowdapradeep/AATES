# AATES Story Creation Layer (Phase 2B) Design

This document details the architectural layout, core components, and data flows of the **Story Creation Layer**, which acts as the creative IP core of AATES between Planning and Production.

---

## 1. Pipeline Topology

The Story Creation Layer converts structured creative plans into screenplays and regional Tamil dialogues:

```text
    [ Episode Planner ] (Objective & Story Beats)
            │
            ▼
    [ Screenwriter Agent ] (Generates raw screenplay scenes)
            │
            ▼
    [ Dialogue Agent ] (Applies regional Tamil slang & character voice)
            │
            ▼
    [ Continuity Agent ] (Verifies Story Bible rules & constraints)
            │
            ▼
    [ Screenplay Output DTO ] (Converts to DB schema & production inputs)
```

---

## 2. Core Components

### 2.1 Screenwriter Agent (`brain/story/writer.py`)
-   **Mission**: Draft structured screenplay scenes, actions, and raw dialogues based on planner inputs.
-   **Scope**: Screenplay composition and dramatic pacing.
-   **Inputs**: Episode Plan, Character registry.
-   **Outputs**: Raw script DTO containing scene beats and draft dialogue lines.

### 2.2 Dialogue Specialist Agent (`brain/story/dialogue.py`)
-   **Mission**: Refine script dialogues to match character backgrounds and regional Tamil variations.
-   **Scope**: Language authenticity and regional slang usage.
-   **Inputs**: Raw dialogues, Character Profiles, regional slang dictionaries (Knowledge base).
-   **Outputs**: Polished dialogues mapping local Tamil slang (e.g. Chennai, Madurai, Kongu).

### 2.3 Continuity Supervisor Agent (`brain/story/continuity.py`)
-   **Mission**: Review completed scripts to ensure strict alignment with the Story Bible.
-   **Scope**: Lore rules, entity states, location settings, and item attributes.
-   **Inputs**: Screenplay script, Story Bible rules.
-   **Outputs**: Continuity audit reports containing approval statuses or warning logs.

---

## 3. Data Schemas (DTOs)

### Screenplay DTO (`contracts/dto/screenplay.py`)
```python
from pydantic import BaseModel
from typing import Any

class DialogueLine(BaseModel):
    character_name: str
    text_tamil: str
    text_english: str
    slang_type: str  # e.g., "chennai", "madurai", "standard"
    delivery_note: str | None = None

class ScreenplayScene(BaseModel):
    scene_number: int
    location: str
    time_of_day: str  # e.g., "DAY", "NIGHT"
    action_descriptions: list[str]
    dialogues: list[DialogueLine]
    outcomes: str

class Screenplay(BaseModel):
    universe_id: str
    season: int
    episode: int
    scenes: list[ScreenplayScene]
    version: int
```
