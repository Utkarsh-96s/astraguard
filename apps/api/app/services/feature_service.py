"""Feature flags service for ASTRA-GUARD.

Loads feature toggles from config/features.yaml with environment variable overrides.
"""
import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from app.core.logging import logger


class FeatureService:
    """Manages feature flags across the platform."""

    def __init__(self, config_path: str | None = None) -> None:
        if config_path:
            self.config_path = Path(config_path)
        else:
            # Resolve relative to repo root
            root = Path(__file__).resolve().parent.parent.parent.parent.parent
            self.config_path = root / "config" / "features.yaml"

    def get_features(self) -> dict[str, bool]:
        """Return flattened dictionary of all feature flags with env overrides."""
        flags: dict[str, bool] = {}
        if self.config_path.exists():
            try:
                with open(self.config_path, encoding="utf-8") as f:
                    data: dict[str, Any] = yaml.safe_load(f) or {}
                for category in ("features", "quick_wins"):
                    for key, val in data.get(category, {}).items():
                        flags[key] = bool(val)
            except Exception as e:
                logger.error(f"Error loading {self.config_path}: {e}")

        # Check environment variable overrides (e.g. ASTRA_FEATURE_ORBIT_TWIN_3D=false)
        for flag in list(flags.keys()):
            env_var = f"ASTRA_FEATURE_{flag.upper()}"
            if env_var in os.environ:
                val = os.environ[env_var].strip().lower()
                flags[flag] = val in ("1", "true", "yes", "on")

        return flags

    def is_enabled(self, flag_name: str) -> bool:
        """Check if a specific feature flag is active."""
        features = self.get_features()
        return features.get(flag_name, False)


@lru_cache(maxsize=1)
def get_feature_service() -> FeatureService:
    """Singleton provider for FeatureService."""
    return FeatureService()


feature_service = get_feature_service()
