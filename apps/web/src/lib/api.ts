/**
 * API client for ASTRA-GUARD backend endpoints with resilient fallbacks.
 */
import {
  Alert,
  ConjunctionItem,
  ConstellationMatrixResponse,
  DisasterDeckResponse,
  DisasterEventItem,
  DisasterScenario,
  IncidentReportData,
  LiveTelemetryPacket,
  ManeuverRequest,
  ManeuverResponse,
  ModelRegistryEntry,
  ObservationTaskingPlan,
  OperatorAction,
  OrbitTracksResponse,
  RiskSnapshot,
  TrustLayerMetrics,
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

export async function fetchDisasterDeck(): Promise<DisasterDeckResponse> {
  try {
    const res = await fetch(`${API_BASE}/api/v1/events/disaster-deck`, { cache: "no-store" });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch {
    return {
      count: 4,
      scenarios: [
        {
          id: "DIS-EMILIA-FLOOD-2023",
          name: "Emilia-Romagna Flash & River Inundation",
          location: "Emilia-Romagna, Italy",
          country: "Italy",
          sensor: "Sentinel-1 C-SAR (Synthetic Aperture Radar)",
          sensor_type: "radar",
          polarization: "VV + VH Dual-Pol",
          resolution_m: 10.0,
          acquisition_date: "2023-05-18T05:32:00Z",
          disaster_type: "flood",
          area_km2: 480.0,
          priority: 0.88,
          confidence: 0.96,
          mean_iou: 0.9548,
          mean_dice: 0.9768,
          backscatter_drop_db: -4.2,
          geojson_footprint: {
            type: "Feature",
            geometry: {
              type: "Polygon",
              coordinates: [
                [
                  [11.85, 44.3],
                  [12.35, 44.3],
                  [12.35, 44.65],
                  [11.85, 44.65],
                  [11.85, 44.3],
                ],
              ],
            },
            properties: {
              name: "Bologna-Ravenna-Faenza Basin",
              bbox: [11.85, 44.3, 12.35, 44.65],
            },
          },
          infrastructure_impact: {
            substations_affected: 14,
            bridges_critical: 28,
            hospitals_warning: 3,
            agricultural_hectares: 12400.0,
            population_exposed: 185000,
          },
          priority_drivers: [
            {"factor": "Inundated Extent (480 km²)", "weight": 0.35, "score": 0.35},
            {"factor": "Critical Energy & Transport Nodes", "weight": 0.25, "score": 0.23},
            {"factor": "Agricultural Economic Risk", "weight": 0.2, "score": 0.18},
            {"factor": "Sensor Cloud Penetration (SAR All-Weather)", "weight": 0.2, "score": 0.12},
          ],
          description: "Catastrophic river overflows triggered by 36 hours of extreme precipitation across 23 river basins.",
        },
        {
          id: "DIS-BRAHMAPUTRA-01",
          name: "Brahmaputra River Basin Monsoonal Surge",
          location: "Assam, India",
          country: "India",
          sensor: "Sentinel-1 C-SAR",
          sensor_type: "radar",
          polarization: "Dual-Pol VV+VH",
          resolution_m: 10.0,
          acquisition_date: "2026-10-19T00:15:00Z",
          disaster_type: "flood",
          area_km2: 320.0,
          priority: 0.78,
          confidence: 0.94,
          mean_iou: 0.942,
          mean_dice: 0.9701,
          backscatter_drop_db: -3.8,
          geojson_footprint: {
            type: "Feature",
            geometry: {
              type: "Polygon",
              coordinates: [
                [
                  [85.0, 20.0],
                  [85.5, 20.0],
                  [85.5, 20.5],
                  [85.0, 20.5],
                  [85.0, 20.0],
                ],
              ],
            },
            properties: {
              name: "Brahmaputra Flood Plain",
              bbox: [85.0, 20.0, 85.5, 20.5],
            },
          },
          infrastructure_impact: {
            substations_affected: 8,
            bridges_critical: 19,
            hospitals_warning: 2,
            agricultural_hectares: 8900.0,
            population_exposed: 95000,
          },
          priority_drivers: [
            {"factor": "Inundated Extent (320 km²)", "weight": 0.35, "score": 0.28},
            {"factor": "High Population Vulnerability", "weight": 0.25, "score": 0.24},
            {"factor": "River Embankment Breaches", "weight": 0.2, "score": 0.16},
            {"factor": "Repeat Optical Cloud Cover", "weight": 0.2, "score": 0.1},
          ],
          description: "Monsoonal river expansion inundating agricultural lowlands and low-lying river islands.",
        },
        {
          id: "DIS-GREECE-EVROS-2023",
          name: "Evros Megafire & Dadia Forest Burn Scar",
          location: "Evros, Greece",
          country: "Greece",
          sensor: "Sentinel-2 MSI (Multi-Spectral Instrument)",
          sensor_type: "optical",
          polarization: "SWIR-2 / NIR / Red Normalized Burn Ratio",
          resolution_m: 10.0,
          acquisition_date: "2023-08-28T09:12:00Z",
          disaster_type: "wildfire",
          area_km2: 935.0,
          priority: 0.94,
          confidence: 0.98,
          mean_iou: 0.961,
          mean_dice: 0.9802,
          backscatter_drop_db: 0.0,
          geojson_footprint: {
            type: "Feature",
            geometry: {
              type: "Polygon",
              coordinates: [
                [
                  [25.8, 40.85],
                  [26.4, 40.85],
                  [26.4, 41.35],
                  [25.8, 41.35],
                  [25.8, 40.85],
                ],
              ],
            },
            properties: {
              name: "Evros & Dadia Biosphere Reserve",
              bbox: [25.8, 40.85, 26.4, 41.35],
            },
          },
          infrastructure_impact: {
            substations_affected: 6,
            bridges_critical: 8,
            hospitals_warning: 1,
            agricultural_hectares: 34000.0,
            population_exposed: 42000,
          },
          priority_drivers: [
            {"factor": "Massive Burn Scar Extent (935 km²)", "weight": 0.4, "score": 0.39},
            {"factor": "Protected Biosphere Destruction", "weight": 0.25, "score": 0.25},
            {"factor": "Border Region Transport Corridor", "weight": 0.2, "score": 0.18},
            {"factor": "dNBR Burn Severity Index", "weight": 0.15, "score": 0.12},
          ],
          description: "Largest single recorded wildfire in EU history, consuming protected black vulture habitat.",
        },
        {
          id: "DIS-VALENCIA-FLASH-2024",
          name: "Valencia DANA Flash Flood & Ravine Torrent",
          location: "Valencia, Spain",
          country: "Spain",
          sensor: "Sentinel-1 C-SAR + Sentinel-2 MSI Multi-Sensor Fusion",
          sensor_type: "radar_optical_fusion",
          polarization: "Dual-Pol + RGB/NIR",
          resolution_m: 10.0,
          acquisition_date: "2024-10-30T06:14:00Z",
          disaster_type: "flood",
          area_km2: 215.0,
          priority: 0.84,
          confidence: 0.95,
          mean_iou: 0.948,
          mean_dice: 0.9734,
          backscatter_drop_db: -5.1,
          geojson_footprint: {
            type: "Feature",
            geometry: {
              type: "Polygon",
              coordinates: [
                [
                  [-0.55, 39.3],
                  [-0.25, 39.3],
                  [-0.25, 39.6],
                  [-0.55, 39.6],
                  [-0.55, 39.3],
                ],
              ],
            },
            properties: {
              name: "Rambla del Poyo & Horta Sud",
              bbox: [-0.55, 39.3, -0.25, 39.6],
            },
          },
          infrastructure_impact: {
            substations_affected: 22,
            bridges_critical: 41,
            hospitals_warning: 5,
            agricultural_hectares: 7200.0,
            population_exposed: 240000,
          },
          priority_drivers: [
            {"factor": "High Urban Population Density", "weight": 0.35, "score": 0.33},
            {"factor": "Critical Highway & Rail Cutoffs", "weight": 0.25, "score": 0.24},
            {"factor": "Flash Surge Inundation", "weight": 0.25, "score": 0.17},
            {"factor": "Rapid Cloud Clearing Multi-Sensor", "weight": 0.15, "score": 0.1},
          ],
          description: "Isolated high-altitude depression (DANA) causing unprecedented ravine surges across southern Valencia.",
        },
      ],
      synthetic: true,
    };
  }
}

export async function fetchDisasterScenario(eventId: string): Promise<DisasterScenario> {
  try {
    const res = await fetch(`${API_BASE}/api/v1/events/disaster-deck/${eventId}`, { cache: "no-store" });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch {
    const deck = await fetchDisasterDeck();
    return deck.scenarios.find((s) => s.id === eventId) || deck.scenarios[0];
  }
}

export async function fetchConstellationMatrix(): Promise<ConstellationMatrixResponse> {
  try {
    const res = await fetch(`${API_BASE}/api/v1/assets/constellation-matrix`, { cache: "no-store" });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch {
    return {
      fleet_size: 3,
      aggregate_health_score: 9.73,
      fleet_risk_level: "NOMINAL",
      assets: [
        {
          id: "SENTINEL-2A",
          name: "Sentinel-2A (Optical MSI)",
          norad_id: 40697,
          type: "Optical Earth Observation",
          orbit: {
            altitude_km: 786.0,
            inclination_deg: 98.62,
            period_min: 100.5,
            local_time_descending_node: "10:30 AM",
          },
          subsystems: {
            eps: { battery_temp_c: 24.2, bus_voltage_v: 28.4, solar_current_a: 34.2, status: "NOMINAL" },
            thermal: { payload_temp_c: 18.2, radiator_temp_c: -12.4, status: "NOMINAL" },
            adcs: { wheel_rpm: 2450, attitude_error_deg: 0.002, status: "NOMINAL" },
            obc: { cpu_load_pct: 28, memory_used_pct: 42, status: "NOMINAL" },
            payload: { active_instrument: "MSI Multi-Spectral", duty_cycle_pct: 38, status: "ACTIVE" },
          },
          health_score: 9.8,
          risk_level: "NOMINAL",
        },
        {
          id: "SENTINEL-1A",
          name: "Sentinel-1A (C-SAR Radar)",
          norad_id: 39634,
          type: "Synthetic Aperture Radar",
          orbit: {
            altitude_km: 693.0,
            inclination_deg: 98.18,
            period_min: 98.6,
            local_time_descending_node: "06:00 PM",
          },
          subsystems: {
            eps: { battery_temp_c: 26.5, bus_voltage_v: 28.1, solar_current_a: 42.0, status: "NOMINAL" },
            thermal: { payload_temp_c: 22.0, radiator_temp_c: -8.5, status: "NOMINAL" },
            adcs: { wheel_rpm: 3120, attitude_error_deg: 0.004, status: "NOMINAL" },
            obc: { cpu_load_pct: 48, memory_used_pct: 56, status: "NOMINAL" },
            payload: { active_instrument: "C-SAR Interferometric Wide", duty_cycle_pct: 65, status: "ACTIVE" },
          },
          health_score: 9.5,
          risk_level: "NOMINAL",
        },
        {
          id: "SENTINEL-3A",
          name: "Sentinel-3A (OLCI & SLSTR)",
          norad_id: 41335,
          type: "Ocean & Land Environment",
          orbit: {
            altitude_km: 814.5,
            inclination_deg: 98.65,
            period_min: 101.2,
            local_time_descending_node: "10:00 AM",
          },
          subsystems: {
            eps: { battery_temp_c: 22.8, bus_voltage_v: 28.6, solar_current_a: 31.8, status: "NOMINAL" },
            thermal: { payload_temp_c: -196.0, radiator_temp_c: -18.2, status: "NOMINAL" },
            adcs: { wheel_rpm: 2100, attitude_error_deg: 0.002, status: "NOMINAL" },
            obc: { cpu_load_pct: 24, memory_used_pct: 38, status: "NOMINAL" },
            payload: { active_instrument: "OLCI / SLSTR Dual-Optics", duty_cycle_pct: 45, status: "ACTIVE" },
          },
          health_score: 9.9,
          risk_level: "NOMINAL",
        },
      ],
      cross_conjunctions: [
        {
          id: "CONJ-S2A-29834",
          primary_asset_id: "SENTINEL-2A",
          primary_name: "Sentinel-2A",
          secondary_name: "FENGYUN-1C-DEB-29834",
          secondary_norad_id: 29834,
          tca_hours: 14.2,
          miss_distance_m: 315.4,
          relative_velocity_kms: 12.42,
          pc: 2.4e-4,
          risk_class: "CRITICAL",
          screening_grade: true,
        },
        {
          id: "CONJ-S1A-40112",
          primary_asset_id: "SENTINEL-1A",
          primary_name: "Sentinel-1A",
          secondary_name: "COSMOS-2251-DEB-40112",
          secondary_norad_id: 40112,
          tca_hours: 21.4,
          miss_distance_m: 1240.0,
          relative_velocity_kms: 11.2,
          pc: 1.8e-5,
          risk_class: "WARNING",
          screening_grade: true,
        },
        {
          id: "CONJ-S3A-33441",
          primary_asset_id: "SENTINEL-3A",
          primary_name: "Sentinel-3A",
          secondary_name: "IRIDIUM-33-DEB-33441",
          secondary_norad_id: 33441,
          tca_hours: 36.8,
          miss_distance_m: 4850.0,
          relative_velocity_kms: 13.85,
          pc: 1.2e-6,
          risk_class: "WATCH",
          screening_grade: true,
        },
      ],
      active_threats_count: 2,
      timestamp: new Date().toISOString(),
    };
  }
}

export async function fetchLiveTelemetryPacket(
  assetId: string = "SENTINEL-2A",
  step: number = 0
): Promise<LiveTelemetryPacket> {
  try {
    const res = await fetch(`${API_BASE}/api/v1/assets/${assetId}/telemetry/live-stream?step=${step}`, {
      cache: "no-store",
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch {
    const t = step * 0.1;
    return {
      asset_id: assetId,
      timestamp: new Date().toISOString(),
      sequence_number: step,
      channels: {
        eps_battery_temp_c: Math.round((24.2 + 0.8 * Math.sin(t * 0.05)) * 100) / 100,
        eps_bus_voltage_v: Math.round((28.4 + 0.2 * Math.cos(t * 0.05)) * 100) / 100,
        eps_solar_array_current_a: Math.round((34.2 + 3.0 * Math.sin(t * 0.02)) * 100) / 100,
        adcs_reaction_wheel_rpm: Math.round(2450 + 45 * Math.sin(t * 0.1)),
        adcs_attitude_jitter_deg: Math.round((0.002 + 0.0005 * Math.sin(t * 0.2)) * 10000) / 10000,
        obc_cpu_load_pct: Math.round(28 + 4 * Math.sin(t * 0.3)),
      },
      synthetic: true,
    };
  }
}

export async function fetchTrustLayerMetrics(): Promise<TrustLayerMetrics> {
  try {
    const res = await fetch(`${API_BASE}/api/v1/models/trust`, { cache: "no-store" });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch {
    return {
      timestamp: new Date().toISOString(),
      overall_trust_grade: "A- (HIGH RELIABILITY)",
      summary: {
        active_models_monitored: 4,
        channels_monitored: 6,
        channels_with_drift_alert: 1,
        in_distribution: true,
        overall_ece: 0.0214,
        overall_brier_score: 0.0384,
      },
      calibration: {
        ece: 0.0214,
        mce: 0.048,
        brier_score: 0.0384,
        reliability_bins: [
          { bin_index: 1, conf_range: "0.0 - 0.1", confidence: 0.05, accuracy: 0.048, samples: 420 },
          { bin_index: 2, conf_range: "0.1 - 0.2", confidence: 0.15, accuracy: 0.142, samples: 380 },
          { bin_index: 3, conf_range: "0.2 - 0.3", confidence: 0.25, accuracy: 0.245, samples: 310 },
          { bin_index: 4, conf_range: "0.3 - 0.4", confidence: 0.35, accuracy: 0.358, samples: 290 },
          { bin_index: 5, conf_range: "0.4 - 0.5", confidence: 0.45, accuracy: 0.441, samples: 260 },
          { bin_index: 6, conf_range: "0.5 - 0.6", confidence: 0.55, accuracy: 0.562, samples: 280 },
          { bin_index: 7, conf_range: "0.6 - 0.7", confidence: 0.65, accuracy: 0.639, samples: 340 },
          { bin_index: 8, conf_range: "0.7 - 0.8", confidence: 0.75, accuracy: 0.761, samples: 410 },
          { bin_index: 9, conf_range: "0.8 - 0.9", confidence: 0.85, accuracy: 0.843, samples: 590 },
          { bin_index: 10, conf_range: "0.9 - 1.0", confidence: 0.95, accuracy: 0.962, samples: 1710 },
        ],
      },
      drift_monitoring: {
        test_method: "Two-sample Kolmogorov-Smirnov test (alpha=0.01)",
        channels: [
          { channel: "battery_bus_voltage", subsystem: "EPS", ks_statistic: 0.042, p_value: 0.88, kl_divergence: 0.012, status: "STABLE", baseline_mean: 28.42, current_mean: 28.39, unit: "V" },
          { channel: "reaction_wheel_rpm", subsystem: "ADCS", ks_statistic: 0.068, p_value: 0.45, kl_divergence: 0.024, status: "STABLE", baseline_mean: 2450.0, current_mean: 2468.0, unit: "RPM" },
          { channel: "gyro_drift_rate", subsystem: "ADCS", ks_statistic: 0.218, p_value: 0.003, kl_divergence: 0.185, status: "DRIFT_ALERT", baseline_mean: 0.0021, current_mean: 0.0048, unit: "deg/s", note: "Thermal gradient induced bias on Y-axis fiber gyro" },
          { channel: "solar_array_current", subsystem: "EPS", ks_statistic: 0.035, p_value: 0.94, kl_divergence: 0.008, status: "STABLE", baseline_mean: 34.15, current_mean: 33.98, unit: "A" },
          { channel: "radiator_temperature", subsystem: "Thermal", ks_statistic: 0.082, p_value: 0.31, kl_divergence: 0.031, status: "STABLE", baseline_mean: -12.4, current_mean: -10.8, unit: "°C" },
          { channel: "obc_cpu_load", subsystem: "OBC", ks_statistic: 0.051, p_value: 0.72, kl_divergence: 0.015, status: "STABLE", baseline_mean: 28.4, current_mean: 29.6, unit: "%" },
        ],
      },
      out_of_distribution: {
        ood_score: 0.142,
        threshold_nominal: 0.5,
        threshold_alert: 0.65,
        status: "IN_DISTRIBUTION",
        mahalanobis_distance: 1.24,
        latent_reconstruction_error: 0.041,
        percentile_rank: 14.2,
        description: "Telemetry vector is well within training manifold bounds (ESA-ADB baseline).",
      },
      tle_staleness: {
        primary_asset: { id: "SENTINEL-2A", tle_age_hours: 3.8, status: "FRESH", covariance_growth_factor: 1.05, projected_position_sigma_km: 0.42 },
        secondary_debris: { id: "FENGYUN-1C-DEB", norad_id: 29834, tle_age_hours: 18.4, status: "STALE_WARNING", covariance_growth_factor: 1.68, projected_position_sigma_km: 2.45, drag_inflation_pct: 34.8, recommendation: "Task ground radar tracking (TIRA) to refresh covariance prior to burn decision." },
        space_weather_context: { kp_index: 6.8, storm_level: "G3 Strong Geomagnetic Storm", f10_7_solar_flux: 168.4, atmospheric_density_anomaly_pct: 42.0 },
        staleness_curve: [
          { hours: 6, position_error_km: 0.653, covariance_scale: 1.13 },
          { hours: 12, position_error_km: 1.481, covariance_scale: 1.35 },
          { hours: 24, position_error_km: 3.398, covariance_scale: 2.0 },
          { hours: 48, position_error_km: 7.925, covariance_scale: 3.83 },
          { hours: 72, position_error_km: 13.144, covariance_scale: 6.2 },
        ],
      },
      provenance_hash: "28f9d012e8b417c9",
      synthetic: true,
    };
  }
}

export async function fetchObservationTasking(
  conjunctionId = "CONJ-29834",
  secondaryName = "FENGYUN-1C-DEB-29834",
  hoursToTca = 14.2
): Promise<ObservationTaskingPlan> {
  try {
    const res = await fetch(
      `${API_BASE}/api/v1/debris/observations?conjunction_id=${encodeURIComponent(conjunctionId)}&secondary_name=${encodeURIComponent(secondaryName)}&hours_to_tca=${hoursToTca}`,
      { cache: "no-store" }
    );
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch {
    const now = new Date();
    return {
      conjunction_id: conjunctionId,
      secondary_name: secondaryName,
      hours_to_tca: hoursToTca,
      tca_epoch_utc: new Date(now.getTime() + hoursToTca * 3600 * 1000).toISOString(),
      station_network_size: 4,
      stations_available: [
        { id: "GS-TIRA", name: "TIRA Tracking & Imaging Radar", operator: "Fraunhofer FHR", location: "Wachtberg, Germany", lat: 50.6167, lon: 7.1306, alt_m: 269, type: "Radar (L/Ku-band Monopulse)", min_elevation_deg: 10.0, accuracy_m: 3.5, all_weather: true },
        { id: "GS-TEIDE", name: "ESA Optical Ground Station (OGS)", operator: "ESA Space Debris Office", location: "Teide Observatory, Tenerife, Spain", lat: 28.3006, lon: -16.5108, alt_m: 2393, type: "Optical (1.0m Zeiss Telescope)", min_elevation_deg: 15.0, accuracy_m: 8.0, all_weather: false },
        { id: "GS-MAUI", name: "Maui Space Surveillance System (AMOS)", operator: "US Space Force / AFRL", location: "Haleakala, Hawaii, USA", lat: 20.7083, lon: -156.2575, alt_m: 3058, type: "Optical & Laser (3.6m AEOS)", min_elevation_deg: 15.0, accuracy_m: 5.0, all_weather: false },
        { id: "GS-LEARMONTH", name: "Learmonth Space Surveillance Station", operator: "Australian Defence Force", location: "Exmouth, WA, Australia", lat: -22.2356, lon: 114.0889, alt_m: 12, type: "Radar (C-band SSA Radar)", min_elevation_deg: 5.0, accuracy_m: 6.2, all_weather: true },
      ],
      scheduled_passes: [
        {
          pass_id: "PASS-01-TIRA",
          station: { id: "GS-TIRA", name: "TIRA Tracking & Imaging Radar", operator: "Fraunhofer FHR", location: "Wachtberg, Germany", lat: 50.6167, lon: 7.1306, alt_m: 269, type: "Radar (L/Ku-band Monopulse)", min_elevation_deg: 10.0, accuracy_m: 3.5, all_weather: true },
          start_utc: new Date(now.getTime() + 2.4 * 3600 * 1000).toISOString(),
          peak_utc: new Date(now.getTime() + 2.52 * 3600 * 1000).toISOString(),
          end_utc: new Date(now.getTime() + 2.64 * 3600 * 1000).toISOString(),
          duration_sec: 860,
          duration_min: 14.3,
          max_elevation_deg: 68.4,
          approach_azimuth_deg: 194.2,
          departure_azimuth_deg: 18.5,
          track_quality_snr_db: 28.5,
          sensor_modality: "Radar (L-band monopulse)",
          recommended: true,
          shrinkage_contribution_pct: 74.2,
        },
        {
          pass_id: "PASS-02-TEIDE",
          station: { id: "GS-TEIDE", name: "ESA Optical Ground Station (OGS)", operator: "ESA Space Debris Office", location: "Teide Observatory, Tenerife, Spain", lat: 28.3006, lon: -16.5108, alt_m: 2393, type: "Optical (1.0m Zeiss Telescope)", min_elevation_deg: 15.0, accuracy_m: 8.0, all_weather: false },
          start_utc: new Date(now.getTime() + 5.8 * 3600 * 1000).toISOString(),
          peak_utc: new Date(now.getTime() + 5.9 * 3600 * 1000).toISOString(),
          end_utc: new Date(now.getTime() + 6.01 * 3600 * 1000).toISOString(),
          duration_sec: 750,
          duration_min: 12.5,
          max_elevation_deg: 44.1,
          approach_azimuth_deg: 210.0,
          departure_azimuth_deg: 32.0,
          track_quality_snr_db: 21.0,
          sensor_modality: "Optical (night solar phase angle 118°)",
          recommended: true,
          shrinkage_contribution_pct: 18.4,
        },
      ],
      optimal_primary_pass: {
        pass_id: "PASS-01-TIRA",
        station: { id: "GS-TIRA", name: "TIRA Tracking & Imaging Radar", operator: "Fraunhofer FHR", location: "Wachtberg, Germany", lat: 50.6167, lon: 7.1306, alt_m: 269, type: "Radar (L/Ku-band Monopulse)", min_elevation_deg: 10.0, accuracy_m: 3.5, all_weather: true },
        start_utc: new Date(now.getTime() + 2.4 * 3600 * 1000).toISOString(),
        peak_utc: new Date(now.getTime() + 2.52 * 3600 * 1000).toISOString(),
        end_utc: new Date(now.getTime() + 2.64 * 3600 * 1000).toISOString(),
        duration_sec: 860,
        duration_min: 14.3,
        max_elevation_deg: 68.4,
        approach_azimuth_deg: 194.2,
        departure_azimuth_deg: 18.5,
        track_quality_snr_db: 28.5,
        sensor_modality: "Radar (L-band monopulse)",
        recommended: true,
        shrinkage_contribution_pct: 74.2,
      },
      covariance_projection: {
        initial_sigma_in_track_m: 250.0,
        initial_sigma_normal_m: 50.0,
        projected_sigma_in_track_m: 38.5,
        projected_sigma_normal_m: 18.2,
        uncertainty_reduction_pct: 84.6,
        projected_pc_resolution: 4.2e-7,
        potential_cam_avoidance: true,
        projected_fuel_savings_g: 128.4,
      },
      tdm_command_preview: `CCSDS_TDM_VERS = 2.0\nCREATION_DATE = ${now.toISOString()}\nORIGINATOR = ASTRA-GUARD_SSA_DIRECTORATE\nTARGET_NAME = ${secondaryName}\nSENSOR_REQUEST = TIRA_RADAR_TRACKING\nMODE = HIGH_PRECISION_RANGE_RANGE_RATE`,
      synthetic: true,
    };
  }
}

export function generateIncidentReportData(alert: Alert): IncidentReportData {
  return {
    incident_id: `INC-${alert.id || "2026-0889"}`,
    classification: alert.level === "CRITICAL" ? "CRITICAL // DETERMINISTIC CONJUNCTION OVERRIDE" : `${alert.level} // MISSION ADVISORY`,
    asset_id: alert.asset_id || "SENTINEL-2A",
    asset_norad: 40697,
    timestamp: alert.created_at || new Date().toISOString(),
    risk_level: alert.level,
    risk_score: alert.level === "CRITICAL" ? 94.7 : 62.9,
    pc: 1.42e-3,
    r_h: 0.082,
    r_d: 0.942,
    r_e: 0.15,
    secondary_name: "COSMOS 2251 DEBRIS",
    secondary_norad: 34120,
    miss_distance_m: 45.2,
    relative_velocity_kms: 14.82,
    tca_hours: 2.24,
    b_plane_sigma_y_m: 250.0,
    b_plane_sigma_x_m: 50.0,
    recommended_burn: "In-track prograde impulsive thruster burn",
    delta_v_ms: 0.42,
    fuel_expenditure_g: 128.4,
    post_cam_miss_m: 2840.0,
    post_cam_pc: 4.2e-7,
    operator_audit_trail: alert.audit_actions || [
      {
        id: "ACT-INIT",
        user: "FlightDirector_Sarah",
        action: "approve",
        note: "Reviewed B-plane geometry. Authorized pre-burn telemetry lock and ground station tasking.",
        timestamp: alert.created_at || new Date().toISOString(),
      },
    ],
    space_weather: {
      kp: 6.8,
      status: "G3 Strong Geomagnetic Storm",
      f10_7: 168.4,
      drag_factor_pct: 42.0,
    },
    telemetry_anomalies: [
      { channel: "battery_bus_voltage", value: 27.92, baseline: 28.4, unit: "V", dev: "-1.7%" },
      { channel: "gyro_drift_rate_y", value: 0.0048, baseline: 0.0021, unit: "deg/s", dev: "+128.5%" },
      { channel: "reaction_wheel_3_temp", value: 38.6, baseline: 24.0, unit: "°C", dev: "+60.8%" },
    ],
    provenance_sha256: "8e2f41bb92c10ad4593e817a52ff6071420a8db6712390aefb123d902187fa54",
  };
}

