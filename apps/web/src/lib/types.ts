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
