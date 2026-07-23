import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from core.database.session import get_db
from core.marketing.dto.marketing_dto import (
    SegmentCreateDTO, SegmentResponseDTO, CampaignResponseDTO
)
from core.marketing.services.marketing_service import MarketingService

router = APIRouter(prefix="/v1/marketing", tags=["Dynamic Marketing Engine"])

class GenerateCampaignIn(BaseModel):
    title: str
    genre: str = "Drama"
    target_platform: str = "youtube_reels"

@router.post("/segment", response_model=SegmentResponseDTO, status_code=status.HTTP_201_CREATED)
def create_audience_segment(dto: SegmentCreateDTO, db: Session = Depends(get_db)):
    service = MarketingService(db)
    return service.create_segment(dto)

@router.post("/campaign/generate", response_model=CampaignResponseDTO)
def generate_ai_campaign(payload: GenerateCampaignIn, db: Session = Depends(get_db)):
    service = MarketingService(db)
    return service.generate_ai_campaign(payload.title, payload.genre, payload.target_platform)

@router.get("/campaigns", response_model=List[CampaignResponseDTO])
def list_active_campaigns(db: Session = Depends(get_db)):
    service = MarketingService(db)
    return service.list_campaigns()
