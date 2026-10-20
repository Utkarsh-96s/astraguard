"use client";

import React, { useEffect, useState } from "react";
import {
  ShieldCheck,
  TrendingDown,
  Activity,
  AlertTriangle,
  Clock,
  Sparkles,
  BarChart3,
  Layers,
  CheckCircle2,
  Lock,
} from "lucide-react";
import { TrustLayerMetrics } from "../lib/types";
import { fetchTrustLayerMetrics } from "../lib/api";

export function TrustLayerCard() {
  const [metrics, setMetrics] = useState<TrustLayerMetrics | null>(null);
  const [activeTab, setActiveTab] = useState<"calibration" | "drift" | "ood" | "staleness">("calibration");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadMetrics() {
      try {
        const data = await fetchTrustLayerMetrics();
        setMetrics(data);
      } catch (e) {
        console.warn("Failed to load trust layer metrics:", e);
      } finally {
        setLoading(false);
      }
    }
    loadMetrics();
  }, []);

  if (loading || !metrics) {
    return (
      <div className="p-6 rounded-card bg-charcoal border border-white/10 animate-pulse text-xs font-mono text-pebble">
        Loading AI Trust Layer & Calibration Engine...
      </div>
    );
  }

  return (
    <div className="p-5 sm:p-6 rounded-card bg-charcoal border border-white/15 shadow-xl space-y-5">
      {/* Trust Layer Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 border-b border-white/10 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-emerald-400" />
            <h3 className="text-base font-bold font-mono text-bone">
              AI Trust Layer & Model Observability (F9)
            </h3>
            <span className="px-2 py-0.5 rounded bg-emerald-950/60 border border-emerald-500/40 text-[10px] font-mono text-emerald-300 font-bold">
              {metrics.overall_trust_grade}
            </span>
          </div>
          <p className="text-xs text-ash font-mono mt-0.5">
            Statistical ECE Calibration · Kolmogorov-Smirnov Telemetry Drift · OOD Scoring · TLE Staleness
          </p>
        </div>

        {/* Quick Status Badges */}
        <div className="flex flex-wrap items-center gap-2 text-[11px] font-mono">
          <div className="px-2.5 py-1 rounded bg-smoke border border-white/10 text-ash flex items-center gap-1.5">
            <span className="text-pebble">ECE:</span>
            <strong className="text-emerald-400">{metrics.calibration.ece}</strong>
          </div>
          <div className="px-2.5 py-1 rounded bg-smoke border border-white/10 text-ash flex items-center gap-1.5">
            <span className="text-pebble">OOD:</span>
            <strong className="text-sky-400">{metrics.out_of_distribution.ood_score}</strong>
          </div>
          <div className="px-2.5 py-1 rounded bg-amber-950/40 border border-amber-500/30 text-amber-300 flex items-center gap-1.5">
            <AlertTriangle className="w-3.5 h-3.5" />
            <span>1 Drift Alert</span>
          </div>
        </div>
      </div>

      {/* Navigation Sub-Tabs */}
      <div className="flex items-center gap-2 border-b border-white/5 pb-2 text-xs font-mono">
        <button
          onClick={() => setActiveTab("calibration")}
          className={`px-3 py-1.5 rounded-nav transition-colors ${
            activeTab === "calibration"
              ? "bg-smoke text-bone font-bold border border-white/20"
              : "text-pebble hover:text-bone"
          }`}
        >
          Model Calibration (ECE)
        </button>
        <button
          onClick={() => setActiveTab("drift")}
          className={`px-3 py-1.5 rounded-nav transition-colors ${
            activeTab === "drift"
              ? "bg-smoke text-bone font-bold border border-white/20"
              : "text-pebble hover:text-bone"
          }`}
        >
          Telemetry Drift (KS-Test)
        </button>
        <button
          onClick={() => setActiveTab("ood")}
          className={`px-3 py-1.5 rounded-nav transition-colors ${
            activeTab === "ood"
              ? "bg-smoke text-bone font-bold border border-white/20"
              : "text-pebble hover:text-bone"
          }`}
        >
          OOD Anomaly Detector
        </button>
        <button
          onClick={() => setActiveTab("staleness")}
          className={`px-3 py-1.5 rounded-nav transition-colors ${
            activeTab === "staleness"
              ? "bg-smoke text-bone font-bold border border-white/20"
              : "text-pebble hover:text-bone"
          }`}
        >
          TLE Ephemeris Staleness
        </button>
      </div>

      {/* Tab 1: Calibration & Reliability Diagram */}
      {activeTab === "calibration" && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs font-mono">
            <div className="p-3 rounded bg-void/80 border border-white/5 space-y-1">
              <span className="text-[10px] text-pebble uppercase">Expected Calibration Error (ECE):</span>
              <div className="text-xl font-bold text-emerald-400">{metrics.calibration.ece}</div>
              <span className="text-[10px] text-pebble">Threshold: &le; 0.050 (Well Calibrated)</span>
            </div>
            <div className="p-3 rounded bg-void/80 border border-white/5 space-y-1">
              <span className="text-[10px] text-pebble uppercase">Maximum Calibration Error (MCE):</span>
              <div className="text-xl font-bold text-bone">{metrics.calibration.mce}</div>
              <span className="text-[10px] text-pebble">Peak Deviation Across Any Bin</span>
            </div>
            <div className="p-3 rounded bg-void/80 border border-white/5 space-y-1">
              <span className="text-[10px] text-pebble uppercase">Overall Brier Score:</span>
              <div className="text-xl font-bold text-sky-400">{metrics.calibration.brier_score}</div>
              <span className="text-[10px] text-pebble">Mean Squared Probability Error</span>
            </div>
          </div>

          {/* Reliability Diagram Visualization */}
          <div className="p-4 rounded bg-void/80 border border-white/5 space-y-3">
            <div className="flex items-center justify-between text-xs font-mono">
              <span className="text-bone font-bold">10-Bin Reliability Curve (Confidence vs Empirical Accuracy):</span>
              <span className="text-pebble text-[11px]">Diagonal (y = x) represents perfect calibration</span>
            </div>

            <div className="space-y-1.5">
              {metrics.calibration.reliability_bins.map((bin) => {
                const diff = Math.abs(bin.confidence - bin.accuracy);
                return (
                  <div key={bin.bin_index} className="grid grid-cols-12 items-center gap-2 text-[11px] font-mono">
                    <span className="col-span-2 text-pebble truncate">{bin.conf_range}</span>
                    <div className="col-span-8 flex items-center gap-2">
                      <div className="h-2.5 rounded bg-smoke flex-1 relative overflow-hidden">
                        {/* Target confidence line */}
                        <div
                          className="absolute top-0 bottom-0 w-0.5 bg-white/40 z-10"
                          style={{ left: `${bin.confidence * 100}%` }}
                          title={`Target: ${(bin.confidence * 100).toFixed(0)}%`}
                        />
                        {/* Observed accuracy bar */}
                        <div
                          className={`h-full rounded ${
                            diff <= 0.03 ? "bg-emerald-500" : "bg-sky-500"
                          }`}
                          style={{ width: `${bin.accuracy * 100}%` }}
                        />
                      </div>
                    </div>
                    <span className="col-span-2 text-right text-bone">
                      {(bin.accuracy * 100).toFixed(1)}% <span className="text-pebble text-[9px]">({bin.samples})</span>
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* Tab 2: Feature Distribution Drift */}
      {activeTab === "drift" && (
        <div className="space-y-3">
          <div className="flex items-center justify-between text-xs font-mono">
            <span className="text-ash">Statistical Hypothesis Testing: Kolmogorov-Smirnov 2-Sample Test (&alpha;=0.01)</span>
            <span className="text-pebble">Rolling 24h Window vs Baseline Distribution</span>
          </div>

          <div className="overflow-x-auto rounded border border-white/5 bg-void/80">
            <table className="w-full text-left text-xs font-mono">
              <thead className="bg-smoke/60 text-pebble text-[10px] uppercase border-b border-white/10">
                <tr>
                  <th className="p-2.5">Subsystem Channel</th>
                  <th className="p-2.5">KS Statistic</th>
                  <th className="p-2.5">p-value</th>
                  <th className="p-2.5">KL Divergence</th>
                  <th className="p-2.5">Baseline &rarr; Current</th>
                  <th className="p-2.5">Drift Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5 text-[11px]">
                {metrics.drift_monitoring.channels.map((ch) => (
                  <tr key={ch.channel} className="hover:bg-white/5 transition-colors">
                    <td className="p-2.5 font-bold text-bone">
                      <div>{ch.channel}</div>
                      <div className="text-[10px] font-normal text-pebble">Subsystem: {ch.subsystem}</div>
                      {ch.note && <div className="text-[10px] text-amber-300 italic">{ch.note}</div>}
                    </td>
                    <td className="p-2.5 text-bone">{ch.ks_statistic}</td>
                    <td className="p-2.5 font-bold">
                      <span className={ch.p_value < 0.01 ? "text-red-400" : "text-emerald-400"}>
                        {ch.p_value}
                      </span>
                    </td>
                    <td className="p-2.5 text-ash">{ch.kl_divergence}</td>
                    <td className="p-2.5 text-pebble">
                      {ch.baseline_mean} &rarr; <span className="text-bone">{ch.current_mean} {ch.unit}</span>
                    </td>
                    <td className="p-2.5">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          ch.status === "DRIFT_ALERT"
                            ? "bg-red-950/60 border border-arterial/50 text-red-300"
                            : "bg-emerald-950/60 border border-emerald-500/40 text-emerald-300"
                        }`}
                      >
                        {ch.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab 3: Out-of-Distribution Detector */}
      {activeTab === "ood" && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs font-mono">
            <div className="p-3 rounded bg-void/80 border border-white/5 space-y-1">
              <span className="text-[10px] text-pebble uppercase">Current OOD Score:</span>
              <div className="text-xl font-bold text-emerald-400">{metrics.out_of_distribution.ood_score}</div>
              <span className="text-[10px] text-pebble">Threshold: &lt; 0.50 (Nominal)</span>
            </div>
            <div className="p-3 rounded bg-void/80 border border-white/5 space-y-1">
              <span className="text-[10px] text-pebble uppercase">Mahalanobis Distance:</span>
              <div className="text-xl font-bold text-bone">{metrics.out_of_distribution.mahalanobis_distance}</div>
              <span className="text-[10px] text-pebble">Covariance-Weighted Distance</span>
            </div>
            <div className="p-3 rounded bg-void/80 border border-white/5 space-y-1">
              <span className="text-[10px] text-pebble uppercase">Latent Reconstruction Loss:</span>
              <div className="text-xl font-bold text-sky-400">{metrics.out_of_distribution.latent_reconstruction_error}</div>
              <span className="text-[10px] text-pebble">LSTM Autoencoder Residual</span>
            </div>
          </div>

          <div className="p-4 rounded bg-void/80 border border-white/5 space-y-2">
            <div className="flex items-center justify-between text-xs font-mono">
              <span className="text-bone font-bold">OOD Score Boundary Spectrum:</span>
              <span className="text-emerald-400 font-bold">{metrics.out_of_distribution.status}</span>
            </div>

            <div className="h-3 rounded-full bg-smoke relative overflow-hidden">
              {/* Threshold marker */}
              <div
                className="absolute top-0 bottom-0 w-0.5 bg-arterial z-10"
                style={{ left: `${metrics.out_of_distribution.threshold_alert * 100}%` }}
                title="Alert Threshold (0.65)"
              />
              <div
                className="h-full rounded-full bg-emerald-500"
                style={{ width: `${metrics.out_of_distribution.ood_score * 100}%` }}
              />
            </div>

            <p className="text-xs text-ash font-sans pt-1">
              {metrics.out_of_distribution.description}
            </p>
          </div>
        </div>
      )}

      {/* Tab 4: TLE Staleness Degradation */}
      {activeTab === "staleness" && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs font-mono">
            {/* Primary Asset */}
            <div className="p-3 rounded bg-void/80 border border-white/5 space-y-1.5">
              <div className="flex justify-between items-center">
                <span className="text-bone font-bold">{metrics.tle_staleness.primary_asset.id}</span>
                <span className="px-2 py-0.5 rounded bg-emerald-950/60 border border-emerald-500/40 text-emerald-400 text-[10px] font-bold">
                  {metrics.tle_staleness.primary_asset.status}
                </span>
              </div>
              <div className="text-ash text-[11px] space-y-0.5">
                <div>TLE Age: <strong className="text-bone">{metrics.tle_staleness.primary_asset.tle_age_hours} hours</strong></div>
                <div>Projected Covariance Sigma: {metrics.tle_staleness.primary_asset.projected_position_sigma_km} km</div>
              </div>
            </div>

            {/* Secondary Debris */}
            <div className="p-3 rounded bg-void/80 border border-amber-500/30 space-y-1.5">
              <div className="flex justify-between items-center">
                <span className="text-bone font-bold">{metrics.tle_staleness.secondary_debris.id}</span>
                <span className="px-2 py-0.5 rounded bg-amber-950/60 border border-amber-500/40 text-amber-300 text-[10px] font-bold">
                  {metrics.tle_staleness.secondary_debris.status}
                </span>
              </div>
              <div className="text-ash text-[11px] space-y-0.5">
                <div>TLE Age: <strong className="text-amber-400">{metrics.tle_staleness.secondary_debris.tle_age_hours} hours</strong></div>
                <div>Drag Inflation: <strong className="text-red-400">+{metrics.tle_staleness.secondary_debris.drag_inflation_pct}%</strong></div>
              </div>
              <div className="text-[10px] text-pebble pt-1 border-t border-white/5">
                {metrics.tle_staleness.secondary_debris.recommendation}
              </div>
            </div>
          </div>

          {/* SGP4 Uncertainty Growth Curve */}
          <div className="p-3.5 rounded bg-void/80 border border-white/5 space-y-2 text-xs font-mono">
            <div className="flex justify-between text-pebble text-[10px] uppercase">
              <span>SGP4 Propagation Uncertainty Growth Horizons:</span>
              <span>Space Weather: Kp {metrics.tle_staleness.space_weather_context.kp_index}</span>
            </div>
            <div className="grid grid-cols-5 gap-2 text-center text-[11px]">
              {metrics.tle_staleness.staleness_curve.map((c) => (
                <div key={c.hours} className="p-2 rounded bg-smoke flex flex-col justify-between">
                  <span className="text-pebble text-[10px]">T+{c.hours}h</span>
                  <span className="text-bone font-bold">{c.position_error_km} km</span>
                  <span className="text-[9px] text-amber-400">&sigma; &times;{c.covariance_scale}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Footer Provenance */}
      <div className="flex items-center justify-between pt-3 border-t border-white/10 text-[11px] font-mono text-pebble">
        <div className="flex items-center gap-1.5">
          <Lock className="w-3.5 h-3.5 text-cyan-400" />
          <span>Trust Layer SHA-256: {metrics.provenance_hash}</span>
        </div>
        <span>Last Evaluated: {new Date(metrics.timestamp).toLocaleTimeString()}</span>
      </div>
    </div>
  );
}
