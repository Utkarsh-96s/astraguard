"""Router for SpaceX monochrome figures and visual artifacts catalog."""
from fastapi import APIRouter, HTTPException, Query

from app.schemas.dl_inference import FigureEntry
from app.services.dl_inference_service import dl_inference_service

router = APIRouter(prefix="/api/v1/figures", tags=["Figures & Visual Artifacts"])


@router.get("", summary="Get all evaluated SpaceX monochrome figures", response_model=list[FigureEntry])
async def list_figures(
    tag: str | None = Query(default=None, description="Optional tag filter (e.g. loss_curve, xai, failure_case)"),
    subsystem: str | None = Query(default=None, description="Domain filter: health, debris, or disaster"),
    model_id: str | None = Query(default=None, description="Filter by model identifier"),
) -> list[FigureEntry]:
    """Retrieve catalog of all 26 measured, traceable SpaceX monochrome figures (PNG & SVG) with data hashes."""
    return dl_inference_service.get_figures(tag=tag, subsystem=subsystem, model_id=model_id)


@router.get("/{figure_id}", summary="Get single figure metadata by ID", response_model=FigureEntry)
async def get_figure_by_id(figure_id: str) -> FigureEntry:
    """Retrieve figure metadata, data source, commit hash, timestamp, and visual artifact URLs."""
    figure = dl_inference_service.get_figure(figure_id)
    if not figure:
        raise HTTPException(status_code=404, detail=f"Figure '{figure_id}' not found in manifest")
    return figure
