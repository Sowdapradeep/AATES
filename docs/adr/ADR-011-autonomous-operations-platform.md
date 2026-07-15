# ADR-011: Autonomous Operations Platform Loop

## Status
Approved

## Context
Standard AI automation scripts blindly publish assets without checking engagement performance or closing the feedback loop. To achieve true autonomy, AATES must model a closed-loop business management system:
`Think ──► Create ──► Produce ──► Publish ──► Measure ──► Learn ──► Improve ──► Think Again`.

We must also enforce a strict separation of concerns: the Publishing layer must never generate media, and the Production Studio must never upload media.

## Decision
We will model the Operations Layer (Master Prompt 4) as a closed-loop business optimizer managing the lifecycle of the Master Reel:

```text
       [ Master Reel ]
              │
              ▼
     [ Operations Engine ]  ◄── (Manage Release Calendar & Queue States)
              │
              ▼
     [ Publisher Adapters ] ──► Upload to Instagram Reels & YouTube Shorts
              │
              ▼
    [ Analytics Engine ]    ──► Collect views, watch time, and engagement metrics
              │
              ▼
    [ Learning Loop ]       ──► Feed back to CEO Agent to update Story Bible rules
```

### Components
1.  **Operations Engine**: Handles release schedules, queue management (Pause, Resume, Retry), and monitoring.
2.  **Publisher Engine**: Relies on abstract interfaces (`PublishProvider`) for Instagram Reels and YouTube Shorts. Consumes only the completed Master Reel S3 paths; it never performs media editing or compilation.
3.  **Analytics Engine**: Collects performance logs (views, retention rates) and translates them into performance scores.
4.  **Learning & Optimization Loop**: Feeds performance metrics to the CEO agent. The CEO makes strategic decisions (e.g. "Increase comedy rating," "Reduce duration by 10s") and updates the Story Bible rules, closing the loop.

## Consequences
*   **Zero Coupling**: The Production Studio remains entirely media-independent. It terminates at the compilation of the Master Reel. The Operations layer handles distribution independently.
*   **Adaptive Intelligence**: Audience trends autonomously guide narrative direction without manual user intervention.
