from typing import Any
from sqlalchemy.orm import Session
from core.database.session import SessionLocal
from core.database.models import SystemState
from contracts.dto.blueprint import ProductionBlueprint, SceneBlueprint
from contracts.dto.creative import DialogueLine
from brain.story_bible.bible import story_bible_engine

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
        session = db or SessionLocal()
        try:
            bible = story_bible_engine.get_bible(universe_id, db=session)
            chars = list(bible.get("characters", {}).keys())
            
            # Formulate structured Scene Blueprint parameters
            scene_1 = SceneBlueprint(
                scene_number=1,
                location="Village Border Woods",
                time_of_day="DAY",
                weather="SUNNY",
                lighting_mood="Warm golden natural light",
                characters=chars[:2] if len(chars) >= 2 else ["Kadamban", "Nallasamy"],
                emotions=["nostalgic", "tense"],
                props=["survey boundary stakes", "official document blue folder"],
                costumes={
                    "Kadamban": "Green traditional cotton shirt and rustic dhoti.",
                    "Nallasamy": "Polished charcoal corporate business suit."
                },
                camera_intent="Establishing wide shot showing native trees, slow tracking closer to characters confrontation.",
                visual_style="Rustic realism with high contrast tones.",
                dialogues=[
                    DialogueLine(
                        character_name="Kadamban",
                        text_tamil="Idhu enga nilam. Ingu ungaluku velai illai.",
                        text_english="This is our land. You have no business here.",
                        slang_type="kovai",
                        delivery_note="Quiet indignation, resolute gaze."
                    )
                ],
                music_mood="Low atmospheric percussion, traditional Tamil flute elements",
                sound_effects=["Forest wind blow", "Stakes pounding sound"],
                continuity_notes="Survey folder must match blue cover from season arc setups.",
                rendering_hints={"target_resolution": "1080p", "style_reference": "cinematic_realism"}
            )
            
            blueprint = ProductionBlueprint(
                episode_id=episode_id,
                universe_id=universe_id,
                season=season,
                episode=episode,
                scenes=[scene_1],
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
