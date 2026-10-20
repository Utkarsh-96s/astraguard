"""Disaster Intelligence Deck Service.

Provides rich Earth Observation scenarios across radar (SAR) and optical multi-spectral sensors,
including high-resolution flood extent, wildfire burn scars, and critical infrastructure triage.
"""
from typing import Any


class DisasterDeckService:
    """Service providing multi-hazard Earth Observation disaster datasets and infrastructure triage."""

    SCENARIOS: dict[str, dict[str, Any]] = {
        "DIS-EMILIA-FLOOD-2023": {
            "id": "DIS-EMILIA-FLOOD-2023",
            "name": "Emilia-Romagna Flash & River Inundation",
            "location": "Emilia-Romagna, Italy",
            "country": "Italy",
            "sensor": "Sentinel-1 C-SAR (Synthetic Aperture Radar)",
            "sensor_type": "radar",
            "polarization": "VV + VH Dual-Pol",
            "resolution_m": 10.0,
            "acquisition_date": "2023-05-18T05:32:00Z",
            "disaster_type": "flood",
            "area_km2": 480.0,
            "priority": 0.88,
            "confidence": 0.96,
            "mean_iou": 0.9548,
            "mean_dice": 0.9768,
            "backscatter_drop_db": -4.2,
            "geojson_footprint": {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [11.85, 44.30],
                        [12.35, 44.30],
                        [12.35, 44.65],
                        [11.85, 44.65],
                        [11.85, 44.30],
                    ]],
                },
                "properties": {
                    "name": "Bologna-Ravenna-Faenza Basin",
                    "bbox": [11.85, 44.30, 12.35, 44.65],
                },
            },
            "infrastructure_impact": {
                "substations_affected": 14,
                "bridges_critical": 28,
                "hospitals_warning": 3,
                "agricultural_hectares": 12400.0,
                "population_exposed": 185000,
            },
            "priority_drivers": [
                {"factor": "Inundated Extent (480 km²)", "weight": 0.35, "score": 0.35},
                {"factor": "Critical Energy & Transport Nodes", "weight": 0.25, "score": 0.23},
                {"factor": "Agricultural Economic Risk", "weight": 0.20, "score": 0.18},
                {"factor": "Sensor Cloud Penetration (SAR All-Weather)", "weight": 0.20, "score": 0.12},
            ],
            "description": "Catastrophic river overflows triggered by 36 hours of extreme precipitation across 23 river basins.",
        },
        "DIS-BRAHMAPUTRA-01": {
            "id": "DIS-BRAHMAPUTRA-01",
            "name": "Brahmaputra River Basin Monsoonal Surge",
            "location": "Assam, India",
            "country": "India",
            "sensor": "Sentinel-1 C-SAR",
            "sensor_type": "radar",
            "polarization": "Dual-Pol VV+VH",
            "resolution_m": 10.0,
            "acquisition_date": "2026-10-19T00:15:00Z",
            "disaster_type": "flood",
            "area_km2": 320.0,
            "priority": 0.78,
            "confidence": 0.94,
            "mean_iou": 0.9420,
            "mean_dice": 0.9701,
            "backscatter_drop_db": -3.8,
            "geojson_footprint": {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [85.00, 20.00],
                        [85.50, 20.00],
                        [85.50, 20.50],
                        [85.00, 20.50],
                        [85.00, 20.00],
                    ]],
                },
                "properties": {
                    "name": "Brahmaputra Flood Plain",
                    "bbox": [85.00, 20.00, 85.50, 20.50],
                },
            },
            "infrastructure_impact": {
                "substations_affected": 8,
                "bridges_critical": 19,
                "hospitals_warning": 2,
                "agricultural_hectares": 8900.0,
                "population_exposed": 95000,
            },
            "priority_drivers": [
                {"factor": "Inundated Extent (320 km²)", "weight": 0.35, "score": 0.28},
                {"factor": "High Population Vulnerability", "weight": 0.25, "score": 0.24},
                {"factor": "River Embankment Breaches", "weight": 0.20, "score": 0.16},
                {"factor": "Repeat Optical Cloud Cover", "weight": 0.20, "score": 0.10},
            ],
            "description": "Monsoonal river expansion inundating agricultural lowlands and low-lying river islands.",
        },
        "DIS-GREECE-EVROS-2023": {
            "id": "DIS-GREECE-EVROS-2023",
            "name": "Evros Megafire & Dadia Forest Burn Scar",
            "location": "Evros, Greece",
            "country": "Greece",
            "sensor": "Sentinel-2 MSI (Multi-Spectral Instrument)",
            "sensor_type": "optical",
            "polarization": "SWIR-2 / NIR / Red Normalized Burn Ratio",
            "resolution_m": 10.0,
            "acquisition_date": "2023-08-28T09:12:00Z",
            "disaster_type": "wildfire",
            "area_km2": 935.0,
            "priority": 0.94,
            "confidence": 0.98,
            "mean_iou": 0.9610,
            "mean_dice": 0.9802,
            "backscatter_drop_db": 0.0,
            "geojson_footprint": {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [25.80, 40.85],
                        [26.40, 40.85],
                        [26.40, 41.35],
                        [25.80, 41.35],
                        [25.80, 40.85],
                    ]],
                },
                "properties": {
                    "name": "Evros & Dadia Biosphere Reserve",
                    "bbox": [25.80, 40.85, 26.40, 41.35],
                },
            },
            "infrastructure_impact": {
                "substations_affected": 6,
                "bridges_critical": 8,
                "hospitals_warning": 1,
                "agricultural_hectares": 34000.0,
                "population_exposed": 42000,
            },
            "priority_drivers": [
                {"factor": "Massive Burn Scar Extent (935 km²)", "weight": 0.40, "score": 0.39},
                {"factor": "Protected Biosphere Destruction", "weight": 0.25, "score": 0.25},
                {"factor": "Border Region Transport Corridor", "weight": 0.20, "score": 0.18},
                {"factor": "dNBR Burn Severity Index", "weight": 0.15, "score": 0.12},
            ],
            "description": "Largest single recorded wildfire in EU history, consuming protected black vulture habitat in Dadia National Park.",
        },
        "DIS-VALENCIA-FLASH-2024": {
            "id": "DIS-VALENCIA-FLASH-2024",
            "name": "Valencia DANA Flash Flood & Ravine Torrent",
            "location": "Valencia, Spain",
            "country": "Spain",
            "sensor": "Sentinel-1 C-SAR + Sentinel-2 MSI Multi-Sensor Fusion",
            "sensor_type": "radar_optical_fusion",
            "polarization": "Dual-Pol + RGB/NIR",
            "resolution_m": 10.0,
            "acquisition_date": "2024-10-30T06:14:00Z",
            "disaster_type": "flood",
            "area_km2": 215.0,
            "priority": 0.84,
            "confidence": 0.95,
            "mean_iou": 0.9480,
            "mean_dice": 0.9734,
            "backscatter_drop_db": -5.1,
            "geojson_footprint": {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [-0.55, 39.30],
                        [-0.25, 39.30],
                        [-0.25, 39.60],
                        [-0.55, 39.60],
                        [-0.55, 39.30],
                    ]],
                },
                "properties": {
                    "name": "Rambla del Poyo & Horta Sud",
                    "bbox": [-0.55, 39.30, -0.25, 39.60],
                },
            },
            "infrastructure_impact": {
                "substations_affected": 22,
                "bridges_critical": 41,
                "hospitals_warning": 5,
                "agricultural_hectares": 7200.0,
                "population_exposed": 240000,
            },
            "priority_drivers": [
                {"factor": "High Urban Population Density", "weight": 0.35, "score": 0.33},
                {"factor": "Critical Highway & Rail Cutoffs", "weight": 0.25, "score": 0.24},
                {"factor": "Flash Surge Inundation", "weight": 0.25, "score": 0.17},
                {"factor": "Rapid Cloud Clearing Multi-Sensor", "weight": 0.15, "score": 0.10},
            ],
            "description": "Isolated high-altitude depression (DANA) causing unprecedented ravine surges across southern Valencia metropolitan towns.",
        },
    }

    def list_scenarios(self) -> list[dict[str, Any]]:
        """Return catalog of all available disaster scenarios."""
        return list(self.SCENARIOS.values())

    def get_scenario(self, event_id: str) -> dict[str, Any] | None:
        """Return scenario by ID with fallback matching."""
        if event_id in self.SCENARIOS:
            return self.SCENARIOS[event_id]
        # Match case-insensitive or partial
        for key, val in self.SCENARIOS.items():
            if event_id.upper() in key:
                return val
        return None
