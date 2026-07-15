# AATES Cognitive Engine Design Specification

This document details the architectural layout, organizational model, agent contracts, and planning workflows for the AATES AI Brain (Executive Council).

---

## 1. The Executive Council Organizational Model

Rather than a single centralized actor, AATES is governed by an **Executive Council** of specialized directors, each supervising dedicated execution departments.

```text
                        ┌───────────────────┐
                        │ Executive Council │
                        └─────────┬─────────┘
      ┌──────────────┬────────────┼───────────┬──────────────┐
      ▼              ▼            ▼           ▼              ▼
   [ CEO ]      [ Creative ] [ Production ] [ Business ] [ Technology ]
                    │            │
                    ▼            ▼
     ┌──────────────┴──────┐  ┌──┴──────────────────┐
     ▼                     ▼  ▼                     ▼
[ Departments ]         [ Story, Character,  [ Universe, Review,
                         Dialogue ]           Publishing ]
```

### Council Roles & Responsibilities
1.  **CEO (Chief Executive Officer)**:
    *   *Responsibility*: Governs overall platform execution, production queues, and season scheduling.
    *   *Supervises*: All Departments via high-level workflow definitions.
2.  **Creative Director**:
    *   *Responsibility*: Protects universe continuity, tone, and character arcs.
    *   *Supervises*: Story Department, Character Department, Dialogue Department.
3.  **Production Director**:
    *   *Responsibility*: Controls assets generation, rendering speeds, and rendering workers.
    *   *Supervises*: Universe Department, Review Department.
4.  **Business Director**:
    *   *Responsibility*: Controls costs, monitors model prices, and manages budgets (Budget Engine).
5.  **Technology Director**:
    *   *Responsibility*: Monitors model capabilities, telemetry latencies, and plugin states (Runtime Layer).
6.  **Analytics Director**:
    *   *Responsibility*: Evaluates viewer trends, comments, and publish schedules.
    *   *Supervises*: Publishing Department.

---

## 2. Standard Agent Contract Template

Every AI agent in AATES must align with the following contract block structure:

| Parameter | Specification | Description |
| :--- | :--- | :--- |
| **Mission** | Core operational goal | The primary objective the agent aims to achieve. |
| **Scope** | Boundaries of execution | Limits on what the agent can modify or decide. |
| **Inputs** | Required data contexts | The schemas, parameters, or states needed to run. |
| **Outputs** | Produced data artifacts | The exact contract schemas or files generated. |
| **Memory Access** | Read/write permissions | Access rules to short-term, episodic, or Story Bible tables. |
| **Decision Power**| Autonomous authorization | Limits of actions the agent can trigger without review. |
| **KPIs** | Performance metrics | CPU, latency, cost, and quality scores metrics. |

---

## 3. Memory & Story Bible Architecture

### Memory Strategy
-   **Short-Term Memory**: Ephemeral thread state passed inside the `RuntimeContext` for the active step execution.
-   **Long-Term Memory**: Lore, histories, and stylistic templates retrieved semantically.
-   **Episodic Memory**: Chronicles of past scripts, summaries, and generated media assets.

### Story Bible Model
Stores the permanent truth of every creative universe, consulted by agents before generation:
*   **Characters**: Lore profiles, relationships, tone descriptions, voice/visual assets IDs.
*   **Locations**: Visual style configurations, scenery descriptions.
*   **Timeline**: Chronological history of universe events.
*   **Rules**: World logic, constraints, physical limits.

---

## 4. Planning Workflows & Decision Hierarchy

### Execution Sequences
1.  **CEO** triggers a "Produce Episode" workflow task.
2.  **Creative Director** consults the **Story Bible** and directs the **Story Department** to generate the screenplay.
3.  **Dialogue Department** translates dialogs to authentic Tamil variations.
4.  **Production Director** schedules rendering jobs via the **Universe Department**.
5.  **Review Department** critiques visual quality and continuity metrics.
6.  **CEO & Business Director** approve cost thresholds before **Publishing Department** triggers release.
