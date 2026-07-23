import uuid
from typing import List, Optional
from sqlalchemy.orm import Session
from core.marketing.dto.marketing_dto import (
    SegmentCreateDTO, SegmentResponseDTO, CampaignCreateDTO, CampaignResponseDTO
)
from core.marketing.repositories.audience_repo import AudienceRepository
from core.marketing.repositories.campaign_repo import CampaignRepository
from core.narrative.intelligence.bedrock_client import bedrock_intelligence

class MarketingService:
    """Service handling audience segment creation and AI viral campaign generation."""
    def __init__(self, db: Session) -> None:
        self.db = db
        self.aud_repo = AudienceRepository(db)
        self.camp_repo = CampaignRepository(db)

    def create_segment(self, dto: SegmentCreateDTO) -> SegmentResponseDTO:
        seg = self.aud_repo.create(**dto.model_dump())
        return SegmentResponseDTO.model_validate(seg)

    def generate_ai_campaign(self, title: str, genre: str = "Drama", target_platform: str = "youtube_reels") -> CampaignResponseDTO:
        # Use Bedrock Nova Pro to generate targeted Tamil marketing hooks and viral hashtags
        system_prompt = "You are the AATES Marketing Intelligence Engine. Generate viral Tamil promotional hooks and hashtags for entertainment assets."
        user_prompt = f"Video Title: {title}\nGenre: {genre}\nPlatform: {target_platform}\n\nReturn JSON with fields: 'viral_hook', 'hashtags' (list of strings)."

        raw = bedrock_intelligence.reason(user_prompt, system_instruction=system_prompt)
        parsed = {}
        try:
            import json
            parsed = json.loads(raw)
        except Exception:
            parsed = {
                "viral_hook": f"Unseen dramatic twist in {title}! #AATES #TamilCinema",
                "hashtags": ["#AATES", "#TamilShorts", "#TrendingTamil", "#CinemaUpdate"]
            }

        camp = self.camp_repo.create(
            title=title,
            target_platform=target_platform,
            viral_hook=parsed.get("viral_hook"),
            hashtags=parsed.get("hashtags", []),
            budget_allocation_usd=0.0,
            performance_score=85.0
        )
        return CampaignResponseDTO.model_validate(camp)

    def list_campaigns(self) -> List[CampaignResponseDTO]:
        camps = self.camp_repo.get_active_campaigns()
        return [CampaignResponseDTO.model_validate(c) for c in camps]
