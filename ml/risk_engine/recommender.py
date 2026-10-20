"""Rule-based operator recommendation engine requiring human sign-off."""
from datetime import UTC, datetime
from typing import Any

from ml.risk_engine.schemas import OperatorActionType, Recommendation, RiskLevel


class RecommendationEngine:
    """Evaluates mission conditions to formulate human-in-the-loop recommendations."""

    def generate_recommendations(
        self,
        asset_id: str,
        score: float,
        level: RiskLevel,
        r_h: float,
        r_d: float,
        r_e: float,
        critical_override: bool,
        warning_override: bool,
        defer_eo: bool,
        evidence: dict[str, Any] | None = None,
        now: datetime | None = None,
    ) -> list[Recommendation]:
        """Generate structured operational recommendations based on mission state."""
        ev = evidence or {}
        timestamp = now or datetime.now(UTC)
        recs: list[Recommendation] = []

        # 1. Critical Conjunction / Collision Avoidance
        pc_val = ev.get("pc", 0.0)
        if critical_override or pc_val >= 1.0e-4 or r_d >= 0.70:
            sec_obj = ev.get("secondary_id", ev.get("secondary_object", "tracked orbital debris"))
            miss_m = ev.get("miss_distance_m", ev.get("miss_km", "unknown"))
            tca_h = ev.get("time_to_tca_hours", ev.get("tca", "TBD"))

            recs.append(
                Recommendation(
                    action_code="CAM_ASSESSMENT",
                    title="Execute Conjunction Assessment & Maneuver Analysis",
                    description=(
                        f"Close approach detected with {sec_obj} (miss distance: {miss_m} m, TCA: {tca_h} h). "
                        f"Perform B-plane encounter verification, evaluate propellant margins, and compute screening "
                        f"differential-drag or chemical thruster ΔV avoidance maneuver. Advisory only: requires explicit "
                        f"operator sign-off before uplink."
                    ),
                    priority="critical" if (critical_override or pc_val >= 1.0e-4) else "high",
                    required_operator_action=OperatorActionType.APPROVE,
                    rationale=f"Conjunction collision risk r_d={r_d:.2f} (Pc={pc_val:.2e}).",
                    subsystem_or_target=str(sec_obj),
                    created_at=timestamp,
                )
            )

        # 2. Severe Spacecraft Health Anomaly (Load Shedding / Standby)
        if r_h >= 0.85 or warning_override:
            subsystem = ev.get("anomaly_subsystem", ev.get("primary_channel", "bus_electronics"))
            recs.append(
                Recommendation(
                    action_code="LOAD_SHED_SAFE_MODE",
                    title="Initiate Non-Essential Payload Load Shedding",
                    description=(
                        f"Severe telemetry deviation on subsystem '{subsystem}'. Command high-draw science and "
                        f"imaging instruments into low-power safe standby to stabilize battery state-of-charge "
                        f"and mitigate thermal stress."
                    ),
                    priority="high",
                    required_operator_action=OperatorActionType.APPROVE,
                    rationale=f"Spacecraft health anomaly score r_h={r_h:.2f} exceeds critical safe operating margins.",
                    subsystem_or_target=str(subsystem),
                    created_at=timestamp,
                )
            )
        elif r_h >= 0.50:
            subsystem = ev.get("anomaly_subsystem", "telemetry_sensors")
            recs.append(
                Recommendation(
                    action_code="TELEMETRY_DIAGNOSTIC",
                    title="Command High-Rate Diagnostic Telemetry Downlink",
                    description=(
                        f"Elevated telemetry residuals on '{subsystem}'. Switch telemetry packet generation to high-rate "
                        f"engineering mode during upcoming ground station pass for diagnostic analysis."
                    ),
                    priority="medium",
                    required_operator_action=OperatorActionType.APPROVE,
                    rationale=f"Telemetry drift detected (r_h={r_h:.2f}) approaching warning threshold.",
                    subsystem_or_target=str(subsystem),
                    created_at=timestamp,
                )
            )

        # 3. Cross-Effect: Defer Earth Observation Tasks
        if defer_eo and r_e > 0.05:
            recs.append(
                Recommendation(
                    action_code="DEFER_EO_PAYLOAD",
                    title="Defer Scheduled Earth Observation Payloads",
                    description=(
                        f"Automatic safety interlock engaged: Spacecraft health risk (r_h={r_h:.2f}) exceeds the 0.50 "
                        f"cutoff. Postpone scheduled optical/SAR payload imaging passes until the bus anomaly is resolved."
                    ),
                    priority="high",
                    required_operator_action=OperatorActionType.APPROVE,
                    rationale="Architecture §5.4 cross-system constraint: protect spacecraft bus before payload operations.",
                    subsystem_or_target="EO_PAYLOAD_MANAGER",
                    created_at=timestamp,
                )
            )

        # 4. Earth Observation Tasking (When Spacecraft is Healthy)
        if not defer_eo and r_e >= 0.45:
            event_id = ev.get("disaster_event_id", ev.get("event_id", "DISASTER-TARGET-001"))
            area_km2 = ev.get("flooded_area_km2", ev.get("area_km2", "observed region"))
            recs.append(
                Recommendation(
                    action_code="TASK_DISASTER_IMAGERY",
                    title="Authorize Disaster Response Target Acquisition",
                    description=(
                        f"Inundation event detected ({area_km2} km²). Target is within upcoming access swath. "
                        f"Authorize Earth observation payload schedule for emergency response mapping."
                    ),
                    priority="medium",
                    required_operator_action=OperatorActionType.APPROVE,
                    rationale=f"Disaster observation priority is elevated (r_e={r_e:.2f}) with healthy spacecraft bus.",
                    subsystem_or_target=str(event_id),
                    created_at=timestamp,
                )
            )

        # 5. Routine Baseline Monitoring (Nominal)
        if not recs:
            recs.append(
                Recommendation(
                    action_code="MONITOR_NOMINAL",
                    title="Maintain Routine Autonomous Flight Operations",
                    description=(
                        f"All subsystems on '{asset_id}' are nominal. Maintain scheduled mission timeline and "
                        f"routine ground station contact cycles."
                    ),
                    priority="low",
                    required_operator_action=OperatorActionType.DISMISS,
                    rationale="Mission parameters within nominal 3-sigma tolerance envelopes.",
                    subsystem_or_target=asset_id,
                    created_at=timestamp,
                )
            )

        return recs
