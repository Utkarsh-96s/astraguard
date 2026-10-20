"use client";

import React, { useEffect, useState } from "react";
import {
  Radio,
  Clock,
  Compass,
  CheckCircle2,
  Copy,
  Check,
  Send,
  X,
  ShieldCheck,
  Zap,
  ArrowRight,
  TrendingDown,
  Layers,
} from "lucide-react";
import { ObservationTaskingPlan } from "../lib/types";
import { fetchObservationTasking } from "../lib/api";
import { playAudioCue } from "../lib/audio";

interface ObservationTaskingModalProps {
  conjunctionId?: string;
  secondaryName?: string;
  hoursToTca?: number;
  onClose?: () => void;
  isEmbedded?: boolean;
}

export function ObservationTaskingModal({
  conjunctionId = "CONJ-29834",
  secondaryName = "FENGYUN-1C-DEB-29834",
  hoursToTca = 14.2,
  onClose,
  isEmbedded = false,
}: ObservationTaskingModalProps) {
  const [plan, setPlan] = useState<ObservationTaskingPlan | null>(null);
  const [loading, setLoading] = useState(true);
  const [copiedTdm, setCopiedTdm] = useState(false);
  const [dispatched, setDispatched] = useState(false);

  useEffect(() => {
    async function loadTasking() {
      try {
        const data = await fetchObservationTasking(conjunctionId, secondaryName, hoursToTca);
        setPlan(data);
      } catch (e) {
        console.warn("Failed to load observation tasking plan:", e);
      } finally {
        setLoading(false);
      }
    }
    loadTasking();
  }, [conjunctionId, secondaryName, hoursToTca]);

  const handleCopyTdm = () => {
    if (!plan) return;
    navigator.clipboard.writeText(plan.tdm_command_preview).then(() => {
      setCopiedTdm(true);
      playAudioCue("click");
      setTimeout(() => setCopiedTdm(false), 2500);
    });
  };

  const handleDispatch = () => {
    playAudioCue("affirmative");
    setDispatched(true);
  };

  if (loading || !plan) {
    return (
      <div className="p-8 rounded-card bg-charcoal border border-white/10 animate-pulse text-xs font-mono text-pebble">
        Computing optimal ground sensor pass geometry and covariance shrinkage...
      </div>
    );
  }

  const content = (
    <div className="space-y-5 text-xs font-mono text-bone">
      {/* Header Summary */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 border-b border-white/10 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <Radio className="w-5 h-5 text-sky-400" />
            <h3 className="text-base font-bold text-bone">
              Observation Tasking Optimizer (F12)
            </h3>
            <span className="px-2 py-0.5 rounded bg-sky-950/60 border border-sky-500/40 text-[10px] text-sky-300 font-bold">
              {plan.station_network_size} SSA Ground Stations Ready
            </span>
          </div>
          <p className="text-xs text-ash mt-0.5">
            Target Threat: <span className="text-bone font-bold">{plan.secondary_name}</span> · TCA: in {plan.hours_to_tca}h
          </p>
        </div>

        <div className="flex items-center gap-2">
          <div className="px-3 py-1.5 rounded bg-smoke border border-emerald-500/30 text-emerald-300 flex items-center gap-1.5 text-[11px]">
            <TrendingDown className="w-3.5 h-3.5" />
            <span>Projected Covariance Shrinkage: -{plan.covariance_projection.uncertainty_reduction_pct}%</span>
          </div>
          {onClose && !isEmbedded && (
            <button
              onClick={onClose}
              className="p-1.5 rounded-nav hover:bg-white/10 text-pebble hover:text-bone transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      {/* Covariance Shrinkage Impact Card */}
      <div className="p-4 rounded bg-void/80 border border-emerald-500/30 grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="space-y-1">
          <span className="text-[10px] text-pebble uppercase">Initial In-Track Uncertainty (&sigma;_y):</span>
          <div className="text-xl font-bold text-amber-400">
            {plan.covariance_projection.initial_sigma_in_track_m} m
          </div>
          <span className="text-[10px] text-pebble">Screening TLE Covariance</span>
        </div>

        <div className="space-y-1">
          <span className="text-[10px] text-pebble uppercase">Projected Post-Track Uncertainty (&sigma;_y):</span>
          <div className="text-xl font-bold text-emerald-400 flex items-center gap-2">
            <span>{plan.covariance_projection.projected_sigma_in_track_m} m</span>
            <span className="text-xs text-emerald-300">(-{plan.covariance_projection.uncertainty_reduction_pct}%)</span>
          </div>
          <span className="text-[10px] text-emerald-400">Enables high-confidence miss determination</span>
        </div>

        <div className="space-y-1">
          <span className="text-[10px] text-pebble uppercase">Propellant Saved If CAM Avoided:</span>
          <div className="text-xl font-bold text-sky-400">
            {plan.covariance_projection.projected_fuel_savings_g} g Hydrazine
          </div>
          <span className="text-[10px] text-pebble">Resolves false alarm collision risks</span>
        </div>
      </div>

      {/* Sensor Passes Schedule */}
      <div className="space-y-2">
        <div className="flex items-center justify-between text-xs font-mono">
          <span className="text-bone font-bold">Upcoming Optimal Ground Sensor Pass Windows:</span>
          <span className="text-pebble text-[11px]">Ranked by expected information gain & elevation</span>
        </div>

        <div className="space-y-2">
          {plan.scheduled_passes.map((p) => (
            <div
              key={p.pass_id}
              className={`p-3.5 rounded border transition-all ${
                p.recommended
                  ? "bg-smoke/80 border-sky-500/50 shadow-glass"
                  : "bg-void/60 border-white/5 opacity-80"
              }`}
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-white/5 pb-2">
                <div className="flex items-center gap-2">
                  <span
                    className={`w-2 h-2 rounded-full ${
                      p.recommended ? "bg-sky-400 animate-pulse" : "bg-pebble"
                    }`}
                  />
                  <strong className="text-bone text-xs">{p.station.name}</strong>
                  <span className="text-[10px] text-pebble">({p.station.location})</span>
                </div>
                <div className="flex items-center gap-2 text-[10px]">
                  <span className="px-2 py-0.5 rounded bg-void text-pebble">{p.sensor_modality}</span>
                  {p.recommended && (
                    <span className="px-2 py-0.5 rounded bg-sky-950/60 border border-sky-500/40 text-sky-300 font-bold">
                      RECOMMENDED PRIMARY
                    </span>
                  )}
                </div>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-2 text-[11px] text-ash">
                <div>
                  <span className="text-pebble block text-[10px]">PASS START (UTC):</span>
                  <span className="text-bone">{new Date(p.start_utc).toLocaleTimeString()}</span>
                </div>
                <div>
                  <span className="text-pebble block text-[10px]">DURATION / PEAK EL:</span>
                  <span className="text-bone">{p.duration_min} min / {p.max_elevation_deg}&deg;</span>
                </div>
                <div>
                  <span className="text-pebble block text-[10px]">TRACK QUALITY SNR:</span>
                  <span className="text-emerald-400 font-bold">+{p.track_quality_snr_db} dB</span>
                </div>
                <div>
                  <span className="text-pebble block text-[10px]">COVARIANCE SHADOW:</span>
                  <span className="text-sky-300 font-bold">-{p.shrinkage_contribution_pct}% variance</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* CCSDS 2.0 TDM Preview & Action Dispatch */}
      <div className="p-3.5 rounded bg-void/80 border border-white/10 space-y-2">
        <div className="flex items-center justify-between text-xs">
          <span className="text-bone font-bold">CCSDS 2.0 Tracking Data Message (TDM) Tasking Protocol:</span>
          <button
            onClick={handleCopyTdm}
            className="px-2.5 py-1 rounded bg-smoke hover:bg-white/10 border border-white/10 text-ash hover:text-bone flex items-center gap-1.5 text-[10px] transition-colors"
          >
            {copiedTdm ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
            <span>{copiedTdm ? "Copied" : "Copy TDM"}</span>
          </button>
        </div>

        <pre className="p-2.5 rounded bg-charcoal text-[10px] text-sky-300 overflow-x-auto border border-white/5 font-mono leading-relaxed">
          {plan.tdm_command_preview}
        </pre>

        <div className="flex items-center justify-between pt-2">
          <div className="text-[10px] text-pebble">
            Status: {dispatched ? "Sensor Tasking Dispatched to TIRA Monopulse Radar" : "Ready for Tasking Dispatch"}
          </div>

          <button
            onClick={handleDispatch}
            disabled={dispatched}
            className={`px-4 py-2 rounded-nav font-bold text-xs flex items-center gap-1.5 transition-all ${
              dispatched
                ? "bg-emerald-950/60 border border-emerald-500/50 text-emerald-300"
                : "bg-sky-600 hover:bg-sky-500 text-white shadow-lg shadow-sky-600/30"
            }`}
          >
            {dispatched ? <CheckCircle2 className="w-4 h-4" /> : <Send className="w-4 h-4" />}
            <span>{dispatched ? "Tasking Dispatched to Network" : "Authorize & Dispatch Tasking"}</span>
          </button>
        </div>
      </div>
    </div>
  );

  if (isEmbedded) {
    return (
      <div className="p-5 rounded-card bg-charcoal border border-white/10">
        {content}
      </div>
    );
  }

  return (
    <div className="fixed inset-0 z-50 bg-black/85 backdrop-blur-md flex items-center justify-center p-3 sm:p-6 overflow-y-auto">
      <div className="w-full max-w-3xl max-h-[92vh] overflow-y-auto bg-charcoal border border-white/20 rounded-card shadow-2xl p-6">
        {content}
      </div>
    </div>
  );
}
