"""Router for Demo Mode interactive mission playback and scenario progression."""
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.scenario_player import scenario_player

router = APIRouter(prefix="/api/v1/demo", tags=["Demo Mode"])


class SeekRequest(BaseModel):
    """Payload to jump directly to a specific scenario stage."""

    stage_idx: int = Field(..., ge=0, description="Stage index (0 to N-1)")


@router.get("/scenario", summary="Get demo scenario timeline specification")
async def get_demo_scenario() -> dict[str, Any]:
    """Retrieve full declarative definition of the scripted 'Day in the life' scenario."""
    return scenario_player.config


@router.get("/scenarios", summary="List available demo scenarios")
async def list_demo_scenarios() -> list[dict[str, Any]]:
    """Retrieve catalog of demo scenarios/stages."""
    stages = scenario_player.stages
    return [
        {
            "id": f"SCENARIO-{s.get('stage_idx', idx) + 1:02d}",
            "stage_idx": s.get("stage_idx", idx),
            "hour": s.get("t_hour", 0),
            "name": s.get("name", f"Scenario {idx + 1}"),
            "description": s.get("description", ""),
            "expected_level": s.get("expected", {}).get("level", "NOMINAL"),
        }
        for idx, s in enumerate(stages)
    ]


@router.get("/status", summary="Get current demo player status")
async def get_demo_status() -> dict[str, Any]:
    """Retrieve current playback pointer, playing status, and latest stage evaluation."""
    return scenario_player.get_status()


@router.post("/step", summary="Advance demo scenario by one stage")
async def step_demo(
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Step forward one stage in the flight scenario, persist evaluation, and return updated risk."""
    try:
        return await scenario_player.step(db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/seek", summary="Seek directly to a scenario stage")
async def seek_demo(
    request: SeekRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Jump directly to a specific stage index in the scenario timeline."""
    try:
        return await scenario_player.seek(request.stage_idx, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/reset", summary="Reset demo player to initial baseline stage")
async def reset_demo(
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Reset scenario player to T+0 nominal state and evaluate."""
    try:
        return await scenario_player.reset(db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
