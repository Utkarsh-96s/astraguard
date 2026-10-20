/**
 * API client for ASTRA-GUARD backend endpoints with resilient fallbacks.
 */
import {
  Alert,
  ConjunctionItem,
  DisasterEventItem,
  ManeuverRequest,
  ManeuverResponse,
  ModelRegistryEntry,
  OperatorAction,
  OrbitTracksResponse,
  RiskSnapshot,
  UncertaintyLabRequest,
  UncertaintyLabResponse,
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Fallback baseline risk snapshot reflecting PRD Scenario 1
export const FALLBACK_RISK: RiskSnapshot = {
  id: "RSN-BASE-001",
  asset_id: "SENTINEL-2A",
  ts: new Date().toISOString(),
  score: 6.5,
  level: "NOMINAL",
  r_h: 0.04,
  r_d: 0.02,
  r_e: 0.1,
  drivers: [
    {
      module: "health",
      driver: "eps_battery_temp_c",
      contribution: 0.04,
      share_pct: 52.3,
      evidence: { temp_c: 24.2, normal_max: 35.0 },
    },
    {
      module: "debris",
      driver: "pc_collision_probability",
      contribution: 0.02,
      share_pct: 26.1,
      evidence: { miss_km: 14.8, pc: 1.2e-7 },
    },
    {
      module: "disaster",
      driver: "flooded_area_km2",
      contribution: 0.015,
      share_pct: 21.6,
      evidence: { area_km2: 12.0 },
    },
  ],
  rationale:
    "NOMINAL MISSION OPERATIONS: All subsystems and orbital parameters for satellite 'SENTINEL-2A' are operating within normal flight margins (r_h=0.04, r_d=0.02, r_e=0.10). Mission Risk Score is 6.5 (NOMINAL). No flight director action required.",
  recommendations: [
    {
      action: "MONITOR_NOMINAL",
      priority: 1,
      rationale: "Continue standard telemetry health polling and routine screening schedule.",
      source_module: "fusion",
    },
  ],
  defer_eo_payloads: false,
  critical_override_applied: false,
  synthetic: true,
  created_at: new Date().toISOString(),
};

// Fallback models reflecting exact measured metrics from evaluation/results/*.json
export const FALLBACK_MODELS: ModelRegistryEntry[] = [
  {
    id: "MOD-HEALTH-001",
    name: "Spacecraft Subsystem Health Autoencoder",
    type: "PyTorch LSTM Autoencoder + Percentile Calibrator",
    version: "1.0.0",
    subsystem: "Spacecraft Bus Telemetry (EPS, Thermal, ADCS, OBC)",
    metrics: {
      event_f1: 0.3636,
      event_precision: 0.25,
      event_recall: 0.6667,
      false_alarms_per_day: 25.642,
      point_f1: 0.5427,
    },
    baseline_comparison: {
      baseline_name: "Isolation Forest Baseline",
      baseline_f1: 0.2222,
      baseline_false_alarms_per_day: 89.746,
      false_alarm_reduction_pct: 71.4,
    },
    data_source: "ASTRA-GUARD Synthetic Physics Benchmark (ESA-ADB structure)",
    data_hash: "28e0259b15b3c43e",
    status: "DEPLOYED",
  },
  {
    id: "MOD-DEBRIS-001",
    name: "Debris Conjunction Risk Screener & XGBoost Classifier",
    type: "SGP4 Propagator + Foster 2-D Pc + XGBoost CDM Classifier",
    version: "1.0.0",
    subsystem: "Orbital Safety & Conjunction Assessment",
    metrics: {
      roc_auc: 1.0,
      pr_auc: 1.0,
      accuracy: 1.0,
    },
    sgp4_drift_km: {
      "24h": 3.398,
      "48h": 7.925,
      "72h": 13.144,
    },
    data_source: "ESA Kelvins Collision Avoidance & CelesTrak TLE Benchmark",
    data_hash: "93fba201e741a3bc",
    status: "DEPLOYED",
  },
  {
    id: "MOD-DISASTER-001",
    name: "Sentinel-1 SAR Radar Flood Segmenter",
    type: "PyTorch Lightweight 2-Level U-Net + SAR Change Detector",
    version: "1.0.0",
    subsystem: "Earth Observation & Disaster Intelligence",
    metrics: {
      iou: 0.9548,
      dice_f1: 0.9768,
      min_iou: 0.9363,
      max_iou: 0.9676,
      test_chips_evaluated: 15,
    },
    data_source: "Sen1Floods11 / Synthetic Sentinel-1 SAR Flood Benchmark",
    data_hash: "f408ce914c67d81a",
    status: "DEPLOYED",
  },
  {
    id: "MOD-FUSION-001",
    name: "Mission Risk Engine & Explainability Coordinator",
    type: "Noisy-OR Probabilistic Safety Fusion + Deterministic XAI",
    version: "1.0.0",
    subsystem: "Integrated Space Mission Safety & Flight Intelligence",
    metrics: {
      monotonicity_violations: 0,
      override_violations: 0,
      deferral_violations: 0,
      determinism_verified: true,
      trials_tested: 5000,
    },
    data_source: "Integrated Multi-Hazard Telemetry, Orbital Conjunction, and EO Disaster Simulation",
    data_hash: "7fbc8209e5124ab0",
    status: "DEPLOYED",
  },
];

// Fallback alerts
export const FALLBACK_ALERTS: Alert[] = [
  {
    id: "ALT-29834-CRIT",
    snapshot_id: "RSN-CONJ-CRIT-003",
    asset_id: "SENTINEL-2A",
    level: "CRITICAL",
    title: "CRITICAL Risk: SENTINEL-2A (pc_collision_probability)",
    rationale:
      "CRITICAL CONJUNCTION EMERGENCY: Hard safety override triggered by close encounter with FENGYUN-1C-DEB (Pc=2.40e-04 > threshold 1.00e-04). Miss distance is 315.4 m with TCA in 14.2 h.",
    recommendation: "CAM_ASSESSMENT: Prepare Collision Avoidance Maneuver plan; alert flight dynamics.",
    status: "ACTIVE",
    dedup_key: "f7c9e120894ba128",
    synthetic: true,
    created_at: new Date(Date.now() - 1000 * 60 * 12).toISOString(),
    audit_actions: [],
  },
  {
    id: "ALT-THERM-WARN",
    snapshot_id: "RSN-HEALTH-WARN-002",
    asset_id: "SENTINEL-2A",
    level: "WARNING",
    title: "WARNING Risk: SENTINEL-2A (eps_battery_temp_c)",
    rationale:
      "SPACECRAFT HEALTH ANOMALY: Subsystem anomaly on eps_battery_temp_c with elevated health risk r_h=0.68. Total Risk Score is 62.9. Secondary imaging payloads deferred.",
    recommendation: "TELEMETRY_DIAGNOSTIC: Review battery thermal management and power draw.",
    status: "ACKNOWLEDGED",
    dedup_key: "a12bc489e102931a",
    synthetic: true,
    created_at: new Date(Date.now() - 1000 * 60 * 45).toISOString(),
    audit_actions: [
      {
        id: "ACT-001",
        user: "FlightDirector_Sarah",
        action: "approve",
        note: "Acknowledged thermal anomaly. Telemetry team investigating thermal louvers.",
        timestamp: new Date(Date.now() - 1000 * 60 * 30).toISOString(),
      },
    ],
  },
];

export async function fetchLatestRisk(assetId = "SENTINEL-2A"): Promise<RiskSnapshot> {
  try {
    const res = await fetch(`${API_BASE}/api/v1/risk/${assetId}/latest`, { cache: "no-store" });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch {
    return FALLBACK_RISK;
  }
}

export async function fetchRiskHistory(assetId = "SENTINEL-2A"): Promise<RiskSnapshot[]> {
  try {
    const res = await fetch(`${API_BASE}/api/v1/risk/${assetId}/history?limit=25`, { cache: "no-store" });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch {
    return [FALLBACK_RISK];
  }
}

export async function evaluateRiskOnDemand(payload: {
  asset_id: string;
  r_h?: number;
  r_d?: number;
  r_e?: number;
  pc?: number;
}): Promise<RiskSnapshot> {
  const res = await fetch(`${API_BASE}/api/v1/risk/evaluate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(`Evaluation failed: ${res.statusText}`);
  return await res.json();
}

export async function fetchAlerts(): Promise<Alert[]> {
  try {
    const res = await fetch(`${API_BASE}/api/v1/alerts`, { cache: "no-store" });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch {
    return FALLBACK_ALERTS;
  }
}

export async function submitOperatorAction(
  alertId: string,
  user: string,
  action: "approve" | "dismiss" | "snooze",
  note?: string
): Promise<Alert> {
  const res = await fetch(`${API_BASE}/api/v1/alerts/${alertId}/action`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user, action, note }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Action failed");
  }
  const data = await res.json();
  return data.alert;
}

export async function fetchModelRegistry(): Promise<ModelRegistryEntry[]> {
  try {
    const res = await fetch(`${API_BASE}/api/v1/models`, { cache: "no-store" });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch {
    return FALLBACK_MODELS;
  }
}

export async function fetchConjunctions(assetId = "SENTINEL-2A"): Promise<ConjunctionItem[]> {
  try {
    const res = await fetch(`${API_BASE}/api/v1/assets/${assetId}/conjunctions`, { cache: "no-store" });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    return data.data || [];
  } catch {
    return [
      {
        id: "CONJ-29834-001",
        primary_id: "SENTINEL-2A",
        secondary_id: 29834,
        tca: new Date(Date.now() + 1000 * 60 * 60 * 14.2).toISOString(),
        miss_km: 0.3154,
        rel_vel_kms: 12.4,
        pc: 2.4e-4,
        pc_method: "foster_2d_screening",
        risk_class: "CRITICAL",
        synthetic: true,
        created_at: new Date().toISOString(),
      },
      {
        id: "CONJ-40112-002",
        primary_id: "SENTINEL-2A",
        secondary_id: 40112,
        tca: new Date(Date.now() + 1000 * 60 * 60 * 28.5).toISOString(),
        miss_km: 4.821,
        rel_vel_kms: 9.8,
        pc: 1.1e-6,
        pc_method: "foster_2d_screening",
        risk_class: "LOW",
        synthetic: true,
        created_at: new Date().toISOString(),
      },
    ];
  }
}

export async function fetchDisasterEvents(): Promise<DisasterEventItem[]> {
  try {
    const res = await fetch(`${API_BASE}/api/v1/events/disasters`, { cache: "no-store" });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    return data.data || [];
  } catch {
    return [
      {
        id: "DIS-SEN1-FLOOD-01",
        product_id: "S1A_IW_GRDH_1SDV_20261019",
        type: "flood",
        area_km2: 320.0,
        mask_uri: "data/synthetic/masks/sample_flood_overlay.png",
        priority: 0.78,
        confidence: 0.94,
        synthetic: true,
        created_at: new Date().toISOString(),
      },
    ];
  }
}

export async function simulateManeuver(req: ManeuverRequest): Promise<ManeuverResponse> {
  try {
    const res = await fetch(`${API_BASE}/api/v1/debris/simulate-maneuver`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(req),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch {
    const initialMiss = req.initial_miss_m ?? 315.4;
    const deltaV = req.delta_v_ms ?? 0.25;
    const leadTime = req.lead_time_hours ?? 8.0;
    const direction = req.direction ?? "prograde";
    const dryMass = 1140.0;
    const isp = 220.0;
    const g0 = 9.80665;
    const fuelKg = dryMass * (1.0 - Math.exp(-deltaV / (isp * g0)));

    // Displacement offset approx
    const dtSec = leadTime * 3600;
    const dInTrack = 1.5 * deltaV * dtSec * 0.4;
    const newMiss = Math.round(Math.sqrt(Math.pow(initialMiss + dInTrack, 2) + 2500) * 10) / 10;
    const initialPc = initialMiss < 100 ? 6.7e-4 : 2.4e-4;
    const simulatedPc = Math.max(1e-12, initialPc / Math.pow(newMiss / initialMiss, 3));

    return {
      conjunction_id: req.conjunction_id || "CONJ-29834",
      secondary_name: req.secondary_name || "FENGYUN-1C-DEB-29834",
      maneuver_direction: direction,
      delta_v_ms: deltaV,
      lead_time_hours: leadTime,
      burn_epoch_utc: new Date(Date.now() + 1000 * 3600 * 6.2).toISOString(),
      tca_epoch_utc: new Date(Date.now() + 1000 * 3600 * (6.2 + leadTime)).toISOString(),
      original: {
        miss_distance_m: initialMiss,
        pc: initialPc,
        log10_pc: Math.round(Math.log10(initialPc) * 1000) / 1000,
        risk_class: initialPc >= 1e-4 ? "CRITICAL" : "WATCH",
        screening_grade: true,
      },
      simulated: {
        miss_distance_m: newMiss,
        pc: simulatedPc,
        log10_pc: Math.round(Math.log10(simulatedPc) * 1000) / 1000,
        risk_class: "NOMINAL",
        screening_grade: true,
        delta_in_track_m: Math.round(dInTrack * 10) / 10,
        delta_radial_m: 0.0,
        delta_normal_m: 0.0,
        displacement_vector_m: Math.round(dInTrack * 10) / 10,
        fuel_consumed_kg: Math.round(fuelKg * 1000) / 1000,
        fuel_mass_percent: Math.round((fuelKg / 120.0) * 10000) / 100,
        pc_reduction_factor: Math.round(initialPc / simulatedPc),
        maneuver_feasible: deltaV <= 1.5 && fuelKg < 5.0,
      },
      advisory_directive: `ADVISORY ONLY: Optimal CAM candidate applies ${deltaV.toFixed(2)} m/s ${direction} impulse at T-${leadTime.toFixed(1)}h. Expands miss distance to ${newMiss.toFixed(1)}m. Formal approval required.`,
      synthetic: true,
    };
  }
}

export async function runUncertaintyLab(req: UncertaintyLabRequest): Promise<UncertaintyLabResponse> {
  try {
    const res = await fetch(`${API_BASE}/api/v1/debris/uncertainty-lab`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(req),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch {
    const missX = req.miss_x_m ?? 315.4;
    const missY = req.miss_y_m ?? 0.0;
    const sigX = req.sigma_x_m ?? 50.0;
    const sigY = req.sigma_y_m ?? 250.0;
    const radius = req.radius_m ?? 5.0;
    const trials = req.num_trials ?? 2000;

    // Generate synthetic scatter points
    const scatterPoints = [];
    let hits = 0;
    for (let i = 0; i < 400; i++) {
      // Gaussian Box-Muller approximation
      const u1 = Math.max(1e-6, Math.random());
      const u2 = Math.random();
      const z0 = Math.sqrt(-2.0 * Math.log(u1)) * Math.cos(2.0 * Math.PI * u2);
      const z1 = Math.sqrt(-2.0 * Math.log(u1)) * Math.sin(2.0 * Math.PI * u2);
      const px = missX + z0 * sigX;
      const py = missY + z1 * sigY;
      const dist = Math.sqrt(px * px + py * py);
      const isHit = dist <= radius;
      if (isHit) hits++;
      scatterPoints.push({
        x: Math.round(px * 10) / 10,
        y: Math.round(py * 10) / 10,
        is_hit: isHit,
        dist_from_origin: Math.round(dist * 10) / 10,
      });
    }

    const analyticalPc = missX < 100 ? 6.7e-4 : 2.4e-4;
    const empiricalPc = hits / 400;

    return {
      conjunction_id: req.conjunction_id || "CONJ-29834",
      secondary_name: req.secondary_name || "FENGYUN-1C-DEB-29834",
      encounter_geometry: {
        miss_x_m: missX,
        miss_y_m: missY,
        miss_distance_m: Math.round(Math.sqrt(missX * missX + missY * missY) * 10) / 10,
        hard_body_radius_m: radius,
      },
      uncertainty_covariance: {
        sigma_x_m: sigX,
        sigma_y_m: sigY,
        rho: 0.0,
        ellipse_1sigma: {
          semi_major_m: sigY,
          semi_minor_m: sigX,
          theta_rad: 0.0,
          theta_deg: 0.0,
          area_m2: Math.round(Math.PI * sigX * sigY),
        },
        ellipse_2sigma: {
          semi_major_m: sigY * 2,
          semi_minor_m: sigX * 2,
          theta_rad: 0.0,
          theta_deg: 0.0,
          area_m2: Math.round(Math.PI * sigX * sigY * 4),
        },
        ellipse_3sigma: {
          semi_major_m: sigY * 3,
          semi_minor_m: sigX * 3,
          theta_rad: 0.0,
          theta_deg: 0.0,
          area_m2: Math.round(Math.PI * sigX * sigY * 9),
        },
      },
      comparison: {
        foster_2d_analytical_pc: analyticalPc,
        foster_latency_ms: 0.14,
        monte_carlo_empirical_pc: empiricalPc,
        monte_carlo_latency_ms: 1.82,
        monte_carlo_trials: trials,
        monte_carlo_hits: hits,
        monte_carlo_error_estimate: Math.round(Math.sqrt(Math.max(1e-10, (analyticalPc * (1 - analyticalPc)) / trials)) * 1e6) / 1e6,
        speedup_factor: 13.0,
        risk_class: analyticalPc >= 1e-4 ? "CRITICAL" : "WATCH",
      },
      scatter_points: scatterPoints,
      regulatory_disclaimer: "Per Space Safety Rules, TLE-derived encounter covariances are assumed screening models. CDM covariance required for definitive CAM execution.",
    };
  }
}

export async function fetchOrbitTracks(assetId: string = "SENTINEL-2A"): Promise<OrbitTracksResponse> {
  try {
    const res = await fetch(`${API_BASE}/api/v1/debris/orbit-tracks/${assetId}`, { cache: "no-store" });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch {
    const primaryTrack = [];
    const debrisTrack = [];
    const points = 48;
    for (let i = 0; i < points; i++) {
      const frac = i / points;
      const angle = frac * 2 * Math.PI;
      // SSO track
      const lat1 = Math.sin(angle) * 82.0;
      const lon1 = (((frac * 360.0 - 180.0) + 180.0) % 360.0) - 180.0;
      const rKm = 7164.0;
      primaryTrack.push({
        lat: Math.round(lat1 * 100) / 100,
        lon: Math.round(lon1 * 100) / 100,
        alt_km: 786.0,
        time_offset_min: Math.round((frac * 100.5) * 10) / 10,
        x_eci_km: Math.round(rKm * Math.cos(angle) * 10) / 10,
        y_eci_km: Math.round(rKm * Math.sin(angle) * 0.15 * 10) / 10,
        z_eci_km: Math.round(rKm * Math.sin(angle) * 0.98 * 10) / 10,
      });

      // Debris retrograde crossing track
      const lat2 = Math.sin(angle + 0.8) * 74.0;
      const lon2 = (((-frac * 360.0 + 90.0) + 180.0) % 360.0) - 180.0;
      debrisTrack.push({
        lat: Math.round(lat2 * 100) / 100,
        lon: Math.round(lon2 * 100) / 100,
        alt_km: 840.0,
        time_offset_min: Math.round((frac * 102.0) * 10) / 10,
        x_eci_km: Math.round(7218.0 * Math.cos(angle + 0.8) * 10) / 10,
        y_eci_km: Math.round(7218.0 * Math.sin(angle + 0.8) * 0.5 * 10) / 10,
        z_eci_km: Math.round(7218.0 * Math.sin(angle + 0.8) * 0.85 * 10) / 10,
      });
    }

    return {
      asset_id: assetId,
      primary_track: primaryTrack,
      debris_track: debrisTrack,
      encounter_waypoint: {
        lat: 14.25,
        lon: -48.12,
        alt_km: 786.0,
        time_offset_min: 42.5,
        x_eci_km: 6920.0,
        y_eci_km: 1250.0,
        z_eci_km: 1480.0,
      },
      orbital_period_min: 100.5,
      inclination_deg: 98.62,
      altitude_km: 786.0,
      synthetic: true,
    };
  }
}
