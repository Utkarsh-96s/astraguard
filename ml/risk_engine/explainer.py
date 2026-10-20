"""Explainability and attribution aggregation with deterministic rationale templates."""
from typing import Any

from ml.common.schemas import Attribution
from ml.risk_engine.schemas import DriverContribution, RiskLevel


class AttributionAggregator:
    """Aggregates and normalizes multi-module factor attributions."""

    def aggregate(
        self,
        r_h: float,
        r_d: float,
        r_e: float,
        r_safety: float,
        health_attributions: list[Attribution] | None = None,
        debris_attributions: list[Attribution] | None = None,
        disaster_attributions: list[Attribution] | None = None,
        top_k: int = 5,
    ) -> list[DriverContribution]:
        """Combine module-level attributions and scale them to 100% of explained risk."""
        h_attrs = health_attributions or []
        d_attrs = debris_attributions or []
        e_attrs = disaster_attributions or []

        # Relative module weights in overall risk
        w_safety = 0.85
        w_eo = 0.15

        # Allocate safety weight between health and debris
        denom = r_h + r_d + 1e-6
        h_weight = w_safety * (r_h / denom) * r_safety
        d_weight = w_safety * (r_d / denom) * r_safety
        e_weight = w_eo * r_e

        raw_drivers: list[tuple[str, str, float, str, str]] = []

        # 1. Process health drivers
        for attr in h_attrs:
            mag = float(attr.contribution) * h_weight
            desc = f"Subsystem telemetry anomaly on channel {attr.driver}"
            raw_drivers.append((attr.driver, "health", mag, attr.direction, desc))

        # 2. Process debris drivers
        for attr in d_attrs:
            mag = float(attr.contribution) * d_weight
            desc = f"Orbital encounter parameter: {attr.driver}"
            raw_drivers.append((attr.driver, "debris", mag, attr.direction, desc))

        # 3. Process disaster drivers
        for attr in e_attrs:
            mag = float(attr.contribution) * e_weight
            desc = f"Earth observation priority factor: {attr.driver}"
            raw_drivers.append((attr.driver, "disaster", mag, attr.direction, desc))

        # Fallback if upstream modules provided no fine-grained attributions
        if not raw_drivers:
            if r_h > 0.05:
                raw_drivers.append(("spacecraft_telemetry", "health", h_weight, "increase", "Overall telemetry anomaly score"))
            if r_d > 0.05:
                raw_drivers.append(("orbital_conjunction", "debris", d_weight, "increase", "Debris collision probability"))
            if r_e > 0.05:
                raw_drivers.append(("disaster_priority", "disaster", e_weight, "increase", "Earth observation priority weighting"))

        # Sort by magnitude descending
        raw_drivers.sort(key=lambda x: abs(x[2]), reverse=True)
        top_drivers = raw_drivers[:top_k]

        total_mag = sum(abs(x[2]) for x in top_drivers) + 1e-8

        result: list[DriverContribution] = []
        for name, mod, mag, direction, desc in top_drivers:
            pct = round(float((abs(mag) / total_mag) * 100.0), 1)
            result.append(
                DriverContribution(
                    driver=name,
                    module=mod,
                    magnitude=round(float(mag), 4),
                    percent_of_risk=pct,
                    direction=direction if direction in ("increase", "decrease") else "increase",
                    summary=desc,
                )
            )

        return result


class DeterministicRationaleGenerator:
    """Generates rigorous, deterministic aerospace flight-director rationale text."""

    def generate_rationale(
        self,
        asset_id: str,
        score: float,
        level: RiskLevel,
        r_h: float,
        r_d: float,
        r_e: float,
        r_safety: float,
        critical_override: bool,
        warning_override: bool,
        defer_eo: bool,
        drivers: list[DriverContribution],
        evidence: dict[str, Any] | None = None,
    ) -> str:
        """Compose deterministic rationale from structured operational templates."""
        ev = evidence or {}

        # 1. Critical Conjunction Override
        if critical_override:
            sec_id = ev.get("secondary_id", ev.get("secondary_object", "UNKNOWN-DEBRIS"))
            pc_val = ev.get("pc", 1.0e-4)
            miss_m = ev.get("miss_distance_m", ev.get("miss_km", "N/A"))
            tca_str = ev.get("time_to_tca_hours", ev.get("tca", "N/A"))
            return (
                f"CRITICAL CONJUNCTION EMERGENCY: Satellite '{asset_id}' has breached safety limits. "
                f"Hard safety override triggered by close encounter with '{sec_id}' (collision probability "
                f"Pc={pc_val:.2e} exceeding threshold 1.00e-04). Miss distance is {miss_m} m with "
                f"TCA in {tca_str} h. Immediate flight director conjunction assessment required."
            )

        # 2. Compound Risk (Both Health and Debris Elevated)
        if r_h >= 0.50 and r_d >= 0.50:
            top_driver = drivers[0].driver if drivers else "telemetry_and_debris"
            return (
                f"COMPOUND SAFETY CRISIS: Satellite '{asset_id}' is experiencing simultaneous hazards. "
                f"Subsystem telemetry health risk is elevated (r_h={r_h:.2f}, primary driver: {top_driver}), "
                f"while orbital conjunction collision risk is severe (r_d={r_d:.2f}). Noisy-OR safety hazard "
                f"fused to R_safety={r_safety:.2f}. Total Mission Risk Score is {score:.1f} ({level.value}). "
                f"Secondary Earth observation payloads are deferred to conserve spacecraft power."
            )

        # 3. Severe Health Anomaly
        if r_h >= 0.50 or warning_override:
            top_h_driver = next((d.driver for d in drivers if d.module == "health"), "telemetry_channels")
            override_text = " (Persistent health anomaly override applied)" if warning_override else ""
            defer_text = " Secondary imaging payloads deferred." if defer_eo else ""
            return (
                f"SPACECRAFT HEALTH ANOMALY: Satellite '{asset_id}' telemetry anomaly detected on subsystem "
                f"'{top_h_driver}' with elevated health risk r_h={r_h:.2f}{override_text}. "
                f"Total Mission Risk Score is {score:.1f} ({level.value}).{defer_text} "
                f"Flight director telemetry review recommended."
            )

        # 4. Elevated Debris Encounter
        if r_d >= 0.50:
            sec_id = ev.get("secondary_id", "tracked orbital debris")
            return (
                f"ELEVATED CONJUNCTION RISK: Satellite '{asset_id}' orbital screening indicates conjunction "
                f"with {sec_id} (debris collision risk r_d={r_d:.2f}). "
                f"Total Mission Risk Score is {score:.1f} ({level.value}). "
                f"Close approach monitoring escalated."
            )

        # 5. Elevated Disaster Response Tasking
        if r_e >= 0.50 and level in (RiskLevel.WATCH, RiskLevel.WARNING):
            disaster_type = ev.get("disaster_type", "disaster")
            area_km2 = ev.get("flooded_area_km2", ev.get("area_km2", "significant"))
            return (
                f"HIGH-PRIORITY EARTH OBSERVATION TASKING: Active {disaster_type} event detected ({area_km2} km²). "
                f"Spacecraft subsystems and orbit are nominal (r_h={r_h:.2f}, r_d={r_d:.2f}). "
                f"Observation urgency elevates Mission Score to {score:.1f} ({level.value}). "
                f"Target acquisition recommended."
            )

        # 6. Watch Level
        if level == RiskLevel.WATCH:
            top_d = drivers[0].driver if drivers else "minor telemetry drift"
            return (
                f"MISSION WATCH STATUS: Satellite '{asset_id}' operating within tolerable limits with minor "
                f"environmental or telemetry deviation (primary driver: {top_d}). "
                f"Mission Risk Score is {score:.1f} (WATCH). Increased telemetry sampling active."
            )

        # 7. Nominal Level
        return (
            f"NOMINAL MISSION OPERATIONS: All subsystems and orbital parameters for satellite '{asset_id}' "
            f"are operating within normal flight margins (r_h={r_h:.2f}, r_d={r_d:.2f}, r_e={r_e:.2f}). "
            f"Mission Risk Score is {score:.1f} (NOMINAL). No flight director action required."
        )
