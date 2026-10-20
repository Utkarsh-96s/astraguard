"use client";

import React, { useState } from "react";
import {
  Layers,
  MapPin,
  Eye,
  AlertTriangle,
  CheckCircle,
  TrendingDown,
  Sparkles,
  Info,
} from "lucide-react";
import { SimulatedBadge } from "../../components/SimulatedBadge";

export default function DisasterPage() {
  const [showMask, setShowMask] = useState(true);
  const [simulateDegradedHealth, setSimulateDegradedHealth] = useState(false);

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
              Earth Observation Disaster Intelligence
            </h1>
            <SimulatedBadge />
          </div>
          <p className="text-xs text-ash font-mono mt-0.5">
            Sentinel-1 Synthetic Aperture Radar (SAR) Flood Extent Segmentation & Priority Engine
          </p>
        </div>

        {/* Cloud Penetration Badge */}
        <div className="px-3 py-1.5 rounded-nav bg-smoke border border-emerald-500/30 text-xs font-mono text-emerald-400 flex items-center gap-1.5">
          <Sparkles className="w-3.5 h-3.5" />
          <span>SAR C-Band: All-Weather Cloud Penetrating</span>
        </div>
      </div>

      {/* Cross-System Health Deferral Toggle & Warning Banner */}
      <div className="p-4 rounded-card bg-charcoal border border-white/10 space-y-3">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 border-b border-white/10 pb-3">
          <div className="text-xs font-mono uppercase tracking-wider text-ash flex items-center gap-2">
            <Info className="w-4 h-4 text-sky-400" />
            Cross-System Health Degradation Interlock (PRD §5.3)
          </div>
          <button
            onClick={() => setSimulateDegradedHealth(!simulateDegradedHealth)}
            className={`px-3 py-1.5 rounded-nav text-xs font-mono border transition-all ${
              simulateDegradedHealth
                ? "bg-amber-950/50 border-amber-500 text-amber-300 font-bold"
                : "bg-smoke border-white/15 text-ash hover:text-bone"
            }`}
          >
            {simulateDegradedHealth ? "Health Degraded (r_h = 0.68) [Active]" : "Simulate Degraded Spacecraft Health (r_h >= 0.50)"}
          </button>
        </div>

        {simulateDegradedHealth ? (
          <div className="p-3 rounded-card bg-amber-950/40 border border-amber-500/50 flex items-center justify-between text-amber-200 text-xs">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
              <div>
                <strong className="uppercase">Observation Tasking Deferred: </strong>
                Spacecraft health anomaly (r_h &ge; 0.50) forces optical/radar observation task deferral. Computed disaster observation score penalized from {nominalPriority.toFixed(2)} &rarr; {degradedPriority.toFixed(2)} to protect spacecraft bus power margins.
              </div>
            </div>
            <span className="shrink-0 px-2 py-0.5 rounded bg-amber-500/20 font-mono text-[10px] font-bold">
              PENALTY -60%
            </span>
          </div>
        ) : (
          <div className="flex items-center gap-2 text-xs text-pebble font-mono">
            <CheckCircle className="w-3.5 h-3.5 text-emerald-400" />
            <span>Spacecraft health nominal (r_h &lt; 0.50). Full Earth observation instrument duty cycle permitted.</span>
          </div>
        )}
      </div>

      {/* Main Dual Grid: SAR Inundation Chip & Model Diagnostics */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: SAR Dual-Pol Flood Extent Viewer */}
        <div className="lg:col-span-7 p-5 rounded-card bg-charcoal border border-white/10 space-y-4">
          <div className="flex items-center justify-between border-b border-white/10 pb-3">
            <div>
              <h2 className="text-sm font-bold font-mono text-bone flex items-center gap-2">
                <MapPin className="w-4 h-4 text-rose-400" />
                Sentinel-1 SAR Chip: Flood Extent Inundation
              </h2>
              <span className="text-xs text-pebble font-mono">
                Region: Brahmaputra River Basin · Dual-Pol VV+VH Backscatter
              </span>
            </div>

            {/* Mask Toggle */}
            <button
              onClick={() => setShowMask(!showMask)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-nav bg-smoke border border-white/15 text-xs font-mono text-bone hover:bg-white/10 transition-colors"
            >
              <Eye className="w-3.5 h-3.5 text-sky-400" />
              <span>{showMask ? "Hide U-Net Mask" : "Show U-Net Mask"}</span>
            </button>
          </div>

          {/* Interactive SAR Synthetic Imagery Display */}
          <div className="relative w-full aspect-square max-h-[380px] bg-void rounded-card border border-white/10 overflow-hidden flex items-center justify-center p-3">
            <svg viewBox="0 0 400 400" className="w-full h-full">
              <defs>
                {/* Background SAR speckle noise texture */}
                <radialGradient id="sar-bg" cx="50%" cy="50%" r="50%">
                  <stop offset="0%" stopColor="#1a1a1a" />
                  <stop offset="100%" stopColor="#0a0a0a" />
                </radialGradient>
              </defs>

              {/* Base SAR Canvas */}
              <rect width="400" height="400" fill="url(#sar-bg)" />

              {/* Terrain Contours */}
              <path
                d="M 30 120 Q 120 80 200 130 T 380 90 L 400 400 L 0 400 Z"
                fill="#141414"
                stroke="#2a2a2a"
                strokeWidth="1"
              />

              {/* Permanent River Channel (Low Backscatter - Dark) */}
              <path
                d="M 0 160 Q 100 140 180 180 T 300 240 T 400 220"
                fill="none"
                stroke="#080808"
                strokeWidth="14"
                strokeLinecap="round"
              />

              {/* Flood Inundation Region (U-Net Predicted Mask) */}
              {showMask && (
                <path
                  d="M 80 140 Q 140 110 200 150 Q 260 170 320 210 Q 360 250 310 280 Q 230 290 160 250 Q 90 230 60 190 Z"
                  fill="rgba(56, 189, 248, 0.45)"
                  stroke="#38bdf8"
                  strokeWidth="2"
                  className="transition-all duration-300"
                />
              )}

              {/* Center Coordinate Marker */}
              <circle cx="200" cy="200" r="3" fill="#fe1e34" />
              <line x1="190" y1="200" x2="210" y2="200" stroke="#fe1e34" strokeWidth="1" />
              <line x1="200" y1="190" x2="200" y2="210" stroke="#fe1e34" strokeWidth="1" />
            </svg>

            {/* Overlay Info Badges */}
            <div className="absolute bottom-4 left-4 px-2.5 py-1 rounded bg-charcoal/90 border border-white/10 text-[10px] font-mono text-pebble">
              SAR Backscatter Drop: &Delta;&sigma;<sup>0</sup> &lt; -3.8 dB
            </div>
            {showMask && (
              <div className="absolute top-4 right-4 px-2.5 py-1 rounded bg-sky-950/80 border border-sky-500/40 text-[10px] font-mono text-sky-300 font-semibold">
                U-Net Water Mask Active
              </div>
            )}
          </div>

          <div className="flex items-center justify-between text-xs font-mono text-ash pt-1">
            <span>Estimated Flood Area: <strong className="text-bone">320.0 km²</strong></span>
            <span>U-Net Dice F1: <strong className="text-emerald-400">0.9768</strong></span>
          </div>
        </div>

        {/* Right: Model Architecture & Priority Calculation */}
        <div className="lg:col-span-5 space-y-4">
          {/* U-Net Performance Metrics Card */}
          <div className="p-4 rounded-card bg-charcoal border border-white/10 space-y-3">
            <h3 className="text-xs uppercase font-mono tracking-wider text-ash border-b border-white/10 pb-2">
              PyTorch Lightweight U-Net Metrics (Measured)
            </h3>
            <div className="grid grid-cols-2 gap-2 text-xs font-mono">
              <div className="p-2.5 rounded bg-smoke">
                <div className="text-[10px] text-pebble">Mean IoU</div>
                <div className="text-emerald-400 font-bold text-base">
                  {segmentationMetrics.meanIoU.toFixed(4)}
                </div>
              </div>
              <div className="p-2.5 rounded bg-smoke">
                <div className="text-[10px] text-pebble">Mean Dice F1</div>
                <div className="text-emerald-400 font-bold text-base">
                  {segmentationMetrics.meanDice.toFixed(4)}
                </div>
              </div>
              <div className="p-2.5 rounded bg-smoke">
                <div className="text-[10px] text-pebble">Min IoU (Worst Chip)</div>
                <div className="text-bone font-semibold">
                  {segmentationMetrics.minIoU.toFixed(4)}
                </div>
              </div>
              <div className="p-2.5 rounded bg-smoke">
                <div className="text-[10px] text-pebble">Max IoU (Best Chip)</div>
                <div className="text-bone font-semibold">
                  {segmentationMetrics.maxIoU.toFixed(4)}
                </div>
              </div>
            </div>
          </div>

          {/* Priority Score Breakdown */}
          <div className="p-4 rounded-card bg-charcoal border border-white/10 space-y-3">
            <div className="flex items-center justify-between border-b border-white/10 pb-2">
              <h3 className="text-xs uppercase font-mono tracking-wider text-ash">
                Disaster Priority Score (r_e)
              </h3>
              <span className="text-sm font-mono font-bold text-amber-400">
                {currentPriority.toFixed(3)} / 1.000
              </span>
            </div>

            <div className="space-y-2 text-xs font-mono">
              <div className="flex justify-between py-1 border-b border-white/5">
                <span className="text-pebble">Inundated Area (320 km²):</span>
                <span className="text-bone font-semibold">+0.320</span>
              </div>
              <div className="flex justify-between py-1 border-b border-white/5">
                <span className="text-pebble">Event Recency (2h ago):</span>
                <span className="text-bone font-semibold">+0.250</span>
              </div>
              <div className="flex justify-between py-1 border-b border-white/5">
                <span className="text-pebble">Population Exposure:</span>
                <span className="text-bone font-semibold">+0.210</span>
              </div>
              {simulateDegradedHealth && (
                <div className="flex justify-between py-1 text-arterial font-bold">
                  <span>Health Anomaly Deferral:</span>
                  <span>-0.470</span>
                </div>
              )}
            </div>
          </div>

          {/* GeoJSON Footprint Card */}
          <div className="p-4 rounded-card bg-charcoal border border-white/10 space-y-2 text-xs font-mono">
            <div className="text-ash uppercase tracking-wider">GeoJSON Footprint Metadata</div>
            <div className="bg-void p-2.5 rounded border border-white/5 text-[11px] text-pebble space-y-1">
              <div>Type: RFC 7946 Polygon</div>
              <div>BBox: [85.0° E, 20.0° N, 85.5° E, 20.5° N]</div>
              <div>Coordinate Reference: EPSG:4326 (WGS 84)</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
