/**
 * Shared TypeScript type definitions for ASTRA-GUARD web platform.
 */

export type RiskLevel = "NOMINAL" | "WATCH" | "WARNING" | "CRITICAL";

export type AlertStatus = "ACTIVE" | "ACKNOWLEDGED" | "DISMISSED" | "SNOOZED";

export interface RiskDriver {
  module: "health" | "debris" | "disaster" | "cross_effect";
  driver: string;
  contribution: number;
  share_pct: number;
  evidence: Record<string, unknown>;
}

export interface Recommendation {
  action: string;
  priority: number;
  rationale: string;
  source_module: string;
}

export interface RiskSnapshot {
  id: string;
  asset_id: string;
  ts: string;
  score: number;
  level: RiskLevel;
  r_h: number;
  r_d: number;
  r_e: number;
  drivers: RiskDriver[];
  rationale: string;
  recommendations: Recommendation[];
  defer_eo_payloads: boolean;
  critical_override_applied: boolean;
  synthetic: boolean;
  created_at: string;
}

export interface OperatorAction {
  id: string;
  alert_id?: string;
  user: string;
  action: "approve" | "dismiss" | "snooze" | string;
  note?: string | null;
  timestamp: string;
}

export interface Alert {
  id: string;
  snapshot_id: string;
  asset_id?: string;
  level: RiskLevel;
  title: string;
  rationale: string;
  recommendation: string;
  status: AlertStatus;
  dedup_key: string;
  synthetic: boolean;
  created_at: string;
  audit_actions?: OperatorAction[];
}

export interface ModelRegistryEntry {
  id: string;
  name: string;
  type: string;
  version: string;
  subsystem: string;
  metrics: Record<string, number | boolean | string>;
  baseline_comparison?: Record<string, number | string>;
  sgp4_drift_km?: Record<string, number>;
  data_source: string;
  data_hash: string;
  status: string;
}

export interface ConjunctionItem {
  id: string;
  primary_id: string;
  secondary_id: number;
  tca: string;
  miss_km: number;
  rel_vel_kms: number;
  pc: number;
  pc_method: string;
  risk_class: string;
  synthetic: boolean;
  created_at: string;
}

export interface DisasterEventItem {
  id: string;
  product_id?: string | null;
  type: string;
  area_km2: number;
  mask_uri?: string | null;
  priority: number;
  confidence: number;
  synthetic: boolean;
  created_at: string;
}

export interface TelemetryReading {
  channel: string;
  value: number;
  ts: string;
  synthetic: boolean;
}

export interface ManeuverRequest {
  conjunction_id?: string;
  secondary_name?: string;
  initial_miss_m?: number;
  relative_velocity_kms?: number;
  delta_v_ms?: number;
  direction?: "prograde" | "retrograde" | "radial_out" | "radial_in" | "out_of_plane";
  lead_time_hours?: number;
}

export interface ManeuverState {
  miss_distance_m: number;
  pc: number;
  log10_pc: number;
  risk_class: string;
  screening_grade: boolean;
  delta_in_track_m?: number;
  delta_radial_m?: number;
  delta_normal_m?: number;
  displacement_vector_m?: number;
  fuel_consumed_kg?: number;
  fuel_mass_percent?: number;
  pc_reduction_factor?: number;
  maneuver_feasible?: boolean;
}

export interface ManeuverResponse {
  conjunction_id: string;
  secondary_name: string;
  maneuver_direction: string;
  delta_v_ms: number;
  lead_time_hours: number;
  burn_epoch_utc: string;
  tca_epoch_utc: string;
  original: ManeuverState;
  simulated: ManeuverState;
  advisory_directive: string;
  synthetic: boolean;
}

export interface UncertaintyLabRequest {
  conjunction_id?: string;
  secondary_name?: string;
  miss_x_m?: number;
  miss_y_m?: number;
  sigma_x_m?: number;
  sigma_y_m?: number;
  rho?: number;
  radius_m?: number;
  num_trials?: number;
}

export interface UncertaintyEllipse {
  semi_major_m: number;
  semi_minor_m: number;
  theta_rad: number;
  theta_deg: number;
  area_m2: number;
}

export interface UncertaintyScatterPoint {
  x: number;
  y: number;
  is_hit: boolean;
  dist_from_origin: number;
}

export interface UncertaintyLabResponse {
  conjunction_id: string;
  secondary_name: string;
  encounter_geometry: {
    miss_x_m: number;
    miss_y_m: number;
    miss_distance_m: number;
    hard_body_radius_m: number;
  };
  uncertainty_covariance: {
    sigma_x_m: number;
    sigma_y_m: number;
    rho: number;
    ellipse_1sigma: UncertaintyEllipse;
    ellipse_2sigma: UncertaintyEllipse;
    ellipse_3sigma: UncertaintyEllipse;
  };
  comparison: {
    foster_2d_analytical_pc: number;
    foster_latency_ms: number;
    monte_carlo_empirical_pc: number;
    monte_carlo_latency_ms: number;
    monte_carlo_trials: number;
    monte_carlo_hits: number;
    monte_carlo_error_estimate: number;
    speedup_factor: number;
    risk_class: string;
  };
  scatter_points: UncertaintyScatterPoint[];
  regulatory_disclaimer: string;
}

export interface OrbitPoint {
  lat: number;
  lon: number;
  alt_km: number;
  time_offset_min: number;
  x_eci_km: number;
  y_eci_km: number;
  z_eci_km: number;
}

export interface OrbitTracksResponse {
  asset_id: string;
  primary_track: OrbitPoint[];
  debris_track: OrbitPoint[];
  encounter_waypoint: OrbitPoint;
  orbital_period_min: number;
  inclination_deg: number;
  altitude_km: number;
  synthetic: boolean;
}

export interface DisasterScenario {
  id: string;
  name: string;
  location: string;
  country: string;
  sensor: string;
  sensor_type: string;
  polarization: string;
  resolution_m: number;
  acquisition_date: string;
  disaster_type: string;
  area_km2: number;
  priority: number;
  confidence: number;
  mean_iou: number;
  mean_dice: number;
  backscatter_drop_db: number;
  geojson_footprint: {
    type: string;
    geometry: {
      type: string;
      coordinates: number[][][];
    };
    properties: {
      name: string;
      bbox: number[];
    };
  };
  infrastructure_impact: {
    substations_affected: number;
    bridges_critical: number;
    hospitals_warning: number;
    agricultural_hectares: number;
    population_exposed: number;
  };
  priority_drivers: {
    factor: string;
    weight: number;
    score: number;
  }[];
  description: string;
}

export interface DisasterDeckResponse {
  count: number;
  scenarios: DisasterScenario[];
  synthetic: boolean;
}

export interface FleetSubsystems {
  eps: { battery_temp_c: number; bus_voltage_v: number; solar_current_a: number; status: string };
  thermal: { payload_temp_c: number; radiator_temp_c: number; status: string };
  adcs: { wheel_rpm: number; attitude_error_deg: number; status: string };
  obc: { cpu_load_pct: number; memory_used_pct: number; status: string };
  payload: { active_instrument: string; duty_cycle_pct: number; status: string };
}

export interface FleetAsset {
  id: string;
  name: string;
  norad_id: number;
  type: string;
  orbit: {
    altitude_km: number;
    inclination_deg: number;
    period_min: number;
    local_time_descending_node: string;
  };
  subsystems: FleetSubsystems;
  health_score: number;
  risk_level: string;
}

export interface CrossConjunctionItem {
  id: string;
  primary_asset_id: string;
  primary_name: string;
  secondary_name: string;
  secondary_norad_id: number;
  tca_hours: number;
  miss_distance_m: number;
  relative_velocity_kms: number;
  pc: number;
  risk_class: string;
  screening_grade: boolean;
}

export interface ConstellationMatrixResponse {
  fleet_size: number;
  aggregate_health_score: number;
  fleet_risk_level: string;
  assets: FleetAsset[];
  cross_conjunctions: CrossConjunctionItem[];
  active_threats_count: number;
  timestamp: string;
}

export interface LiveTelemetryPacket {
  asset_id: string;
  timestamp: string;
  sequence_number: number;
  channels: {
    eps_battery_temp_c: number;
    eps_bus_voltage_v: number;
    eps_solar_array_current_a: number;
    adcs_reaction_wheel_rpm: number;
    adcs_attitude_jitter_deg: number;
    obc_cpu_load_pct: number;
  };
  synthetic: boolean;
}

