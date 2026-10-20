"""ScenarioPlayer engine executing the scripted 'Day in the life of Sentinel-2A' mission scenario."""
import os
from datetime import UTC, datetime
from typing import Any

import yaml
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.db.models import RiskSnapshot as DBRiskSnapshot
from app.services.risk_service import risk_service


def load_demo_config(path: str | None = None) -> dict[str, Any]:
    """Load declarative demo scenario YAML file."""
    if path and os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f)

    search_paths = [
        os.path.join("config", "demo_scenario.yaml"),
        os.path.join("..", "..", "config", "demo_scenario.yaml"),
        os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "config", "demo_scenario.yaml"),
    ]
    for p in search_paths:
        norm = os.path.normpath(p)
        if os.path.exists(norm):
            with open(norm, encoding="utf-8") as f:
                return yaml.safe_load(f)

    # Fallback structure if file not found
    return {
        "scenario_id": "DEMO-SENTINEL-2A-DAY1",
        "asset_id": "SENTINEL-2A",
        "stages": [],
    }


class ScenarioPlayer:
    """Orchestrates headless and interactive playback of scripted mission scenarios."""

    def __init__(self, config_path: str | None = None) -> None:
        self.config = load_demo_config(config_path)
        self.stages: list[dict[str, Any]] = self.config.get("stages", [])
        self.current_stage_idx: int = 0
        self.is_playing: bool = False
        self.speed: float = 1.0
        self.last_evaluation: dict[str, Any] | None = None

    def get_status(self) -> dict[str, Any]:
        """Return player status, current stage index, and scenario metadata."""
        current_stage = (
            self.stages[self.current_stage_idx]
            if 0 <= self.current_stage_idx < len(self.stages)
            else None
        )
        return {
            "scenario_id": self.config.get("scenario_id", "DEMO-SENTINEL-2A-DAY1"),
            "asset_id": self.config.get("asset_id", "SENTINEL-2A"),
            "total_stages": len(self.stages),
            "current_stage_idx": self.current_stage_idx,
            "is_playing": self.is_playing,
            "speed": self.speed,
            "current_stage": current_stage,
            "last_evaluation": self.last_evaluation,
        }

    async def step(self, db: AsyncSession) -> dict[str, Any]:
        """Advance one stage in the scenario timeline, execute ingestion/evaluation, and return result."""
        if not self.stages:
            raise ValueError("No stages loaded in scenario configuration.")

        stage = self.stages[self.current_stage_idx]
        eval_inputs = stage.get("eval_inputs", {})

        asset_id = self.config.get("asset_id", "SENTINEL-2A")
        r_h = eval_inputs.get("r_h", 0.04)
        r_d = eval_inputs.get("r_d", 0.02)
        r_e = eval_inputs.get("r_e", 0.10)
        pc = eval_inputs.get("pc", 1.0e-7)

        logger.info(
            f"ScenarioPlayer stepping stage {self.current_stage_idx}: {stage.get('name')} "
            f"(r_h={r_h}, r_d={r_d}, r_e={r_e}, pc={pc})"
        )

        # Execute evaluation and persist to DB through standard pipeline
        db_snapshot: DBRiskSnapshot = await risk_service.evaluate_and_persist(
            db=db,
            asset_id=asset_id,
            override_rh=r_h,
            override_rd=r_d,
            override_re=r_e,
            override_pc=pc,
            evidence={
                "demo_scenario": self.config.get("scenario_id"),
                "stage_idx": self.current_stage_idx,
                "stage_name": stage.get("name"),
                "t_hour": stage.get("t_hour", 0),
            },
        )

        result_summary = {
            "stage_idx": self.current_stage_idx,
            "stage_name": stage.get("name"),
            "t_hour": stage.get("t_hour", 0),
            "snapshot_id": db_snapshot.id,
            "score": db_snapshot.score,
            "level": db_snapshot.level,
            "r_h": db_snapshot.r_h,
            "r_d": db_snapshot.r_d,
            "r_e": db_snapshot.r_e,
            "defer_eo_payloads": db_snapshot.drivers.get("defer_eo_payloads", False),
            "critical_override_applied": db_snapshot.drivers.get("critical_override_applied", False),
            "recommendations": db_snapshot.drivers.get("recommendations", []),
            "rationale": db_snapshot.drivers.get("rationale", ""),
            "timestamp": datetime.now(UTC).isoformat(),
        }
        self.last_evaluation = result_summary

        # Advance pointer for next step
        self.current_stage_idx = (self.current_stage_idx + 1) % len(self.stages)
        return result_summary

    async def seek(self, stage_idx: int, db: AsyncSession) -> dict[str, Any]:
        """Directly jump to a specified stage index and evaluate it."""
        if not (0 <= stage_idx < len(self.stages)):
            raise ValueError(f"Invalid stage_idx {stage_idx}. Must be between 0 and {len(self.stages) - 1}.")
        self.current_stage_idx = stage_idx
        return await self.step(db)

    async def reset(self, db: AsyncSession) -> dict[str, Any]:
        """Reset scenario player to initial state (Stage 0: Nominal) and evaluate."""
        self.current_stage_idx = 0
        self.is_playing = False
        return await self.step(db)


scenario_player = ScenarioPlayer()
