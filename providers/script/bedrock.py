import json
import logging
from typing import Any
from providers.script.interface import ScriptProvider
from providers.registry import provider_registry
from core.config.settings import settings

logger = logging.getLogger("bedrock_script")

class BedrockScriptProvider(ScriptProvider):
    """Production AWS Bedrock Script Provider using bedrock-runtime Converse API."""

    @property
    def name(self) -> str:
        return "BedrockScript"

    def __init__(self) -> None:
        self.llm = provider_registry.select_provider("llm", required_capabilities=["text_generation"])

    async def generate(self, knowledge_package: dict[str, Any], platform: str, language: str) -> dict[str, Any]:
        # Build platform template specifications
        platform_spec = "Short vertical video format, length strictly under 60 seconds. High pacing."
        if "shorts" in platform.lower():
            platform_spec = "YouTube Shorts vertical format, target duration 45-60 seconds. High energy."
        elif "reels" in platform.lower():
            platform_spec = "Instagram Reels format, target duration 30-90 seconds. Highly engaging and visual."
        elif "longform" in platform.lower():
            platform_spec = "YouTube Long-form horizontal format, target duration 5-20 minutes. Comprehensive and informational."

        system_prompt = (
            "You are a World-Class AI Script Writer. Your goal is to write a highly compelling, creative script "
            "based on a provided Knowledge Package. You must output ONLY a valid JSON document matching the requested schema. "
            "Do not include free-form explanations or markdown wraps."
        )

        user_prompt = f"""Generate a production-ready script for topic: "{knowledge_package.get('topic')}" based on this Knowledge Package details:

Summary: {knowledge_package.get('summary')}
Keywords: {knowledge_package.get('keywords')}
Audience: {knowledge_package.get('audience')}
Pain Points: {knowledge_package.get('pain_points')}
Statistics: {knowledge_package.get('statistics')}
Story Outline: {knowledge_package.get('story_structure')}
Visual Ideas: {knowledge_package.get('visual_ideas')}

Platform Template Specifications: {platform_spec}
Target Language: {language} (use correct locale and idioms).

Respond with a JSON object that satisfies this exact schema:
{{
  "title": "A highly catchy title for the target platform",
  "estimated_duration_sec": 45.0,
  "word_count": 140,
  "reading_time_sec": 45.0,
  "hook": "Intense grabber sentence",
  "opening": "Opening segment introduction",
  "problem": "Clear elaboration of audience paint points",
  "story": "Story narration / engagement case study",
  "solution": "Core solution presentation",
  "cta": "Strong call to action",
  "narration": "Full combined voice narration string",
  "scene_breakdown": [
    {{
      "scene_number": 1,
      "duration": 10.0,
      "narration": "Voiceover narration script for this scene",
      "visual_prompt": "Prompt for text-to-image or video generation",
      "camera_angle": "Camera directions, e.g. Close Up, Zooming Pan",
      "background": "Scene setting background description",
      "emotion": "Dominant scene emotional feel",
      "onscreen_text": "Onscreen overlay text",
      "transition": "Transition instructions, e.g. Fade out, quick cut",
      "b_roll": "Secondary b-roll footage description",
      "sound_effects": ["Sound effects to play, e.g. Swoosh, digital chime"]
    }}
  ],
  "thumbnail_prompt": "Prompt description for generating the thumbnail image",
  "description": "Video description text for platform uploads",
  "tags": ["tag1", "tag2"],
  "hashtags": ["#hashtag1", "#hashtag2"]
}}"""

        response_text = await self.llm.generate(system_prompt=system_prompt, user_prompt=user_prompt, temperature=0.3, capability="story")
        return self._clean_and_parse_json(response_text)

    async def review(self, script_data: dict[str, Any], platform: str) -> dict[str, Any]:
        system_prompt = (
            "You are a Senior Video Director and Editor. Evaluate the provided video script "
            "against production-grade metrics. Respond ONLY with a valid JSON document matching the requested schema."
        )

        user_prompt = f"""Review this script:
{json.dumps(script_data, indent=2)}

Platform: {platform}

Respond with a JSON object that satisfies this exact schema:
{{
  "overall_score": 0.85,
  "hook_score": 0.90,
  "story_score": 0.80,
  "cta_score": 0.85,
  "seo_score": 0.88,
  "retention_score": 0.75,
  "platform_score": 0.90,
  "grammar_score": 0.95,
  "consistency_score": 0.85,
  "suggestions": [
    "Identify weak sections or sentences that need improvements.",
    "Specifically mention which scene or segment is weak."
  ]
}}"""

        response_text = await self.llm.generate(system_prompt=system_prompt, user_prompt=user_prompt, temperature=0.2, capability="story")
        return self._clean_and_parse_json(response_text)

    async def improve(self, script_data: dict[str, Any], review_report: dict[str, Any], platform: str) -> dict[str, Any]:
        system_prompt = (
            "You are an expert Script Optimizer. Regenerate and improve ONLY the weak sections highlighted "
            "in the review report, merging them back into the main script structure. Respond ONLY with a valid JSON script."
        )

        user_prompt = f"""Optimize this script:
{json.dumps(script_data, indent=2)}

Based on these review suggestions:
{json.dumps(review_report, indent=2)}

Platform: {platform}

Respond with the updated script satisfying the script generation JSON schema structure exactly."""

        response_text = await self.llm.generate(system_prompt=system_prompt, user_prompt=user_prompt, temperature=0.3, capability="story")
        return self._clean_and_parse_json(response_text)

    def _clean_and_parse_json(self, raw_text: str) -> dict[str, Any]:
        clean_text = raw_text.strip()
        if "```json" in clean_text:
            clean_text = clean_text.split("```json")[1].split("```")[0].strip()
        elif "```" in clean_text:
            clean_text = clean_text.split("```")[1].split("```")[0].strip()
        
        try:
            return json.loads(clean_text)
        except Exception as e:
            logger.error(f"Failed to parse JSON output: {str(e)}. Original text: {raw_text}")
            raise e
