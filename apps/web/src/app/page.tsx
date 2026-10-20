"use client";

import React, { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import {
  ShieldAlert,
  Activity,
  Orbit,
  Layers,
  ArrowRight,
  AlertTriangle,
  CheckCircle2,
  Cpu,
  Clock,
  Sparkles,
  RefreshCw,
} from "lucide-react";

import { RiskSnapshot, Alert } from "../lib/types";
import { fetchLatestRisk, fetchAlerts, FALLBACK_RISK } from "../lib/api";
import { useAsset } from "../lib/assetContext";
import { RiskGauge } from "../components/RiskGauge";
import { StatusBadge } from "../components/StatusBadge";
import { SimulatedBadge } from "../components/SimulatedBadge";
import { DriversList } from "../components/DriversList";
import { ConstellationMatrix } from "../components/ConstellationMatrix";
import { LiveTelemetryStreamer } from "../components/LiveTelemetryStreamer";

export default function OverviewPage() {
  const { selectedAssetId, selectedAsset, setSelectedAssetId } = useAsset();
  const [risk, setRisk] = useState<RiskSnapshot>(FALLBACK_RISK);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [lastRefreshed, setLastRefreshed] = useState<string>("");

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [latestRisk, alertList] = await Promise.all([
        fetchLatestRisk(selectedAssetId),
        fetchAlerts(),
      ]);
      setRisk(latestRisk);
      setAlerts(alertList);
      setLastRefreshed(new Date().toLocaleTimeString());
    } catch (e) {
      console.warn("Failed to fetch live overview data:", e);
    } finally {
      setLoading(false);
    }
  }, [selectedAssetId]);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 15000); // 15s polling fallback
    return () => clearInterval(interval);
  }, [loadData]);

  // Compute Noisy-OR Safety Hazard for display
  const rSafety = 1.0 - (1.0 - risk.r_h) * (1.0 - risk.r_d);

  return (
    <div className="space-y-6">
      {/* Top Banner / Asset Flight Header */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 p-4 rounded-card bg-charcoal border border-white/10 shadow-glass">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-nav bg-void border border-white/15 flex items-center justify-center">
            <Cpu className="w-5 h-5 text-arterial" />
          </div>
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <h1 className="text-xl font-bold tracking-tight text-bone">
                {selectedAsset.name} Mission Intelligence
              </h1>
              <SimulatedBadge />
            </div>
            <p className="text-xs text-ash font-mono mt-0.5">
              NORAD {selectedAsset.norad_id} · {selectedAsset.type} · Ingestion 10Hz Nominal
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3 self-end md:self-auto font-mono text-xs">
          <button
            onClick={loadData}
            disabled={loading}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-nav bg-smoke hover:bg-white/10 border border-white/15 text-bone transition-colors disabled:opacity-50"
            title="Refresh state"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin text-arterial" : "text-ash"}`} />
            <span>Sync</span>
          </button>
          <div className="flex items-center gap-1.5 text-pebble">
            <Clock className="w-3.5 h-3.5" />
            <span>{lastRefreshed || "Live"}</span>
          </div>
        </div>
      </div>

      {/* Cross-System Deferral Warning Banner (Rule: r_h >= 0.50 deferral) */}
      {risk.defer_eo_payloads && (
        <div className="p-3.5 rounded-card bg-amber-950/40 border border-amber-500/50 flex items-center justify-between text-amber-200 text-xs">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
            <div>
              <span className="font-bold uppercase tracking-wider">Secondary Payloads Deferred: </span>
              Spacecraft health risk (r_h = {risk.r_h.toFixed(2)}) exceeds nominal threshold (0.50). Earth observation imaging tasks are deferred to safeguard battery thermal reserves.
            </div>
          </div>
          <Link
            href="/health"
            className="ml-4 shrink-0 px-2.5 py-1 rounded-nav bg-amber-500/20 hover:bg-amber-500/30 font-mono text-[11px] underline"
          >
            Inspect Subsystem &rarr;
          </Link>
        </div>
      )}

      {/* Critical Conjunction Override Banner */}
      {risk.critical_override_applied && (
        <div className="p-3.5 rounded-card bg-red-950/50 border border-arterial flex items-center justify-between text-red-200 text-xs">
          <div className="flex items-center gap-2">
            <ShieldAlert className="w-4 h-4 text-arterial shrink-0 animate-bounce" />
            <div>
              <span className="font-bold uppercase tracking-wider">Critical Conjunction Override Active: </span>
              Collision probability Pc &ge; 1.00e-04 safety ceiling breached. Automatic safety override forced mission risk to CRITICAL status. Immediate flight dynamics assessment required.
            </div>
          </div>
          <Link
            href="/debris"
            className="ml-4 shrink-0 px-2.5 py-1 rounded-nav bg-arterial/30 hover:bg-arterial/40 font-mono text-[11px] underline"
          >
            Assess Conjunction &rarr;
          </Link>
        </div>
      )}

      {/* 4-Card Multi-Hazard Factor Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {/* Safety Hazard Factor */}
        <div className="p-4 rounded-card bg-charcoal border border-white/10 space-y-2">
          <div className="flex items-center justify-between text-xs text-ash">
            <span className="font-mono uppercase tracking-wider">R_safety Hazard</span>
            <span className="text-[10px] text-pebble">Noisy-OR</span>
          </div>
          <div className="text-2xl font-bold font-mono text-bone">
            {(rSafety * 100).toFixed(1)}%
          </div>
          <div className="w-full h-1 bg-black/60 rounded-full overflow-hidden">
            <div
              className={`h-full ${rSafety > 0.5 ? "bg-arterial" : "bg-emerald-400"}`}
              style={{ width: `${Math.min(100, rSafety * 100)}%` }}
            />
          </div>
          <p className="text-[10px] text-pebble">Fused risk of catastrophic loss</p>
        </div>

        {/* Spacecraft Health (r_h) */}
        <Link
          href="/health"
          className="p-4 rounded-card bg-charcoal border border-white/10 hover:border-white/20 transition-colors space-y-2 group"
        >
          <div className="flex items-center justify-between text-xs text-ash">
            <span className="font-mono uppercase tracking-wider flex items-center gap-1.5">
              <Activity className="w-3.5 h-3.5 text-sky-400" />
              Health (r_h)
            </span>
            <ArrowRight className="w-3 h-3 text-pebble group-hover:text-bone transition-transform group-hover:translate-x-0.5" />
          </div>
          <div className="text-2xl font-bold font-mono text-bone">
            {risk.r_h.toFixed(3)}
          </div>
          <div className="w-full h-1 bg-black/60 rounded-full overflow-hidden">
            <div
              className={`h-full ${risk.r_h >= 0.5 ? "bg-amber-400" : "bg-sky-400"}`}
              style={{ width: `${Math.min(100, risk.r_h * 100)}%` }}
            />
          </div>
          <p className="text-[10px] text-pebble">LSTM Autoencoder Anomaly Score</p>
        </Link>

        {/* Debris Risk (r_d) */}
        <Link
          href="/debris"
          className="p-4 rounded-card bg-charcoal border border-white/10 hover:border-white/20 transition-colors space-y-2 group"
        >
          <div className="flex items-center justify-between text-xs text-ash">
            <span className="font-mono uppercase tracking-wider flex items-center gap-1.5">
              <Orbit className="w-3.5 h-3.5 text-rose-400" />
              Debris (r_d)
            </span>
            <ArrowRight className="w-3 h-3 text-pebble group-hover:text-bone transition-transform group-hover:translate-x-0.5" />
          </div>
          <div className="text-2xl font-bold font-mono text-bone">
            {risk.r_d.toFixed(3)}
          </div>
          <div className="w-full h-1 bg-black/60 rounded-full overflow-hidden">
            <div
              className={`h-full ${risk.r_d >= 0.5 ? "bg-arterial" : "bg-rose-400"}`}
              style={{ width: `${Math.min(100, risk.r_d * 100)}%` }}
            />
          </div>
          <p className="text-[10px] text-pebble">Foster 2-D B-Plane Collision Pc</p>
        </Link>

        {/* Disaster Observation Priority (r_e) */}
        <Link
          href="/disaster"
          className="p-4 rounded-card bg-charcoal border border-white/10 hover:border-white/20 transition-colors space-y-2 group"
        >
          <div className="flex items-center justify-between text-xs text-ash">
            <span className="font-mono uppercase tracking-wider flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5 text-amber-400" />
              Disaster (r_e)
            </span>
            <ArrowRight className="w-3 h-3 text-pebble group-hover:text-bone transition-transform group-hover:translate-x-0.5" />
          </div>
          <div className="text-2xl font-bold font-mono text-bone">
            {risk.r_e.toFixed(3)}
          </div>
          <div className="w-full h-1 bg-black/60 rounded-full overflow-hidden">
            <div
              className="h-full bg-amber-400"
              style={{ width: `${Math.min(100, risk.r_e * 100)}%` }}
            />
          </div>
          <p className="text-[10px] text-pebble">SAR Inundation Priority Ranking</p>
        </Link>
      </div>

      {/* Main Dual Grid: Mission Gauge & Drivers */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Mission Risk Gauge Card */}
        <div className="lg:col-span-5 p-6 rounded-card bg-charcoal border border-white/10 flex flex-col items-center justify-between">
          <div className="w-full flex items-center justify-between border-b border-white/10 pb-3">
            <span className="text-xs uppercase font-mono tracking-wider text-ash">
              Integrated Mission Risk Score
            </span>
            <StatusBadge level={risk.level} size="sm" />
          </div>

          <RiskGauge score={risk.score} level={risk.level} size={280} />

          <div className="w-full pt-3 border-t border-white/10 grid grid-cols-2 gap-2 text-center text-xs font-mono">
            <div className="p-2 rounded bg-smoke">
              <div className="text-pebble text-[10px]">Safety Weight</div>
              <div className="text-bone font-semibold">85.0%</div>
            </div>
            <div className="p-2 rounded bg-smoke">
              <div className="text-pebble text-[10px]">EO Urgency Weight</div>
              <div className="text-bone font-semibold">15.0%</div>
            </div>
          </div>
        </div>

        {/* Right Column: Top Attribution Drivers & Rationale */}
        <div className="lg:col-span-7 space-y-6">
          {/* Deterministic Rationale Banner */}
          <div className="p-5 rounded-card bg-charcoal border border-white/10 space-y-2">
            <div className="flex items-center gap-2 text-xs font-mono text-ash uppercase tracking-wider">
              <Sparkles className="w-4 h-4 text-arterial" />
              Deterministic Safety Rationale (Zero-LLM Safety Path)
            </div>
            <p className="text-xs text-bone leading-relaxed font-sans font-light bg-void/60 p-3 rounded-card border border-white/5">
              {risk.rationale}
            </p>
          </div>

          {/* Top Drivers Attribution */}
          <div className="p-5 rounded-card bg-charcoal border border-white/10 space-y-3">
            <div className="flex items-center justify-between border-b border-white/10 pb-2">
              <span className="text-xs font-mono uppercase tracking-wider text-ash">
                Primary Risk Drivers & Channel Attribution
              </span>
              <span className="text-[10px] text-pebble font-mono">Normalized Share</span>
            </div>
            <DriversList drivers={risk.drivers} />
          </div>

          {/* Actionable Recommendations */}
          <div className="p-5 rounded-card bg-charcoal border border-white/10 space-y-3">
            <div className="flex items-center justify-between border-b border-white/10 pb-2">
              <span className="text-xs font-mono uppercase tracking-wider text-ash flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                Actionable Advisory Recommendations
              </span>
              <span className="text-[10px] text-pebble font-mono">Advisory Only</span>
            </div>
            <div className="space-y-2">
              {risk.recommendations && risk.recommendations.length > 0 ? (
                risk.recommendations.map((rec, i) => (
                  <div
                    key={i}
                    className="flex items-start gap-3 p-3 rounded bg-smoke/40 border border-white/5 text-xs"
                  >
                    <span className="px-2 py-0.5 rounded bg-white/10 text-bone font-mono font-bold text-[10px] shrink-0">
                      {rec.action}
                    </span>
                    <div className="space-y-0.5">
                      <p className="text-ash font-sans">{rec.rationale}</p>
                      <span className="text-[10px] text-pebble font-mono uppercase">
                        Source: {rec.source_module} · Priority #{rec.priority}
                      </span>
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-xs text-pebble italic">No operational actions required. Continue monitoring.</div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Real-Time Live Telemetry Streamer */}
      <LiveTelemetryStreamer assetId={selectedAssetId} />

      {/* Constellation Fleet Operations & Conjunction Matrix */}
      <ConstellationMatrix onSelectAsset={(id) => setSelectedAssetId(id)} />

      {/* Active Alerts Strip */}
      <div className="p-4 rounded-card bg-charcoal border border-white/10 space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-arterial" />
            <h2 className="text-xs font-mono uppercase tracking-wider text-bone font-semibold">
              Mission Alerts Ticker ({alerts.filter((a) => a.status === "ACTIVE").length} Active)
            </h2>
          </div>
          <Link
            href="/alerts"
            className="text-xs font-mono text-ash hover:text-bone flex items-center gap-1 transition-colors"
          >
            <span>Alert Management Console</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {alerts.slice(0, 2).map((a) => (
            <div
              key={a.id}
              className="p-3 rounded bg-smoke/50 border border-white/5 flex items-start justify-between gap-3 text-xs"
            >
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <StatusBadge level={a.level} size="sm" />
                  <span className="font-mono text-bone font-semibold">{a.title}</span>
                </div>
                <p className="text-ash line-clamp-2 text-[11px]">{a.rationale}</p>
              </div>
              <Link
                href="/alerts"
                className="shrink-0 px-2.5 py-1 rounded-nav bg-white/5 hover:bg-white/10 border border-white/10 font-mono text-[10px] text-bone"
              >
                Review &rarr;
              </Link>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
