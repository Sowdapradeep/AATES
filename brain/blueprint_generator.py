import re
import json
import logging
from typing import Any
from sqlalchemy.orm import Session
from core.database.session import SessionLocal
from core.database.models import SystemState
from contracts.dto.blueprint import ProductionBlueprint, SceneBlueprint
from contracts.dto.creative import DialogueLine
from brain.story_bible.bible import story_bible_engine

logger = logging.getLogger("blueprint_generator")

class ProductionBlueprintGenerator:
    """Core Production Blueprint Generator compiling creative intelligence states into standard production artifacts."""
    
    async def generate_blueprint(
        self,
        universe_id: str,
        season: int,
        episode: int,
        episode_id: str,
        db: Session = None
    ) -> ProductionBlueprint:
        """Assembles characters, props, camera intents, and dialogue into a standardized Production Blueprint."""
        from core.narrative.models.episode import Episode
        from core.narrative.intelligence.bedrock_client import bedrock_intelligence

        session = db or SessionLocal()
        try:
            bible = story_bible_engine.get_bible(universe_id, db=session)
            chars = list(bible.get("characters", {}).keys()) if bible else ["Kadamban", "Nallasamy"]
            
            # Fetch episode details from DB (convert to UUID object to avoid SQLite StatementError during tests)
            import uuid as uuid_pkg
            ep_record = None
            if isinstance(episode_id, uuid_pkg.UUID):
                ep_record = session.query(Episode).filter(Episode.id == episode_id).first()
            elif isinstance(episode_id, str):
                try:
                    uuid_obj = uuid_pkg.UUID(episode_id)
                    ep_record = session.query(Episode).filter(Episode.id == uuid_obj).first()
                except ValueError:
                    # Invalid UUID string (e.g. test dummies like 'ep-101'), skip DB query
                    pass

            ep_title = ep_record.title if ep_record else "Rising indignation"
            ep_beats = ep_record.story_beats if ep_record else []
            
            # Attempt dynamic Bedrock screenplay generation
            parsed_scenes = []
            try:
                system_prompt = "You are the AATES Screenplay Writer AI. Generate a professional, highly engaging screenplay script for the AATES daily series."
                user_prompt = (
                    f"Series context details:\n"
                    f"- Season: {season}\n"
                    f"- Episode: {episode}\n"
                    f"- Title: {ep_title}\n"
                    f"- Story Beats: {ep_beats}\n"
                    f"- Characters: {chars}\n\n"
                    "Return a JSON object containing a list of exactly 4 sequential scenes that build a complete, continuous cinematic storyline totaling about 60 seconds (each scene should contain 2-3 spoken dialogues). "
                    "The JSON structure must match this schema exactly:\n"
                    "{\n"
                    "  \"scenes\": [\n"
                    "    {\n"
                    "      \"scene_number\": 1,\n"
                    "      \"location\": \"Village Central Square\",\n"
                    "      \"time_of_day\": \"DAY\",\n"
                    "      \"weather\": \"SUNNY\",\n"
                    "      \"lighting_mood\": \"Cinematic high-contrast sunlight\",\n"
                    "      \"characters\": [\"Kadamban\", \"Nallasamy\"],\n"
                    "      \"emotions\": [\"tense\", \"indignant\"],\n"
                    "      \"props\": [\"survey blueprint map\"],\n"
                    "      \"costumes\": {\"Kadamban\": \"Traditional green cotton shirt\", \"Nallasamy\": \"Charcoal business suit\"},\n"
                    "      \"camera_intent\": \"Close-up tracking shot on characters confronting each other\",\n"
                    "      \"visual_style\": \"Dramatic rustic realism\",\n"
                    "      \"dialogues\": [\n"
                    "        {\n"
                    "          \"character_name\": \"Kadamban\",\n"
                    "          \"text_tamil\": \"[Dialogue text written in Tamil script here]\",\n"
                    "          \"text_english\": \"[English translation of the dialogue]\",\n"
                    "          \"slang_type\": \"standard\",\n"
                    "          \"delivery_note\": \"resolute, quiet defiance\"\n"
                    "        }\n"
                    "      ],\n"
                    "      \"music_mood\": \"Tense low traditional flute\",\n"
                    "      \"sound_effects\": [\"rural morning wind\"],\n"
                    "      \"continuity_notes\": \"blueprint folder must match blue cover\",\n"
                    "      \"rendering_hints\": {\"target_resolution\": \"1080p\", \"style_reference\": \"cinematic_realism\"}\n"
                    "    }\n"
                    "  ]\n"
                    "}\n\n"
                    "Ensure dialogues are written in actual Tamil script for 'text_tamil' so that AWS Polly voice synthesizers can speak them properly. Ensure the response is valid, clean, parseable JSON only."
                )
                
                res = bedrock_intelligence.reason(user_prompt, system_instruction=system_prompt)
                cleaned_res = res.strip()
                if "```json" in cleaned_res:
                    cleaned_res = re.search(r"```json\s*(.*?)\s*```", cleaned_res, re.DOTALL).group(1)
                elif "```" in cleaned_res:
                    cleaned_res = re.search(r"```\s*(.*?)\s*```", cleaned_res, re.DOTALL).group(1)
                
                parsed_data = json.loads(cleaned_res)
                raw_scenes = parsed_data.get("scenes", [])
                
                for s in raw_scenes:
                    dialogues_list = []
                    for d in s.get("dialogues", []):
                        dialogues_list.append(DialogueLine(
                            character_name=d.get("character_name", chars[0]),
                            text_tamil=d.get("text_tamil", ""),
                            text_english=d.get("text_english", ""),
                            slang_type=d.get("slang_type", "standard"),
                            delivery_note=d.get("delivery_note", "neutral")
                        ))
                    
                    parsed_scenes.append(SceneBlueprint(
                        scene_number=int(s.get("scene_number", 1)),
                        location=s.get("location", "Village Border Woods"),
                        time_of_day=s.get("time_of_day", "DAY"),
                        weather=s.get("weather", "SUNNY"),
                        lighting_mood=s.get("lighting_mood", "Warm golden natural light"),
                        characters=s.get("characters", chars[:2]),
                        emotions=s.get("emotions", ["tense"]),
                        props=s.get("props", []),
                        costumes=s.get("costumes", {}),
                        camera_intent=s.get("camera_intent", "Widescreen camera shot"),
                        visual_style=s.get("visual_style", "Rustic realism"),
                        dialogues=dialogues_list,
                        music_mood=s.get("music_mood", "Tense traditional elements"),
                        sound_effects=s.get("sound_effects", []),
                        continuity_notes=s.get("continuity_notes", ""),
                        rendering_hints=s.get("rendering_hints", {"target_resolution": "1080p"})
                    ))
                logger.info(f"Successfully generated dynamic 4-scene screenplay blueprint for Episode {episode} via Bedrock.")
            except Exception as ai_err:
                logger.warning(f"Bedrock dynamic screenplay generation failed: {ai_err}. Falling back to 4-scene production template.")
                parsed_scenes = []

            # Fallback block (Construct a solid 4-scene / 60-second cinematic screenplay template)
            if not parsed_scenes:
                fallback_dialogues = [
                    [
                        DialogueLine(
                            character_name="Kadamban",
                            text_tamil="இந்த நிலம் எங்களது மூதாதையர்களுடையது. இதை நீங்கள் எக்காரணத்தைக் கொண்டும் பறிக்க முடியாது.",
                            text_english="This land belongs to our ancestors. You cannot seize it under any circumstance.",
                            slang_type="standard",
                            delivery_note="resolute, quiet defiance"
                        ),
                        DialogueLine(
                            character_name="Kadamban",
                            text_tamil="தலைமுறை தலைமுறையாக நாங்கள் இங்குதான் வாழ்ந்து வருகிறோம்.",
                            text_english="We have been living here for generations.",
                            slang_type="standard",
                            delivery_note="passionate tone"
                        )
                    ],
                    [
                        DialogueLine(
                            character_name="Nallasamy",
                            text_tamil="சட்டப்படி இந்த நிலம் அரசாங்கத்திற்கு சொந்தமானது. நீங்கள் இங்கிருந்து வெளியேறித்தான் ஆக வேண்டும்.",
                            text_english="Legally, this land belongs to the government. You have to leave this place.",
                            slang_type="standard",
                            delivery_note="cold, official authority"
                        ),
                        DialogueLine(
                            character_name="Nallasamy",
                            text_tamil="மாற்று இடம் மற்றும் நஷ்டஈடு வழங்க நாங்கள் தயாராக இருக்கிறோம்.",
                            text_english="We are ready to provide alternative land and compensation.",
                            slang_type="standard",
                            delivery_note="persuading tone"
                        )
                    ],
                    [
                        DialogueLine(
                            character_name="Kadamban",
                            text_tamil="எங்கள் வாழ்வாதாரத்தை பணத்தால் விலை பேச முடியாது. நாங்கள் கடைசி மூச்சு வரை போராடுவோம்!",
                            text_english="Our livelihood cannot be priced with money. We will fight till our last breath!",
                            slang_type="standard",
                            delivery_note="rising anger, high emotion"
                        ),
                        DialogueLine(
                            character_name="Kadamban",
                            text_tamil="எங்கள் மக்கள் அனைவரும் ஒன்று கூடி எதிர்ப்போம்.",
                            text_english="All our people will gather and resist.",
                            slang_type="standard",
                            delivery_note="determined resolve"
                        )
                    ],
                    [
                        DialogueLine(
                            character_name="Nallasamy",
                            text_tamil="அபிவிருத்தி வரும்போது அதை யாராலும் தடுத்து நிறுத்த முடியாது. யோசித்து நல்ல முடிவாக எடுங்கள்.",
                            text_english="When development comes, no one can stop it. Think and make a good decision.",
                            slang_type="standard",
                            delivery_note="stern warning"
                        ),
                        DialogueLine(
                            character_name="Nallasamy",
                            text_tamil="இது உங்களுக்குக் கிடைக்கும் கடைசி வாய்ப்பு.",
                            text_english="This is the last chance you will get.",
                            slang_type="standard",
                            delivery_note="serious delivery"
                        )
                    ]
                ]
                
                locations = ["Village Border Woods", "Village Central Square", "Community Panchayat Office", "Village Elder House"]
                props = ["survey boundary stakes", "official document blue folder", "protest banner", "ancestral documents"]
                camera_intents = [
                    "Establishing wide shot showing native trees, slow tracking closer to characters confrontation.",
                    "Close up on corporate official showing the highway construction blueprint map.",
                    "Wide shot of villagers gathering at community office with angry gestures.",
                    "Medium shot of Nallasamy standing near a black sedan, warning the village elder."
                ]
                
                for idx in range(4):
                    parsed_scenes.append(SceneBlueprint(
                        scene_number=idx + 1,
                        location=locations[idx],
                        time_of_day="DAY",
                        weather="SUNNY",
                        lighting_mood="Warm golden natural light",
                        characters=chars[:2],
                        emotions=["nostalgic", "tense"],
                        props=[props[idx]],
                        costumes={
                            "Kadamban": "Green traditional cotton shirt and rustic dhoti.",
                            "Nallasamy": "Polished charcoal corporate business suit."
                        },
                        camera_intent=camera_intents[idx],
                        visual_style="Rustic realism with high contrast tones.",
                        dialogues=fallback_dialogues[idx],
                        music_mood="Low atmospheric percussion, traditional Tamil flute elements",
                        sound_effects=["Forest wind blow", "Stakes pounding sound"],
                        continuity_notes="Survey folder must match blue cover.",
                        rendering_hints={"target_resolution": "1080p", "style_reference": "cinematic_realism"}
                    ))
            
            blueprint = ProductionBlueprint(
                episode_id=episode_id,
                universe_id=universe_id,
                season=season,
                episode=episode,
                scenes=parsed_scenes,
                version=1
            )
            
            # Persist blueprint in db SystemState
            state_key = f"blueprint-{episode_id}"
            state = session.query(SystemState).filter(SystemState.state_key == state_key).first()
            if not state:
                state = SystemState(state_key=state_key, state_value=blueprint.model_dump())
                session.add(state)
            else:
                # Force updates validation
                state.state_value = {}
                session.flush()
                state.state_value = blueprint.model_dump()
                
            if not db:
                session.commit()
                
            return blueprint
        except Exception as e:
            if not db:
                session.rollback()
            raise e
        finally:
            if not db:
                session.close()


blueprint_generator = ProductionBlueprintGenerator()
