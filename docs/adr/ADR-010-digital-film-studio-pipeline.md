# ADR-010: Digital Film Studio Pipeline

## Status
Approved

## Context
Standard AI video generation systems wrap prompts and hit API endpoints to produce short clips directly from text. This approach is unpredictable, lacks audio-visual synchronization, and fails to maintain continuity across scene cuts. To achieve cinematic coherence, AATES must model a Pixar/Marvel-style Digital Film Studio pipeline instead of a basic wrapper.

## Decision
We will structure the Production Studio (Master Prompt 3) as a multi-stage compilation pipeline consuming the `ProductionBlueprint` and producing a final `Master Reel`:

```text
    [ Production Blueprint ]
               │
               ▼
     ( 1. Pre-production )  ──► Storyboard Frames & Voice Casting
               │
               ▼
     ( 2. Production )      ──► Video segments, Dialogue voice tracks, Music & SFX
               │
               ▼
     ( 3. Post-production ) ──► SRT Subtitles, Audio-Video Mixing (FFmpeg)
               │
               ▼
       [ Master Reel ]      ──► Complete MP4 Episode asset
```

### Pipeline Details
1.  **Pre-production**:
    *   *Storyboarder*: Generates frame reference images for each scene.
    *   *Casting*: Assigns voice profile models (e.g., ElevenLabs IDs) to characters.
2.  **Production**:
    *   *Video Render*: Translates storyboards and camera scripts into video segments.
    *   *Voice Render*: Synthesizes dialogue text into separate character audio tracks.
    *   *Soundtrack Render*: Generates background music and ambient SFX tracks.
3.  **Post-production**:
    *   *Subtitle Synthesizer*: Compiles dialogue timing logs into standard SRT tracks.
    *   *FFmpeg Mixer*: Runs layout compilation scripts to combine video files, overlay subtitle tracks, and mix background music, dialogue, and sound effects.

## Consequences
*   **Decoupled Rendering**: Swapping external providers (e.g., Kling to Runway, ElevenLabs to OpenAI Audio) only requires updating respective provider classes; the core pipeline and FFmpeg assembly configurations remain unchanged.
*   **Timeline Continuity**: Because storyboard frames are generated first, they act as visual anchors, ensuring clothing, props, and face maps remain consistent.
*   **Precise Syncing**: Audio mixing is frame-accurate, avoiding drift between character speech and lip movements.
