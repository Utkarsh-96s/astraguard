"""Router for querying feature flags."""
from fastapi import APIRouter
from pydantic import BaseModel

from app.services.feature_service import feature_service

router = APIRouter(prefix="/features", tags=["features"])


class FeaturesResponse(BaseModel):
    """Features response model."""
    flags: dict[str, bool]


@router.get("", response_model=FeaturesResponse)
async def get_feature_flags() -> FeaturesResponse:
    """Return all active feature flags."""
    return FeaturesResponse(flags=feature_service.get_features())
