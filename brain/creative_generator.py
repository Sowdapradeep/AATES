import uuid
from typing import Any
from sqlalchemy.orm import Session
from contracts.dto.creative import CharacterProfile, VillainProfile, RelationshipDTO, LocationDTO, OrganizationDTO
from brain.story_bible.bible import story_bible_engine

class CreativeGenerator:
    """Creative Generator class creating lore entities and updating the central Story Bible."""
    
    async def generate_universe(self, universe_id: str, name: str, genre: str, themes: list[str], db: Session = None) -> dict[str, Any]:
        """Formulates base universe metadata parameters and initializes the Story Bible."""
        universe_data = {
            "name": name,
            "genre": genre,
            "themes": themes,
            "rules": [
                "Realism must prioritize local Tamil cultural structures.",
                "Character actions conform to the defined continuity timeline."
            ]
        }
        
        story_bible_engine.update_bible(
            universe_id=universe_id,
            section="universe",
            key="metadata",
            new_value=universe_data,
            author="Creative Director Agent",
            reason=f"Initialize new universe lore metadata: {name}",
            db=db
        )
        return universe_data

    async def generate_character(self, universe_id: str, profile: CharacterProfile, db: Session = None) -> CharacterProfile:
        """Formulates a standard character profile and registers them in the Story Bible."""
        story_bible_engine.update_bible(
            universe_id=universe_id,
            section="characters",
            key=profile.id,
            new_value=profile.model_dump(),
            author="Creative Director Agent",
            reason=f"Generate character profile: {profile.name}",
            db=db
        )
        return profile

    async def generate_villain(self, universe_id: str, profile: VillainProfile, db: Session = None) -> VillainProfile:
        """Formulates a villain profile and registers their antagonistic details."""
        story_bible_engine.update_bible(
            universe_id=universe_id,
            section="villains",
            key=profile.character_id,
            new_value=profile.model_dump(),
            author="Creative Director Agent",
            reason=f"Formulate villain parameters for character_id: {profile.character_id}",
            db=db
        )
        return profile

    async def generate_location(self, universe_id: str, loc: LocationDTO, db: Session = None) -> LocationDTO:
        """Registers a set location configuration in the Story Bible."""
        story_bible_engine.update_bible(
            universe_id=universe_id,
            section="locations",
            key=loc.id,
            new_value=loc.model_dump(),
            author="Creative Director Agent",
            reason=f"Register location settings configuration: {loc.name}",
            db=db
        )
        return loc

    async def generate_organization(self, universe_id: str, org: OrganizationDTO, db: Session = None) -> OrganizationDTO:
        """Registers a faction or organization group inside the Story Bible."""
        story_bible_engine.update_bible(
            universe_id=universe_id,
            section="organizations",
            key=org.id,
            new_value=org.model_dump(),
            author="Creative Director Agent",
            reason=f"Formulate faction organization configuration: {org.name}",
            db=db
        )
        return org

    async def establish_relationship(self, universe_id: str, rel: RelationshipDTO, db: Session = None) -> RelationshipDTO:
        """Establishes structural relationship ties between two characters."""
        story_bible_engine.update_bible(
            universe_id=universe_id,
            section="relationships",
            key=f"{rel.character_a_id}-{rel.character_b_id}",
            new_value=rel.model_dump(),
            author="Creative Director Agent",
            reason=f"Set relationship between {rel.character_a_id} and {rel.character_b_id}",
            db=db
        )
        return rel

creative_generator = CreativeGenerator()
