"""Constellation Fleet Service & Multi-Asset Conjunction Matrix.

Provides fleet-wide monitoring across Sentinel-2A, Sentinel-1A, and Sentinel-3A,
evaluating cross-asset conjunction threats and streaming real-time subsystem telemetry.
"""
import math
import random
from datetime import UTC, datetime
from typing import Any


class ConstellationService:
    """Service for multi-satellite fleet operations and cross-conjunction matrix."""

    FLEET: dict[str, dict[str, Any]] = {
        "SENTINEL-2A": {
            "id": "SENTINEL-2A",
            "name": "Sentinel-2A (Optical MSI)",
            "norad_id": 40697,
            "type": "Optical Earth Observation",
            "orbit": {
                "altitude_km": 786.0,
                "inclination_deg": 98.62,
                "period_min": 100.5,
                "local_time_descending_node": "10:30 AM",
            },
            "subsystems": {
                "eps": {"battery_temp_c": 24.2, "bus_voltage_v": 28.4, "solar_current_a": 34.2, "status": "NOMINAL"},
                "thermal": {"payload_temp_c": 18.2, "radiator_temp_c": -12.4, "status": "NOMINAL"},
                "adcs": {"wheel_rpm": 2450, "attitude_error_deg": 0.002, "status": "NOMINAL"},
                "obc": {"cpu_load_pct": 28, "memory_used_pct": 42, "status": "NOMINAL"},
                "payload": {"active_instrument": "MSI Multi-Spectral", "duty_cycle_pct": 38, "status": "ACTIVE"},
            },
            "health_score": 9.8,
            "risk_level": "NOMINAL",
        },
        "SENTINEL-1A": {
            "id": "SENTINEL-1A",
            "name": "Sentinel-1A (C-SAR Radar)",
            "norad_id": 39634,
            "type": "Synthetic Aperture Radar",
            "orbit": {
                "altitude_km": 693.0,
                "inclination_deg": 98.18,
                "period_min": 98.6,
                "local_time_descending_node": "06:00 PM",
            },
            "subsystems": {
                "eps": {"battery_temp_c": 26.5, "bus_voltage_v": 28.1, "solar_current_a": 42.0, "status": "NOMINAL"},
                "thermal": {"payload_temp_c": 22.0, "radiator_temp_c": -8.5, "status": "NOMINAL"},
                "adcs": {"wheel_rpm": 3120, "attitude_error_deg": 0.004, "status": "NOMINAL"},
                "obc": {"cpu_load_pct": 48, "memory_used_pct": 56, "status": "NOMINAL"},
                "payload": {"active_instrument": "C-SAR Interferometric Wide", "duty_cycle_pct": 65, "status": "ACTIVE"},
            },
            "health_score": 9.5,
            "risk_level": "NOMINAL",
        },
        "SENTINEL-3A": {
            "id": "SENTINEL-3A",
            "name": "Sentinel-3A (OLCI & SLSTR)",
            "norad_id": 41335,
            "type": "Ocean & Land Environment",
            "orbit": {
                "altitude_km": 814.5,
                "inclination_deg": 98.65,
                "period_min": 101.2,
                "local_time_descending_node": "10:00 AM",
            },
            "subsystems": {
                "eps": {"battery_temp_c": 22.8, "bus_voltage_v": 28.6, "solar_current_a": 31.8, "status": "NOMINAL"},
                "thermal": {"payload_temp_c": -196.0, "radiator_temp_c": -18.2, "status": "NOMINAL"},
                "adcs": {"wheel_rpm": 2100, "attitude_error_deg": 0.002, "status": "NOMINAL"},
                "obc": {"cpu_load_pct": 24, "memory_used_pct": 38, "status": "NOMINAL"},
                "payload": {"active_instrument": "OLCI / SLSTR Dual-Optics", "duty_cycle_pct": 45, "status": "ACTIVE"},
            },
            "health_score": 9.9,
            "risk_level": "NOMINAL",
        },
    }

    CROSS_CONJUNCTIONS: list[dict[str, Any]] = [
        {
            "id": "CONJ-S2A-29834",
            "primary_asset_id": "SENTINEL-2A",
            "primary_name": "Sentinel-2A",
            "secondary_name": "FENGYUN-1C-DEB-29834",
            "secondary_norad_id": 29834,
            "tca_hours": 14.2,
            "miss_distance_m": 315.4,
            "relative_velocity_kms": 12.42,
            "pc": 2.4e-4,
            "risk_class": "CRITICAL",
            "screening_grade": True,
        },
        {
            "id": "CONJ-S1A-40112",
            "primary_asset_id": "SENTINEL-1A",
            "primary_name": "Sentinel-1A",
            "secondary_name": "COSMOS-2251-DEB-40112",
            "secondary_norad_id": 40112,
            "tca_hours": 21.4,
            "miss_distance_m": 1240.0,
            "relative_velocity_kms": 11.20,
            "pc": 1.8e-5,
            "risk_class": "WARNING",
            "screening_grade": True,
        },
        {
            "id": "CONJ-S3A-33441",
            "primary_asset_id": "SENTINEL-3A",
            "primary_name": "Sentinel-3A",
            "secondary_name": "IRIDIUM-33-DEB-33441",
            "secondary_norad_id": 33441,
            "tca_hours": 36.8,
            "miss_distance_m": 4850.0,
            "relative_velocity_kms": 13.85,
            "pc": 1.2e-6,
            "risk_class": "WATCH",
            "screening_grade": True,
        },
        {
            "id": "CONJ-S2A-22285",
            "primary_asset_id": "SENTINEL-2A",
            "primary_name": "Sentinel-2A",
            "secondary_name": "SL-16-R/B-22285",
            "secondary_norad_id": 22285,
            "tca_hours": 49.5,
            "miss_distance_m": 8200.0,
            "relative_velocity_kms": 9.45,
            "pc": 2.1e-7,
            "risk_class": "NOMINAL",
            "screening_grade": True,
        },
    ]

    def get_fleet_matrix(self) -> dict[str, Any]:
        """Return constellation fleet status and cross-asset conjunction threats."""
        fleet_list = list(self.FLEET.values())

        # Fleet aggregate score (weighted average of asset health)
        avg_health = sum(s["health_score"] for s in fleet_list) / len(fleet_list)
        fleet_risk = "NOMINAL" if avg_health > 9.0 else "WARNING"

        return {
            "fleet_size": len(fleet_list),
            "aggregate_health_score": round(avg_health, 2),
            "fleet_risk_level": fleet_risk,
            "assets": fleet_list,
            "cross_conjunctions": self.CROSS_CONJUNCTIONS,
            "active_threats_count": sum(1 for c in self.CROSS_CONJUNCTIONS if c["risk_class"] in ["CRITICAL", "WARNING"]),
            "timestamp": datetime.now(UTC).isoformat(),
        }

    def generate_live_telemetry_packet(self, asset_id: str = "SENTINEL-2A", step: int = 0) -> dict[str, Any]:
        """Generate high-precision live telemetry packet for flight controller streaming."""
        base = self.FLEET.get(asset_id, self.FLEET["SENTINEL-2A"])
        t = step * 0.1

        # Periodic orbital variations (eclipse cycles and radiator oscillation)
        battery_temp = base["subsystems"]["eps"]["battery_temp_c"] + 0.8 * math.sin(t * 0.05) + random.uniform(-0.1, 0.1)
        bus_volt = base["subsystems"]["eps"]["bus_voltage_v"] + 0.2 * math.cos(t * 0.05) + random.uniform(-0.05, 0.05)
        solar_curr = max(0.0, base["subsystems"]["eps"]["solar_current_a"] + 3.0 * math.sin(t * 0.02) + random.uniform(-0.3, 0.3))
        wheel_rpm = base["subsystems"]["adcs"]["wheel_rpm"] + int(45 * math.sin(t * 0.1) + random.randint(-10, 10))
        cpu_load = max(10, min(95, base["subsystems"]["obc"]["cpu_load_pct"] + int(random.uniform(-3, 3))))

        return {
            "asset_id": asset_id,
            "timestamp": datetime.now(UTC).isoformat(),
            "sequence_number": step,
            "channels": {
                "eps_battery_temp_c": round(battery_temp, 2),
                "eps_bus_voltage_v": round(bus_volt, 2),
                "eps_solar_array_current_a": round(solar_curr, 2),
                "adcs_reaction_wheel_rpm": wheel_rpm,
                "adcs_attitude_jitter_deg": round(0.002 + 0.0005 * math.sin(t * 0.2), 4),
                "obc_cpu_load_pct": cpu_load,
            },
            "synthetic": True,
        }
