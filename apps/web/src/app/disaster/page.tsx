"use client";

import React, { useState } from "react";
import {
  Layers,
  Sparkles,
  Info,
  AlertTriangle,
  CheckCircle,
  Satellite,
  Radio,
  Sliders,
} from "lucide-react";
import { SimulatedBadge } from "../../components/SimulatedBadge";
import { DisasterDeck } from "../../components/DisasterDeck";
import { ConstellationMatrix } from "../../components/ConstellationMatrix";
import { LiveTelemetryStreamer } from "../../components/LiveTelemetryStreamer";
import { playAudioCue } from "../../lib/audio";
import { useAsset } from "../../lib/assetContext";

export default function DisasterPage() {
  const { selectedAssetId, setSelectedAssetId } = useAsset();
  const [simulateDegradedHealth, setSimulateDegradedHealth] = useState(false);
  const [activeTab, setActiveTab] = useState<"deck" | "constellation" | "stream" | "metrics">("deck");

  // Measured values from evaluation/results/disaster.json
  const segmentationMetrics = {
    meanIoU: 0.9548,
    meanDice: 0.9768,
    minIoU: 0.9363,
    maxIoU: 0.9676,
    chipsEvaluated: 15,
  };

  const nominalPriority = 0.78;
  const degradedPriority = 0.31;
  const currentPriority = simulateDegradedHealth ? degradedPriority : nominalPriority;

  return (
    <div className="space-y-6">
      {/* Title Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-4 rounded-card bg-charcoal border border-white/10">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold tracking-tight text-bone flex items-center gap-2">
              <Layers className="w-5 h-5 text-amber-400" />
              Earth Observation & Mission Operations Deck
            </h1>
            <SimulatedBadge />
          </div>
          <p className="text-xs text-ash font-mono mt-0.5">
            Sentinel Synthetic Aperture Radar (SAR) & Optical Multi-Spectral Disaster Intelligence
          </p>
        </div>

        {/* Cloud Penetration Badge */}
        <div className="px-3 py-1.5 rounded-nav bg-smoke border border-emerald-500/30 text-xs font-mono text-emerald-400 flex items-center gap-1.5">
          <Sparkles className="w-3.5 h-3.5" />
          <span>SAR C-Band: All-Weather Cloud Penetrating</span>
        </div>
      </div>

      {/* Navigation Sub-Tabs */}
      <div className="flex items-center gap-2 border-b border-white/10 pb-2 overflow-x-auto">
        <button
          onClick={() => {
            playAudioCue("click");
            setActiveTab("deck");
          }}
          className={`flex items-center gap-2 px-3.5 py-1.5 rounded-nav text-xs font-mono transition-all whitespace-nowrap ${
            activeTab === "deck"
              ? "bg-amber-500/20 text-amber-300 border border-amber-400/50 shadow-glass font-bold"
              : "text-ash hover:text-bone hover:bg-smoke"
          }`}
        >
          <Layers className="w-3.5 h-3.5" />
          <span>Disaster Deck (F7)</span>
        </button>

        <button
          onClick={() => {
            playAudioCue("click");
            setActiveTab("constellation");
          }}
          className={`flex items-center gap-2 px-3.5 py-1.5 rounded-nav text-xs font-mono transition-all whitespace-nowrap ${
            activeTab === "constellation"
              ? "bg-sky-500/20 text-sky-300 border border-sky-400/50 shadow-glass font-bold"
              : "text-ash hover:text-bone hover:bg-smoke"
          }`}
        >
          <Satellite className="w-3.5 h-3.5" />
          <span>Constellation Mode (F8 & F11)</span>
        </button>

        <button
          onClick={() => {
            playAudioCue("click");
            setActiveTab("stream");
          }}
          className={`flex items-center gap-2 px-3.5 py-1.5 rounded-nav text-xs font-mono transition-all whitespace-nowrap ${
            activeTab === "stream"
              ? "bg-emerald-500/20 text-emerald-300 border border-emerald-400/50 shadow-glass font-bold"
              : "text-ash hover:text-bone hover:bg-smoke"
          }`}
        >
          <Radio className="w-3.5 h-3.5" />
          <span>Live Telemetry Streamer (F9)</span>
        </button>

        <button
          onClick={() => {
            playAudioCue("click");
            setActiveTab("metrics");
          }}
          className={`flex items-center gap-2 px-3.5 py-1.5 rounded-nav text-xs font-mono transition-all whitespace-nowrap ${
            activeTab === "metrics"
              ? "bg-smoke text-bone border border-white/20 font-bold"
              : "text-ash hover:text-bone hover:bg-smoke"
          }`}
        >
          <Sliders className="w-3.5 h-3.5" />
          <span>Model Evaluation Metrics</span>
        </button>
      </div>

      {/* Cross-System Health Deferral Toggle & Warning Banner */}
      <div className="p-4 rounded-card bg-charcoal border border-white/10 space-y-3">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 border-b border-white/10 pb-3">
          <div className="text-xs font-mono uppercase tracking-wider text-ash flex items-center gap-2">
            <Info className="w-4 h-4 text-sky-400" />
            Cross-System Health Degradation Interlock (PRD §5.3)
          </div>
          <button
            onClick={() => {
              playAudioCue("click");
              setSimulateDegradedHealth(!simulateDegradedHealth);
            }}
            className={`px-3 py-1.5 rounded-nav text-xs font-mono border transition-all ${
              simulateDegradedHealth
                ? "bg-amber-950/50 border-amber-500 text-amber-300 font-bold"
                : "bg-smoke border-white/15 text-ash hover:text-bone"
            }`}
          >
            {simulateDegradedHealth
              ? "Health Degraded (r_h = 0.68) [Active]"
              : "Simulate Degraded Spacecraft Health (r_h >= 0.50)"}
          </button>
        </div>

        {simulateDegradedHealth ? (
          <div className="p-3 rounded-card bg-amber-950/40 border border-amber-500/50 flex items-center justify-between text-amber-200 text-xs font-mono">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
              <div>
                <strong className="uppercase">Observation Tasking Deferred: </strong>
                Spacecraft health anomaly (r_h &ge; 0.50) forces optical/radar observation task deferral.
                Disaster priority penalized from {nominalPriority.toFixed(2)} &rarr;{" "}
                {degradedPriority.toFixed(2)} to protect spacecraft bus power margins.
              </div>
            </div>
            <span className="shrink-0 px-2 py-0.5 rounded bg-amber-500/20 font-mono text-[10px] font-bold">
              PENALTY -60%
            </span>
          </div>
        ) : (
          <div className="flex items-center gap-2 text-xs text-pebble font-mono">
            <CheckCircle className="w-3.5 h-3.5 text-emerald-400" />
            <span>
              Spacecraft health nominal (r_h &lt; 0.50). Full Earth observation instrument duty cycle permitted.
            </span>
          </div>
        )}
      </div>

      {/* Tab 1: Disaster Intelligence Deck */}
      {activeTab === "deck" && (
        <DisasterDeck simulateDegradedHealth={simulateDegradedHealth} />
      )}

      {/* Tab 2: Constellation Mode & Multi-Asset Conjunction Matrix */}
      {activeTab === "constellation" && (
        <ConstellationMatrix onSelectAsset={(id) => setSelectedAssetId(id)} />
      )}

      {/* Tab 3: Live Telemetry Streamer */}
      {activeTab === "stream" && (
        <div className="space-y-4">
          <LiveTelemetryStreamer assetId={selectedAssetId} />
        </div>
      )}

      {/* Tab 4: Model Evaluation Metrics */}
      {activeTab === "metrics" && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="p-5 rounded-card bg-charcoal border border-white/10 space-y-4">
            <h3 className="text-xs uppercase font-mono tracking-wider text-ash border-b border-white/10 pb-2">
              PyTorch Lightweight U-Net Metrics (Measured)
            </h3>
            <div className="grid grid-cols-2 gap-3 text-xs font-mono">
              <div className="p-3 rounded bg-smoke">
                <div className="text-[10px] text-pebble">Mean IoU</div>
                <div className="text-emerald-400 font-bold text-lg">
                  {segmentationMetrics.meanIoU.toFixed(4)}
                </div>
              </div>
              <div className="p-3 rounded bg-smoke">
                <div className="text-[10px] text-pebble">Mean Dice F1</div>
                <div className="text-emerald-400 font-bold text-lg">
                  {segmentationMetrics.meanDice.toFixed(4)}
                </div>
              </div>
              <div className="p-3 rounded bg-smoke">
                <div className="text-[10px] text-pebble">Min IoU (Worst Chip)</div>
                <div className="text-bone font-semibold text-base">
                  {segmentationMetrics.minIoU.toFixed(4)}
                </div>
              </div>
              <div className="p-3 rounded bg-smoke">
                <div className="text-[10px] text-pebble">Max IoU (Best Chip)</div>
                <div className="text-bone font-semibold text-base">
                  {segmentationMetrics.maxIoU.toFixed(4)}
                </div>
              </div>
            </div>
            <div className="p-3 rounded bg-void/80 border border-white/5 text-[11px] font-mono text-pebble">
              Benchmark evaluated on 15 synthetic chips modeled after Brahmaputra River Basin and Emilia-Romagna flooding events.
            </div>
          </div>

          <div className="p-5 rounded-card bg-charcoal border border-white/10 space-y-3 font-mono text-xs">
            <h3 className="text-ash uppercase tracking-wider border-b border-white/10 pb-2">
              Multi-Spectral Sensor Parameters
            </h3>
            <div className="space-y-2 text-pebble">
              <div className="flex justify-between py-1 border-b border-white/5">
                <span>SAR Instrument:</span>
                <span className="text-bone">Sentinel-1 C-SAR (5.405 GHz)</span>
              </div>
              <div className="flex justify-between py-1 border-b border-white/5">
                <span>Spatial Resolution:</span>
                <span className="text-bone">10m Ground Sampling Distance (IW Mode)</span>
              </div>
              <div className="flex justify-between py-1 border-b border-white/5">
                <span>Optical Complement:</span>
                <span className="text-bone">Sentinel-2 MSI (13 Bands, VNIR + SWIR)</span>
              </div>
              <div className="flex justify-between py-1 border-b border-white/5">
                <span>Water Mask Threshold:</span>
                <span className="text-emerald-400">&Delta;&sigma;⁰ &lt; -3.8 dB drop vs baseline</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
