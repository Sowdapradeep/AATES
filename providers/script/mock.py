import random
from typing import Any
from providers.script.interface import ScriptProvider

class MockScriptProvider(ScriptProvider):
    """Mock Script Provider generating structured scripts and reviews for testing."""

    @property
    def name(self) -> str:
        return "MockScript"

    async def generate(self, knowledge_package: dict[str, Any], platform: str, language: str) -> dict[str, Any]:
        topic = knowledge_package.get("topic", "General Topic")
        summary = knowledge_package.get("summary", "Topic Summary")

        # Select platform parameters
        if "short" in platform.lower() or "reel" in platform.lower():
            duration = 50.0
            word_count = 140
            scenes_count = 3
        else:
            duration = 480.0
            word_count = 1200
            scenes_count = 5

        # Create structured scene objects
        scenes = []
        for i in range(1, scenes_count + 1):
            scenes.append({
                "scene_number": i,
                "duration": round(duration / scenes_count, 1),
                "narration": f"Here is narration for scene {i} on the topic of {topic}. Summarizing details of {summary[:50]}...",
                "visual_prompt": f"Close-up high-contrast cinematic shot illustrating scene {i} details for {topic}",
                "camera_angle": random.choice(["Medium Close-Up", "Extreme Close-Up", "Wide Pan", "Tracking Pan"]),
                "background": "Futuristic neon dark theme studio room",
                "emotion": "Curious",
                "onscreen_text": f"Key takeaway {i}",
                "transition": "Smooth fade-out",
                "b_roll": "Abstract floating graphics",
                "sound_effects": ["Subtle digital sweep"]
            })

        return {
            "title": f"The Ultimate Guide to {topic}",
            "estimated_duration_sec": duration,
            "word_count": word_count,
            "reading_time_sec": round(word_count / 150.0 * 60.0, 1),
            "hook": f"Did you know this shocking secret about {topic}? Let's find out.",
            "opening": f"In today's tutorial, we are exploring {topic}.",
            "problem": f"Most creators spend hours trying to manage {topic} without finding success.",
            "story": f"Meet John, who struggled with {topic} until he automated his entire workflow.",
            "solution": "By deploying autonomous AI agents, you get complete packages in under a minute.",
            "cta": "Click the link below to get your templates now!",
            "narration": " ".join([s["narration"] for s in scenes]),
            "scene_breakdown": scenes,
            "on_screen_text": [s["onscreen_text"] for s in scenes],
            "visual_prompts": [s["visual_prompt"] for s in scenes],
            "thumbnail_prompt": f"High contrast thumbnail illustration for {topic} showing neon lights and dramatic expressions",
            "description": f"Detailed script for {topic} platform upload. References: {', '.join(knowledge_package.get('references') or [])}",
            "tags": [topic.lower(), "ai", "automation", "productivity"],
            "hashtags": [f"#{topic.replace(' ', '')}", "#ai", "#automation"],
            "metadata": {
                "model_id": "mock-llm-v1",
                "temperature": 0.3,
                "prompt_version": "v1.5",
                "generation_time_sec": 1.2
            }
        }

    async def review(self, script_data: dict[str, Any], platform: str) -> dict[str, Any]:
        # Return quality scores
        scores = {
            "overall_score": 0.85 if "short" in platform else 0.72,
            "hook_score": 0.9,
            "story_score": 0.8,
            "cta_score": 0.85,
            "seo_score": 0.88,
            "retention_score": 0.75,
            "platform_score": 0.92,
            "grammar_score": 0.95,
            "consistency_score": 0.88,
            "suggestions": ["Add more emotional hooks in scene 2", "Incorporate direct transition cues in outlines"]
        }
        return scores

    async def improve(self, script_data: dict[str, Any], review_report: dict[str, Any], platform: str) -> dict[str, Any]:
        # Perform target optimizations: update hooks or CTAs
        improved_script = dict(script_data)
        improved_script["hook"] = f"[IMPROVED] " + script_data.get("hook", "")
        improved_script["cta"] = f"[IMPROVED] " + script_data.get("cta", "")
        
        # Modify scene breakdowns with improved text
        scenes = list(improved_script.get("scene_breakdown", []))
        if len(scenes) > 1:
            scenes[1]["narration"] = f"[IMPROVED NARRATION] " + scenes[1].get("narration", "")
        improved_script["scene_breakdown"] = scenes
        return improved_script
