"use client";

import React, { useState, useEffect, useCallback, useMemo } from "react";
import {
  Layers,
  Crosshair,
  Sliders,
  Cpu,
  Clock,
  Sparkles,
  Info,
  RefreshCw,
  Target,
  BarChart2,
} from "lucide-react";
import { UncertaintyLabRequest, UncertaintyLabResponse } from "../lib/types";
import { runUncertaintyLab } from "../lib/api";
import { StatusBadge } from "./StatusBadge";
import { SimulatedBadge } from "./SimulatedBadge";
import { playAudioCue } from "../lib/audio";

interface UncertaintyLabProps {
  conjunctionId?: string;
  secondaryName?: string;
  initialMissM?: number;
}

export function UncertaintyLab({
  conjunctionId = "CONJ-29834",
  secondaryName = "FENGYUN-1C-DEB-29834",
  initialMissM = 315.4,
}: UncertaintyLabProps) {
  const [missX, setMissX] = useState<number>(initialMissM);
  const [missY, setMissY] = useState<number>(0.0);
  const [sigmaX, setSigmaX] = useState<number>(50.0);
  const [sigmaY, setSigmaY] = useState<number>(250.0);
  const [sampleSize, setSampleSize] = useState<number>(2000);
  const [labData, setLabData] = useState<UncertaintyLabResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);

  const fetchLabData = useCallback(
    async (mx = missX, my = missY, sx = sigmaX, sy = sigmaY, trials = sampleSize) => {
      setLoading(true);
      try {
        const req: UncertaintyLabRequest = {
          conjunction_id: conjunctionId,
          secondary_name: secondaryName,
          miss_x_m: mx,
          miss_y_m: my,
          sigma_x_m: sx,
          sigma_y_m: sy,
          rho: 0.0,
          radius_m: 5.0,
          num_trials: trials,
        };
        const res = await runUncertaintyLab(req);
        setLabData(res);
      } catch (err) {
        console.error("Error running uncertainty lab:", err);
      } finally {
        setLoading(false);
      }
    },
    [conjunctionId, secondaryName, missX, missY, sigmaX, sigmaY, sampleSize]
  );

  useEffect(() => {
    fetchLabData();
  }, [fetchLabData]);

  // Coordinate scaling for 500x500 B-Plane canvas
  // World space: [-600, +600] meters along X and Y
  const WORLD_SPAN = 1200; // meters total view width
  const CANVAS_SIZE = 500;
  const toCanvas = (worldCoord: number) => {
    return (worldCoord + WORLD_SPAN / 2) * (CANVAS_SIZE / WORLD_SPAN);
  };
  const toCanvasScale = (meters: number) => {
    return (meters / WORLD_SPAN) * CANVAS_SIZE;
  };

  const comp = labData?.comparison;
  const cov = labData?.uncertainty_covariance;

  return (
    <div className="p-5 rounded-card bg-charcoal border border-white/10 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-white/10 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <Layers className="w-5 h-5 text-rose-400" />
            <h2 className="text-base font-bold text-bone">
              Conjunction Uncertainty Lab & B-Plane Encounter Geometry
            </h2>
            <SimulatedBadge />
          </div>
          <p className="text-xs text-ash font-mono mt-0.5">
            Foster 2-D Numerical Gaussian PDF vs. 2,000-Particle Monte Carlo Covariance Propagation
          </p>
        </div>

        {/* Screening Disclaimer Badge */}
        <div className="px-3 py-1.5 rounded-nav bg-smoke border border-amber-500/30 text-xs font-mono text-amber-300 flex items-center gap-1.5">
          <Info className="w-3.5 h-3.5" />
          <span>Screening-Grade (Assumed Covariance)</span>
        </div>
      </div>

      {/* Main Grid: Left B-Plane Encounter Canvas, Right Parameter Controls & Comparison */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: 2D B-Plane Encounter Plane Visualizer */}
        <div className="lg:col-span-7 space-y-3">
          <div className="flex items-center justify-between text-xs font-mono text-ash uppercase">
            <span className="flex items-center gap-1.5">
              <Crosshair className="w-4 h-4 text-rose-400" />
              B-Plane Encounter Cross-Section (Scale: &plusmn;600m)
            </span>
            <div className="flex items-center gap-3 text-[11px]">
              <span className="flex items-center gap-1 text-arterial">
                <span className="w-2 h-2 rounded-full bg-arterial inline-block" /> Hit ($R \le 5m$)
              </span>
              <span className="flex items-center gap-1 text-pebble">
                <span className="w-2 h-2 rounded-full bg-sky-400/40 inline-block" /> Miss Sample
              </span>
            </div>
          </div>

          <div className="relative w-full aspect-square bg-void rounded-card border border-white/10 overflow-hidden flex items-center justify-center p-2">
            <svg
              viewBox={`0 0 ${CANVAS_SIZE} ${CANVAS_SIZE}`}
              className="w-full h-full select-none"
            >
              {/* Grid Lines */}
              <defs>
                <pattern id="bplane_grid" width="41.66" height="41.66" patternUnits="userSpaceOnUse">
                  <path d="M 41.66 0 L 0 0 0 41.66" fill="none" stroke="#1c1b1c" strokeWidth="1" />
                </pattern>
                {/* Radial Glow Gradient for Encounter Center */}
                <radialGradient id="targetGlow" cx="50%" cy="50%" r="50%">
                  <stop offset="0%" stopColor="#fe1e34" stopOpacity="0.4" />
                  <stop offset="100%" stopColor="#fe1e34" stopOpacity="0" />
                </radialGradient>
              </defs>
              <rect width={CANVAS_SIZE} height={CANVAS_SIZE} fill="url(#bplane_grid)" />

              {/* B-Plane Principal Axes */}
              <line
                x1="0"
                y1={CANVAS_SIZE / 2}
                x2={CANVAS_SIZE}
                y2={CANVAS_SIZE / 2}
                stroke="#2a292a"
                strokeWidth="1.5"
                strokeDasharray="4 4"
              />
              <line
                x1={CANVAS_SIZE / 2}
                y1="0"
                x2={CANVAS_SIZE / 2}
                y2={CANVAS_SIZE}
                stroke="#2a292a"
                strokeWidth="1.5"
                strokeDasharray="4 4"
              />

              {/* Range Circles (100m, 200m, 400m) */}
              {[100, 200, 400].map((dist) => (
                <circle
                  key={dist}
                  cx={CANVAS_SIZE / 2}
                  cy={CANVAS_SIZE / 2}
                  r={toCanvasScale(dist)}
                  fill="none"
                  stroke="#222"
                  strokeWidth="1"
                />
              ))}

              {/* Covariance Error Ellipses (1-sigma, 2-sigma, 3-sigma) centered at (missX, missY) */}
              {cov && (
                <g transform={`translate(${toCanvas(missX)}, ${toCanvas(missY)})`}>
                  {/* 3-Sigma Ellipse */}
                  <ellipse
                    cx="0"
                    cy="0"
                    rx={toCanvasScale(cov.ellipse_3sigma.semi_minor_m)}
                    ry={toCanvasScale(cov.ellipse_3sigma.semi_major_m)}
                    fill="rgba(56, 189, 248, 0.03)"
                    stroke="#38bdf8"
                    strokeWidth="1"
                    strokeDasharray="4 4"
                    opacity="0.3"
                  />
                  {/* 2-Sigma Ellipse */}
                  <ellipse
                    cx="0"
                    cy="0"
                    rx={toCanvasScale(cov.ellipse_2sigma.semi_minor_m)}
                    ry={toCanvasScale(cov.ellipse_2sigma.semi_major_m)}
                    fill="rgba(56, 189, 248, 0.06)"
                    stroke="#38bdf8"
                    strokeWidth="1.2"
                    strokeDasharray="3 3"
                    opacity="0.5"
                  />
                  {/* 1-Sigma Ellipse */}
                  <ellipse
                    cx="0"
                    cy="0"
                    rx={toCanvasScale(cov.ellipse_1sigma.semi_minor_m)}
                    ry={toCanvasScale(cov.ellipse_1sigma.semi_major_m)}
                    fill="rgba(56, 189, 248, 0.12)"
                    stroke="#38bdf8"
                    strokeWidth="1.8"
                    opacity="0.9"
                  />
                  {/* Ellipse Center Marker */}
                  <circle cx="0" cy="0" r="3" fill="#38bdf8" />
                </g>
              )}

              {/* Monte Carlo Scatter Cloud */}
              {labData?.scatter_points.map((pt, idx) => {
                const cx = toCanvas(pt.x);
                const cy = toCanvas(pt.y);
                if (cx < 0 || cx > CANVAS_SIZE || cy < 0 || cy > CANVAS_SIZE) return null;
                return (
                  <circle
                    key={idx}
                    cx={cx}
                    cy={cy}
                    r={pt.is_hit ? 4.5 : 1.5}
                    fill={pt.is_hit ? "#fe1e34" : "#7dd3fc"}
                    opacity={pt.is_hit ? 1 : 0.45}
                    stroke={pt.is_hit ? "#ffffff" : "none"}
                    strokeWidth={pt.is_hit ? 1.5 : 0}
                    className={pt.is_hit ? "animate-pulse" : ""}
                  />
                );
              })}

              {/* Primary Satellite Hard-Body Sphere (Combined R=5m at Origin) */}
              <circle
                cx={CANVAS_SIZE / 2}
                cy={CANVAS_SIZE / 2}
                r={toCanvasScale(25)}
                fill="url(#targetGlow)"
              />
              <circle
                cx={CANVAS_SIZE / 2}
                cy={CANVAS_SIZE / 2}
                r={toCanvasScale(5)}
                fill="#ffffff"
                stroke="#fe1e34"
                strokeWidth="2"
              />

              {/* Labels on Canvas */}
              <text
                x={CANVAS_SIZE / 2 + 10}
                y={CANVAS_SIZE / 2 - 10}
                fill="#ffffff"
                fontSize="10"
                fontFamily="monospace"
                fontWeight="bold"
              >
                S2A Target (R=5m)
              </text>
              <text
                x={toCanvas(missX) + 8}
                y={toCanvas(missY) - 8}
                fill="#38bdf8"
                fontSize="10"
                fontFamily="monospace"
              >
                Debris Peak ({missX.toFixed(0)}m)
              </text>
            </svg>

            {/* Inset Canvas Status Pill */}
            <div className="absolute top-3 left-3 px-3 py-1.5 rounded-nav bg-charcoal/85 backdrop-blur-md border border-white/10 text-xs font-mono flex items-center gap-2">
              <span className="text-pebble">Encounter Distance:</span>
              <span className="text-bone font-bold">
                {Math.sqrt(missX * missX + missY * missY).toFixed(1)} m
              </span>
            </div>
          </div>
        </div>

        {/* Right: Controls & Analytical vs Empirical Comparison */}
        <div className="lg:col-span-5 space-y-4">
          {/* Sliders for Sensitivity Testing */}
          <div className="p-4 rounded-card bg-smoke/40 border border-white/5 space-y-4">
            <h3 className="text-xs font-mono uppercase text-ash flex items-center justify-between">
              <span className="flex items-center gap-1.5">
                <Sliders className="w-3.5 h-3.5 text-sky-400" />
                Uncertainty & Encounter Controls
              </span>
              <button
                onClick={() => {
                  playAudioCue("click");
                  setMissX(45.0);
                  setMissY(0.0);
                  setSigmaX(50.0);
                  setSigmaY(250.0);
                  fetchLabData(45.0, 0.0, 50.0, 250.0);
                }}
                className="text-[11px] text-sky-400 hover:text-sky-300 font-mono flex items-center gap-1"
              >
                <RefreshCw className="w-3 h-3" />
                <span>Reset</span>
              </button>
            </h3>

            {/* Miss Distance Slider */}
            <div className="space-y-1.5">
              <div className="flex justify-between text-xs font-mono">
                <span className="text-pebble">Encounter Miss X:</span>
                <span className="text-bone font-bold">{missX.toFixed(1)} m</span>
              </div>
              <input
                type="range"
                min="0"
                max="500"
                step="5"
                value={missX}
                onChange={(e) => {
                  const val = parseFloat(e.target.value);
                  setMissX(val);
                  fetchLabData(val, missY, sigmaX, sigmaY);
                }}
                className="w-full accent-rose-500 cursor-pointer"
              />
            </div>

            {/* Sigma X (Cross-track uncertainty) */}
            <div className="space-y-1.5">
              <div className="flex justify-between text-xs font-mono">
                <span className="text-pebble">Normal Uncertainty (&sigma;_x):</span>
                <span className="text-sky-300 font-bold">{sigmaX.toFixed(1)} m</span>
              </div>
              <input
                type="range"
                min="10"
                max="150"
                step="5"
                value={sigmaX}
                onChange={(e) => {
                  const val = parseFloat(e.target.value);
                  setSigmaX(val);
                  fetchLabData(missX, missY, val, sigmaY);
                }}
                className="w-full accent-sky-400 cursor-pointer"
              />
            </div>

            {/* Sigma Y (Along-track uncertainty) */}
            <div className="space-y-1.5">
              <div className="flex justify-between text-xs font-mono">
                <span className="text-pebble">In-Track Uncertainty (&sigma;_y):</span>
                <span className="text-sky-300 font-bold">{sigmaY.toFixed(1)} m</span>
              </div>
              <input
                type="range"
                min="50"
                max="500"
                step="10"
                value={sigmaY}
                onChange={(e) => {
                  const val = parseFloat(e.target.value);
                  setSigmaY(val);
                  fetchLabData(missX, missY, sigmaX, val);
                }}
                className="w-full accent-sky-400 cursor-pointer"
              />
            </div>

            {/* Monte Carlo Particle Count */}
            <div className="space-y-1.5">
              <div className="flex justify-between text-xs font-mono">
                <span className="text-pebble">Monte Carlo Particle Cloud:</span>
                <span className="text-bone font-bold">{sampleSize.toLocaleString()} Trials</span>
              </div>
              <div className="grid grid-cols-3 gap-2">
                {[1000, 2000, 5000].map((count) => (
                  <button
                    key={count}
                    onClick={() => {
                      playAudioCue("click");
                      setSampleSize(count);
                      fetchLabData(missX, missY, sigmaX, sigmaY, count);
                    }}
                    className={`py-1 text-xs font-mono rounded border transition-all ${
                      sampleSize === count
                        ? "bg-sky-500/20 border-sky-400 text-sky-300 font-bold"
                        : "bg-void border-white/5 text-ash hover:border-white/20"
                    }`}
                  >
                    {count.toLocaleString()}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Side-by-Side Benchmark Arena: Foster 2-D vs Monte Carlo */}
          {comp && (
            <div className="p-4 rounded-card bg-void/80 border border-white/10 space-y-4">
              <div className="flex items-center justify-between border-b border-white/10 pb-2">
                <span className="text-xs font-mono uppercase tracking-wider text-ash flex items-center gap-1.5">
                  <BarChart2 className="w-3.5 h-3.5 text-emerald-400" />
                  Algorithm Evaluation & Latency
                </span>
                <StatusBadge level={comp.risk_class} size="sm" />
              </div>

              <div className="grid grid-cols-2 gap-3 text-xs font-mono">
                {/* Foster 2-D Box */}
                <div className="p-3 rounded bg-smoke/80 border border-sky-500/30 space-y-1.5">
                  <div className="flex justify-between items-center text-[10px] text-sky-300 font-bold uppercase">
                    <span>Foster 2-D Analytical</span>
                    <Sparkles className="w-3 h-3 text-sky-400" />
                  </div>
                  <div className="text-base font-bold text-bone">
                    {comp.foster_2d_analytical_pc.toExponential(2)}
                  </div>
                  <div className="flex items-center gap-1 text-[10px] text-pebble">
                    <Clock className="w-2.5 h-2.5" />
                    <span>{comp.foster_latency_ms.toFixed(2)} ms latency</span>
                  </div>
                </div>

                {/* Monte Carlo Box */}
                <div className="p-3 rounded bg-smoke/80 border border-white/10 space-y-1.5">
                  <div className="flex justify-between items-center text-[10px] text-pebble font-bold uppercase">
                    <span>Monte Carlo Empirical</span>
                    <Cpu className="w-3 h-3 text-pebble" />
                  </div>
                  <div className="text-base font-bold text-bone">
                    {comp.monte_carlo_empirical_pc === 0
                      ? `< ${(1 / comp.monte_carlo_trials).toExponential(1)}`
                      : comp.monte_carlo_empirical_pc.toExponential(2)}
                  </div>
                  <div className="flex items-center gap-1 text-[10px] text-pebble">
                    <Clock className="w-2.5 h-2.5" />
                    <span>{comp.monte_carlo_latency_ms.toFixed(2)} ms ({comp.monte_carlo_hits} hits)</span>
                  </div>
                </div>
              </div>

              {/* Speedup and Error Stats */}
              <div className="flex items-center justify-between text-xs font-mono text-pebble bg-smoke/40 p-2.5 rounded">
                <span>Analytical Speedup:</span>
                <span className="text-emerald-400 font-bold">
                  {comp.speedup_factor.toFixed(1)}x faster than MC
                </span>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
