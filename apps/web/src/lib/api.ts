/**
 * API client for ASTRA-GUARD backend endpoints with resilient fallbacks.
 */
import {
  Alert,
  ConjunctionItem,
  DisasterEventItem,
  ModelRegistryEntry,
  OperatorAction,
  RiskSnapshot,
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
