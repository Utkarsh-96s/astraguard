"use client";

import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import {
  Activity,
  Orbit,
  Layers,
  Play,
  RotateCcw,
  ShieldCheck,
  Cpu,
  Clock,
  AlertTriangle,
  CheckCircle,
  ExternalLink,
  ChevronRight,
  Info,
} from "lucide-react";
import {
  fetchSamplePresets,
  inferHealth,
  inferDebris,
  inferDisaster,
  HealthInferenceResponse,
  DebrisInferenceResponse,
  DisasterInferenceResponse,
  SamplePreset,
} from "@/lib/api";

type Subsystem = "health" | "debris" | "disaster";

const MODEL_OPTIONS: Record<Subsystem, { id: string; name: string; arch: string }[]> = {
  health: [
    { id: "MOD-HEALTH-TCN-001", name: "TCN Autoencoder", arch: "Dilated Causal 1D-CNN" },
    { id: "MOD-HEALTH-LSTM-001", name: "LSTM Autoencoder", arch: "Recurrent Autoencoder" },
    { id: "MOD-HEALTH-TRANSFORMER-001", name: "Transformer Autoencoder", arch: "Multi-Head Self-Attention" },
  ],
  debris: [
    { id: "MOD-DEBRIS-CNN-001", name: "1D-CNN Classifier", arch: "Multi-Scale Temporal CNN (0.92ms)" },
    { id: "MOD-DEBRIS-GRU-001", name: "Bidirectional GRU", arch: "Gated Recurrent Network" },
    { id: "MOD-DEBRIS-LSTM-001", name: "Bidirectional LSTM", arch: "Long Short-Term Memory" },
  ],
  disaster: [
    { id: "MOD-DISASTER-SIAMESE-001", name: "Siamese Change U-Net", arch: "Dual-Temporal Pre/Post Context" },
    { id: "MOD-DISASTER-UNET-001", name: "Single-Chip U-Net", arch: "Post-Disaster SAR Segmentation" },
  ],
};

export default function ModelExplorerPage() {
  const [activeSubsystem, setActiveSubsystem] = useState<Subsystem>("health");
  const [selectedModel, setSelectedModel] = useState<string>("MOD-HEALTH-TCN-001");
  const [presets, setPresets] = useState<SamplePreset[]>([]);
  const [selectedPresetId, setSelectedPresetId] = useState<string>("battery_thermal_runaway");
  const [loading, setLoading] = useState(false);

  // Results
  const [healthResult, setHealthResult] = useState<HealthInferenceResponse | null>(null);
  const [debrisResult, setDebrisResult] = useState<DebrisInferenceResponse | null>(null);
  const [disasterResult, setDisasterResult] = useState<DisasterInferenceResponse | null>(null);

  // Switch subsystem
  useEffect(() => {
    async function loadPresets() {
      const p = await fetchSamplePresets(activeSubsystem);
      setPresets(p);
      if (p.length > 0) {
        setSelectedPresetId(p[0].id);
      }
      setSelectedModel(MODEL_OPTIONS[activeSubsystem][0].id);
    }
    loadPresets();
  }, [activeSubsystem]);

  // Execute inference
  const runInference = useCallback(async () => {
    setLoading(true);
    try {
      if (activeSubsystem === "health") {
        const res = await inferHealth({
          model_id: selectedModel,
          sample_id: selectedPresetId,
        });
        setHealthResult(res);
      } else if (activeSubsystem === "debris") {
        const res = await inferDebris({
          model_id: selectedModel,
          sample_id: selectedPresetId,
        });
        setDebrisResult(res);
      } else if (activeSubsystem === "disaster") {
        const res = await inferDisaster({
          model_id: selectedModel,
          sample_id: selectedPresetId,
        });
        setDisasterResult(res);
      }
    } catch (err) {
      console.error("Inference execution failed:", err);
    } finally {
      setLoading(false);
    }
  }, [activeSubsystem, selectedModel, selectedPresetId]);

  // Run initial inference on load
  useEffect(() => {
    runInference();
  }, [runInference]);

  const activePreset = presets.find((p) => p.id === selectedPresetId);

  return (
    <div className="space-y-6 w-full pb-16 font-sans">
      {/* Title Header */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 p-5 rounded-[4px] bg-[#08080c] border border-white/10">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold font-mono tracking-tight text-[#f0f0fa] flex items-center gap-2">
              <Cpu className="w-5 h-5 text-sky-400" />
              Interactive Deep Learning Model Explorer
            </h1>
            <span className="px-2 py-0.5 rounded-[4px] bg-emerald-950/60 border border-emerald-500/40 text-emerald-400 font-mono text-[10px] font-bold">
              LIVE ONNX CPU RUNTIME
            </span>
          </div>
          <p className="text-xs text-white/60 font-mono">
            Execute real-time forward passes across TCN, Transformer, 1D-CNN, GRU, and Siamese U-Net architectures.
          </p>
        </div>

        <Link
          href="/technology"
          className="px-3 py-1.5 rounded-[4px] border border-white/20 text-xs font-mono text-white/80 hover:text-white hover:border-white transition-colors flex items-center gap-1.5 shrink-0"
        >
          View Technology Report
          <ExternalLink className="w-3.5 h-3.5" />
        </Link>
      </div>

      {/* Subsystem Navigation Tabs */}
      <div className="grid grid-cols-3 gap-2 p-1 rounded-[4px] bg-black border border-white/10 text-xs font-mono">
        <button
          onClick={() => setActiveSubsystem("health")}
          className={`py-2.5 px-4 rounded-[4px] flex items-center justify-center gap-2 transition-colors uppercase tracking-wider font-bold ${
            activeSubsystem === "health"
              ? "bg-white text-black border border-white"
              : "text-white/70 hover:text-white hover:bg-white/[0.05]"
          }`}
        >
          <Activity className="w-4 h-4" />
          Spacecraft Health
        </button>
        <button
          onClick={() => setActiveSubsystem("debris")}
          className={`py-2.5 px-4 rounded-[4px] flex items-center justify-center gap-2 transition-colors uppercase tracking-wider font-bold ${
            activeSubsystem === "debris"
              ? "bg-white text-black border border-white"
              : "text-white/70 hover:text-white hover:bg-white/[0.05]"
          }`}
        >
          <Orbit className="w-4 h-4" />
          Orbital Debris Risk
        </button>
        <button
          onClick={() => setActiveSubsystem("disaster")}
          className={`py-2.5 px-4 rounded-[4px] flex items-center justify-center gap-2 transition-colors uppercase tracking-wider font-bold ${
            activeSubsystem === "disaster"
              ? "bg-white text-black border border-white"
              : "text-white/70 hover:text-white hover:bg-white/[0.05]"
          }`}
        >
          <Layers className="w-4 h-4" />
          SAR Flood Disaster
        </button>
      </div>

      {/* Control Panel & Preset Selectors */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Preset Scenarios & Architecture Selection */}
        <div className="space-y-6 lg:col-span-1">
          {/* Architecture Selector */}
          <div className="p-4 rounded-[4px] bg-[#050508] border border-white/10 space-y-3">
            <div className="text-[11px] font-mono uppercase tracking-wider text-white/50 flex items-center justify-between">
              <span>Select Model Architecture</span>
              <span className="text-[10px] text-sky-400">ONNX FP32</span>
            </div>
            <div className="space-y-2">
              {MODEL_OPTIONS[activeSubsystem].map((m) => (
                <button
                  key={m.id}
                  onClick={() => setSelectedModel(m.id)}
                  className={`w-full p-3 rounded-[4px] border text-left transition-all font-mono ${
                    selectedModel === m.id
                      ? "bg-white/[0.08] border-white text-white"
                      : "bg-black border-white/10 text-white/70 hover:border-white/30"
                  }`}
                >
                  <div className="flex items-center justify-between text-xs font-bold">
                    <span>{m.name}</span>
                    <span className="text-[10px] text-white/40">{m.id}</span>
                  </div>
                  <div className="text-[11px] text-white/50 mt-1">{m.arch}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Preset Scenario Selector */}
          <div className="p-4 rounded-[4px] bg-[#050508] border border-white/10 space-y-3">
            <div className="text-[11px] font-mono uppercase tracking-wider text-white/50">
              Interactive Mission Presets
            </div>
            <div className="space-y-2">
              {presets.map((p) => (
                <button
                  key={p.id}
                  onClick={() => setSelectedPresetId(p.id)}
                  className={`w-full p-3 rounded-[4px] border text-left transition-all ${
                    selectedPresetId === p.id
                      ? "bg-white/[0.08] border-white text-white"
                      : "bg-black border-white/10 text-white/70 hover:border-white/30"
                  }`}
                >
                  <div className="text-xs font-mono font-bold">{p.name}</div>
                  <div className="text-[11px] text-white/50 mt-0.5 font-sans line-clamp-2">
                    {p.description}
                  </div>
                </button>
              ))}
            </div>

            {/* Run Button */}
            <button
              onClick={runInference}
              disabled={loading}
              className="w-full py-2.5 px-4 rounded-[4px] bg-white text-black font-mono text-xs font-bold uppercase tracking-wider hover:bg-white/90 transition-colors flex items-center justify-center gap-2 mt-4"
            >
              <Play className="w-3.5 h-3.5 fill-black" />
              {loading ? "Executing ONNX Pass..." : "Run Live Inference"}
            </button>
          </div>
        </div>

        {/* Right Column: Live Output & Explainability Dashboard */}
        <div className="lg:col-span-2 space-y-6">
          {/* Active Preset Metadata Banner */}
          {activePreset && (
            <div className="p-4 rounded-[4px] bg-[#050508] border border-white/10 space-y-2">
              <div className="flex items-center justify-between text-xs font-mono">
                <span className="text-white/50 uppercase">Active Scenario:</span>
                <span className="text-emerald-400 font-bold">{activePreset.name}</span>
              </div>
              <div className="text-xs text-white/70 font-sans">
                <strong className="text-white">Injected Condition:</strong> {activePreset.injected_condition}
              </div>
              <div className="text-xs text-white/70 font-sans">
                <strong className="text-white">Expected Output:</strong> {activePreset.expected_verdict}
              </div>
            </div>
          )}

          {/* DOMAIN 1: HEALTH RESULTS */}
          {activeSubsystem === "health" && healthResult && (
            <div className="p-5 rounded-[4px] bg-[#050508] border border-white/10 space-y-6">
              {/* Verdict Header */}
              <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-white/10 pb-4">
                <div className="space-y-1 font-mono">
                  <div className="text-[10px] text-white/50 uppercase tracking-wider">
                    Model: {healthResult.model_id}
                  </div>
                  <div className="flex items-center gap-3">
                    <span
                      className={`px-3 py-1 rounded-[4px] font-bold text-xs uppercase tracking-wider ${
                        healthResult.is_anomaly
                          ? "bg-red-950/80 border border-red-500/50 text-red-400"
                          : "bg-emerald-950/80 border border-emerald-500/50 text-emerald-400"
                      }`}
                    >
                      {healthResult.is_anomaly ? "ANOMALY DETECTED" : "NOMINAL TELEMETRY"}
                    </span>
                    <span className="text-xs text-white/70">
                      Score: <strong className="text-[#f0f0fa]">{healthResult.anomaly_score.toFixed(4)}</strong> (threshold: {healthResult.threshold})
                    </span>
                  </div>
                </div>

                <div className="flex items-center gap-2 px-3 py-1.5 rounded-[4px] bg-white/[0.03] border border-white/10 font-mono text-xs">
                  <Clock className="w-3.5 h-3.5 text-sky-400" />
                  <span>CPU Latency: <strong>{healthResult.latency_ms.toFixed(2)} ms</strong></span>
                </div>
              </div>

              {/* Attribution Breakdown */}
              <div className="space-y-3 font-mono text-xs">
                <div className="text-[11px] uppercase tracking-wider text-white/50">
                  Subsystem Feature Attributions (% Contribution to Error)
                </div>
                <div className="space-y-2">
                  {Object.entries(healthResult.channel_attributions).map(([chan, pct]) => (
                    <div key={chan} className="space-y-1">
                      <div className="flex justify-between text-[11px]">
                        <span className="text-white/80">{chan}</span>
                        <span className="text-[#f0f0fa] font-bold">{pct.toFixed(1)}%</span>
                      </div>
                      <div className="w-full h-2 bg-white/10 rounded-[2px] overflow-hidden">
                        <div
                          className={`h-full ${
                            pct > 35 ? "bg-red-400" : pct > 15 ? "bg-amber-400" : "bg-sky-400"
                          }`}
                          style={{ width: `${Math.min(100, Math.max(2, pct))}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* DOMAIN 2: DEBRIS RESULTS */}
          {activeSubsystem === "debris" && debrisResult && (
            <div className="p-5 rounded-[4px] bg-[#050508] border border-white/10 space-y-6">
              {/* Verdict Header */}
              <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-white/10 pb-4">
                <div className="space-y-1 font-mono">
                  <div className="text-[10px] text-white/50 uppercase tracking-wider">
                    Model: {debrisResult.model_id}
                  </div>
                  <div className="flex items-center gap-3">
                    <span
                      className={`px-3 py-1 rounded-[4px] font-bold text-xs uppercase tracking-wider ${
                        debrisResult.risk_level === "CRITICAL"
                          ? "bg-red-950/80 border border-red-500/50 text-red-400"
                          : debrisResult.risk_level === "HIGH"
                          ? "bg-amber-950/80 border border-amber-500/50 text-amber-400"
                          : debrisResult.risk_level === "ELEVATED"
                          ? "bg-yellow-950/80 border border-yellow-500/50 text-yellow-300"
                          : "bg-emerald-950/80 border border-emerald-500/50 text-emerald-400"
                      }`}
                    >
                      {debrisResult.risk_level} RISK
                    </span>
                    <span className="text-xs text-white/70">
                      Platt P(risk): <strong className="text-[#f0f0fa]">{debrisResult.calibrated_risk_probability.toExponential(3)}</strong>
                    </span>
                  </div>
                </div>

                <div className="flex items-center gap-2 px-3 py-1.5 rounded-[4px] bg-white/[0.03] border border-white/10 font-mono text-xs">
                  <Clock className="w-3.5 h-3.5 text-sky-400" />
                  <span>CPU Latency: <strong>{debrisResult.latency_ms.toFixed(2)} ms</strong></span>
                </div>
              </div>

              {/* Recommendation Callout */}
              <div className="p-3.5 bg-black border border-white/15 rounded-[4px] space-y-1 font-mono text-xs">
                <div className="text-[10px] uppercase text-white/50">Autonomous Maneuver Advisory</div>
                <div className="text-[#f0f0fa] font-bold text-sm">
                  {debrisResult.operational_recommendation}
                </div>
                {debrisResult.lead_time_gain_hours > 0 && (
                  <div className="text-[11px] text-emerald-400 mt-1">
                    + {debrisResult.lead_time_gain_hours.toFixed(1)} hours advance warning gained over Foster thresholding
                  </div>
                )}
              </div>

              {/* Temporal Attribution Timeline */}
              <div className="space-y-3 font-mono text-xs">
                <div className="text-[11px] uppercase tracking-wider text-white/50 flex justify-between">
                  <span>Temporal Step Gradient Attribution</span>
                  <span className="text-white/40">T-72h ──&gt; TCA (T-0h)</span>
                </div>
                <div className="grid grid-cols-10 gap-1.5 h-16 items-end">
                  {debrisResult.temporal_attributions.map((weight, idx) => (
                    <div key={idx} className="flex flex-col items-center gap-1 h-full justify-end">
                      <div
                        className="w-full bg-amber-400 rounded-t-[2px] min-h-[4px]"
                        style={{ height: `${Math.min(100, Math.max(5, weight * 350))}%` }}
                      />
                      <span className="text-[9px] text-white/40">#{idx + 1}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* DOMAIN 3: DISASTER RESULTS */}
          {activeSubsystem === "disaster" && disasterResult && (
            <div className="p-5 rounded-[4px] bg-[#050508] border border-white/10 space-y-6">
              {/* Verdict Header */}
              <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-white/10 pb-4">
                <div className="space-y-1 font-mono">
                  <div className="text-[10px] text-white/50 uppercase tracking-wider">
                    Model: {disasterResult.model_id}
                  </div>
                  <div className="flex items-center gap-3">
                    <span
                      className={`px-3 py-1 rounded-[4px] font-bold text-xs uppercase tracking-wider ${
                        disasterResult.flood_fraction > 0.01
                          ? "bg-sky-950/80 border border-sky-500/50 text-sky-400"
                          : "bg-emerald-950/80 border border-emerald-500/50 text-emerald-400"
                      }`}
                    >
                      {disasterResult.flood_fraction > 0.01 ? "FLOOD INUNDATION DETECTED" : "DRY TERRAIN"}
                    </span>
                    <span className="text-xs text-white/70">
                      Extent: <strong className="text-[#f0f0fa]">{(disasterResult.flood_fraction * 100).toFixed(1)}%</strong> ({disasterResult.inundated_area_km2.toFixed(2)} km²)
                    </span>
                  </div>
                </div>

                <div className="flex items-center gap-2 px-3 py-1.5 rounded-[4px] bg-white/[0.03] border border-white/10 font-mono text-xs">
                  <Clock className="w-3.5 h-3.5 text-sky-400" />
                  <span>CPU Latency: <strong>{disasterResult.latency_ms.toFixed(2)} ms</strong></span>
                </div>
              </div>

              {/* Runway Specular Rejection Status */}
              <div className="p-3 bg-black border border-white/15 rounded-[4px] flex items-center justify-between font-mono text-xs">
                <span className="text-white/60">Specular Runway False Positive Status:</span>
                {disasterResult.specular_runway_rejected ? (
                  <span className="text-emerald-400 font-bold flex items-center gap-1.5">
                    <CheckCircle className="w-3.5 h-3.5" />
                    REJECTED / SUPPRESSED
                  </span>
                ) : (
                  <span className="text-amber-400 font-bold flex items-center gap-1.5">
                    <AlertTriangle className="w-3.5 h-3.5" />
                    POTENTIAL SPECULAR ARTIFACT
                  </span>
                )}
              </div>

              {/* Spatial Attention Heatmap Grid */}
              <div className="space-y-2 font-mono text-xs">
                <div className="text-[11px] uppercase tracking-wider text-white/50 flex justify-between">
                  <span>16x16 Spatial Waterline Probability Grid</span>
                  <span className="text-white/40">Pixel Range: 0.00 – 1.00</span>
                </div>
                <div className="grid grid-cols-16 gap-0.5 p-2 bg-black border border-white/10 rounded-[4px] aspect-square max-w-[320px] mx-auto">
                  {disasterResult.spatial_attention_grid.flatMap((row, rIdx) =>
                    row.map((val, cIdx) => {
                      const alpha = Math.min(1.0, Math.max(0.05, val));
                      return (
                        <div
                          key={`${rIdx}-${cIdx}`}
                          title={`Grid [${rIdx}, ${cIdx}]: ${val.toFixed(2)}`}
                          className="w-full h-full rounded-[1px] transition-colors"
                          style={{
                            backgroundColor: val > 0.5 ? `rgba(56, 189, 248, ${alpha})` : `rgba(255, 255, 255, ${alpha * 0.15})`,
                          }}
                        />
                      );
                    })
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
