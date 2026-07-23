import os
import json
import uuid
from typing import Any, List
from providers.subtitle.interface import SubtitleProvider
from providers.subtitle.alignment import format_timestamp_srt, format_timestamp_vtt, format_timestamp_ass

class MockSubtitleProvider(SubtitleProvider):
    """Mock Subtitle Provider generating test captions, timings, and export files."""

    @property
    def name(self) -> str:
        return "MockSubtitleEngine"

    def __init__(self) -> None:
        self.output_dir = "artifacts/subtitles"
        os.makedirs(self.output_dir, exist_ok=True)

    async def generate(self, voice_pkg: Any, video_pkg: Any, options: dict[str, Any]) -> dict[str, Any]:
        scenes = []
        voice_assets = getattr(voice_pkg, "assets", []) or []

        for i, asset in enumerate(voice_assets):
            scene_num = getattr(asset, "scene_number", i + 1)
            text = getattr(asset, "narration", "") or f"Mock narration text for scene {scene_num}."
            duration_ms = getattr(asset, "duration_ms", 4000)

            words = text.split()
            w_dur = duration_ms // max(1, len(words))
            word_timings = [
                {"word": w, "start_ms": idx * w_dur, "end_ms": (idx + 1) * w_dur}
                for idx, w in enumerate(words)
            ]

            scenes.append({
                "scene_number": scene_num,
                "caption_text": text,
                "word_timings": word_timings,
                "sentence_timings": [{"sentence": text, "start_ms": 0, "end_ms": duration_ms}],
                "duration_ms": duration_ms,
                "key_phrases": [words[0]] if words else ["Sample"],
                "importance_score": 0.85
            })

        return {
            "scenes": scenes,
            "language": getattr(voice_pkg, "language", "en") or "en"
        }

    async def segment(self, text: str, word_timings: list[dict[str, Any]], options: dict[str, Any]) -> list[dict[str, Any]]:
        words = text.split()
        total_len = len(words)
        mid = max(1, total_len // 2)

        w1 = words[:mid]
        w2 = words[mid:]

        s1_text = " ".join(w1)
        s2_text = " ".join(w2) if w2 else ""

        segments = [
            {
                "segment_number": 1,
                "start_ms": 0,
                "end_ms": 2000,
                "text": s1_text,
                "words": word_timings[:mid],
                "reading_speed_wpm": 180.0,
                "reading_speed_cps": 15.0,
                "reading_speed_cpl": 20.0,
                "confidence": 0.99
            }
        ]

        if s2_text:
            segments.append({
                "segment_number": 2,
                "start_ms": 2000,
                "end_ms": 4000,
                "text": s2_text,
                "words": word_timings[mid:],
                "reading_speed_wpm": 175.0,
                "reading_speed_cps": 14.5,
                "reading_speed_cpl": 18.0,
                "confidence": 0.99
            })

        return segments

    async def optimize(self, segments: list[dict[str, Any]], style_profile: dict[str, Any]) -> list[dict[str, Any]]:
        return segments

    async def export(self, segments: list[dict[str, Any]], format_type: str, output_path: str, style_profile: dict[str, Any] = None) -> str:
        dir_name = os.path.dirname(output_path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)

        if format_type == "srt":
            lines = []
            for i, seg in enumerate(segments, 1):
                t_start = format_timestamp_srt(seg["start_ms"])
                t_end = format_timestamp_srt(seg["end_ms"])
                lines.append(f"{i}\n{t_start} --> {t_end}\n{seg['text']}\n")
            with open(output_path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))

        elif format_type == "vtt":
            lines = ["WEBVTT\n"]
            for i, seg in enumerate(segments, 1):
                t_start = format_timestamp_vtt(seg["start_ms"])
                t_end = format_timestamp_vtt(seg["end_ms"])
                lines.append(f"{i}\n{t_start} --> {t_end}\n{seg['text']}\n")
            with open(output_path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))

        elif format_type == "ass":
            with open(output_path, "w", encoding="utf-8") as f:
                f.write("[Script Info]\nTitle: AATES Mock Subtitle\n[Events]\n")

        elif format_type == "json":
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(segments, f, indent=2)

        return output_path
ZOOMING = "zoom"
