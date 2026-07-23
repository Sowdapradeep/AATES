import os
import random
import uuid
from typing import Any, List
from providers.voice.interface import VoiceProvider

class MockVoiceProvider(VoiceProvider):
    """Mock Voice Provider generating simulated WAV/MP3 speech synthesis and millisecond alignments."""

    @property
    def name(self) -> str:
        return "MockVoiceAI"

    @property
    def capabilities(self) -> List[str]:
        return ["voice_cloning", "emotion_control", "tamil_support", "voice_generation"]

    def __init__(self) -> None:
        self.output_dir = "artifacts/audio"
        os.makedirs(self.output_dir, exist_ok=True)

    async def generate(self, text: str, voice_id: str, options: dict[str, Any]) -> dict[str, Any]:
        filename = f"voice_{uuid.uuid4().hex[:8]}.mp3"
        filepath = os.path.join(self.output_dir, filename)

        # Write dummy binary file to make the file real on disk
        with open(filepath, "wb") as f:
            f.write(b"ID3\x03\x00\x00\x00\x00\x00\x00" + b"MP3_MOCK_DATA" * 50)

        # Calculate word alignment timings in milliseconds
        words = text.split()
        word_alignment = []
        current_time_ms = 0
        for w in words:
            word_duration = len(w) * 80 + random.randint(30, 90)
            word_alignment.append({
                "word": w.strip(".,!?\"()"),
                "start_time_ms": current_time_ms,
                "end_time_ms": current_time_ms + word_duration,
                "confidence": round(random.uniform(0.85, 0.99), 2)
            })
            current_time_ms += word_duration + random.randint(50, 150) # gap

        total_duration_ms = current_time_ms

        return {
            "local_path": filepath,
            "storage_key": f"audio/{filename}",
            "public_url": f"https://cdn.aates.internal/audio/{filename}",
            "preview_url": f"https://cdn.aates.internal/previews/audio/{filename}",
            "duration_ms": total_duration_ms,
            "voice_id": voice_id or "narrator-male-1",
            "provider": "MockVoiceAI",
            "model": "MockSpeech-v2",
            "language": options.get("language", "en"),
            "emotion": options.get("emotion", "Narrative"),
            "speaking_style": options.get("speaking_style", "Normal"),
            "pitch": options.get("pitch", "+0%"),
            "speed": options.get("speed", "1.0x"),
            "volume": options.get("volume", "+0dB"),
            "ssml": f"<speak><prosody rate='{options.get('speed', '1.0x')}'>{text}</prosody></speak>",
            "word_alignment": word_alignment,
            "sentence_alignment": [
                {
                    "sentence": text,
                    "start_time_ms": 0,
                    "end_time_ms": total_duration_ms
                }
            ],
            "phoneme_alignment": [],
            "pause_map": {"pauses": []},
            "generation_duration_sec": 0.38,
            "quality_score": round(random.uniform(0.75, 0.98), 2)
        }

    async def regenerate(self, text: str, voice_id: str, options: dict[str, Any]) -> dict[str, Any]:
        res = await self.generate(text, voice_id, options)
        res["quality_score"] = round(random.uniform(0.85, 0.99), 2)
        return res

    async def clone_voice(self, audio_file_path: str, name: str) -> str:
        if not os.path.exists(audio_file_path):
            raise FileNotFoundError(f"Cloning audio sample file {audio_file_path} not found.")
        return f"custom-clone-{uuid.uuid4().hex[:6]}"

    async def align(self, audio_file_path: str, text: str) -> dict[str, Any]:
        if not os.path.exists(audio_file_path):
            raise FileNotFoundError(f"Alignment target audio file {audio_file_path} not found.")
        # Perform mock alignment
        words = text.split()
        word_alignment = []
        current_time_ms = 0
        for w in words:
            word_duration = len(w) * 80 + 50
            word_alignment.append({
                "word": w.strip(".,!?\"()"),
                "start_time_ms": current_time_ms,
                "end_time_ms": current_time_ms + word_duration,
                "confidence": 0.95
            })
            current_time_ms += word_duration + 80
        return {
            "word_alignment": word_alignment,
            "duration_ms": current_time_ms
        }
ZOOMING = "zoom"
