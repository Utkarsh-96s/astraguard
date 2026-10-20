"use client";

import React, { useState } from "react";
import {
  Activity,
  Cpu,
  Flame,
  Zap,
  RotateCcw,
  CheckCircle,
  AlertTriangle,
  TrendingUp,
} from "lucide-react";
import { SimulatedBadge } from "../../components/SimulatedBadge";

interface ChannelData {
  name: string;
  subsystem: string;
  unit: string;
  current: number;
  normalRange: [number, number];
  anomalous: boolean;
  history: number[];
}

export default function HealthPage() {
  const [selectedChannel, setSelectedChannel] = useState<string>("eps_battery_temp_c");

  const channels: Record<string, ChannelData> = {
    eps_battery_temp_c: {
      name: "EPS Battery Cell Temperature",
      subsystem: "Electric Power (EPS)",
      unit: "°C",
      current: 38.6,
      normalRange: [15.0, 32.0],
      anomalous: true,
      history: [24.1, 24.5, 25.0, 26.2, 28.1, 31.5, 34.2, 36.8, 38.6],
    },
    bus_voltage_v: {
      name: "Main Unregulated Bus Voltage",
      subsystem: "Electric Power (EPS)",
      unit: "V",
      current: 27.9,
      normalRange: [27.0, 29.0],
      anomalous: false,
      history: [28.1, 28.2, 28.0, 28.1, 27.9, 28.0, 27.8, 27.9, 27.9],
    },
    adcs_gyro_rate_dps: {
      name: "ADCS Inertial Gyro Slew Rate",
      subsystem: "Attitude & Orbit (ADCS)",
      unit: "°/s",
      current: 0.014,
      normalRange: [0.001, 0.035],
      anomalous: false,
      history: [0.012, 0.015, 0.013, 0.014, 0.011, 0.016, 0.013, 0.015, 0.014],
    },
    solar_array_current_a: {
      name: "Solar Array Primary Current",
      subsystem: "Power Generation",
      unit: "A",
      current: 14.2,
      normalRange: [8.0, 18.0],
      anomalous: false,
      history: [15.2, 15.0, 14.8, 14.5, 14.2, 14.3, 14.1, 14.4, 14.2],
    },
    obc_cpu_load_pct: {
      name: "On-Board Computer CPU Utilization",
      subsystem: "Data Handling (OBC)",
      unit: "%",
      current: 42.5,
      normalRange: [15.0, 65.0],
      anomalous: false,
      history: [35.0, 36.2, 38.1, 40.0, 41.2, 39.5, 41.8, 43.1, 42.5],
    },
  };

  const active = channels[selectedChannel];

  // SVG Chart Dimensions
  const chartWidth = 600;
  const chartHeight = 220;
  const padding = 30;

  const minVal = Math.min(...active.history, active.normalRange[0]) * 0.9;
  const maxVal = Math.max(...active.history, active.normalRange[1]) * 1.1;

  const getX = (idx: number) =>
    padding + (idx / (active.history.length - 1)) * (chartWidth - padding * 2);
  const getY = (val: number) =>
    chartHeight -
    padding -
    ((val - minVal) / (maxVal - minVal || 1)) * (chartHeight - padding * 2);

  const pointsPath = active.history
    .map((val, idx) => `${idx === 0 ? "M" : "L"} ${getX(idx)} ${getY(val)}`)
    .join(" ");

  const normalMinY = getY(active.normalRange[0]);
  const normalMaxY = getY(active.normalRange[1]);

  return (
    <div className="space-y-6">
      {/* Title Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-4 rounded-card bg-charcoal border border-white/10">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold tracking-tight text-bone flex items-center gap-2">
              <Activity className="w-5 h-5 text-sky-400" />
              Spacecraft Subsystem Health AI
            </h1>
            <SimulatedBadge />
          </div>
          <p className="text-xs text-ash font-mono mt-0.5">
            Deep PyTorch LSTM Autoencoder Reconstruction Residuals & Calibrated Persistence Filter
          </p>
        </div>

        {/* Benchmark Pill */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-nav bg-smoke border border-white/15 text-xs font-mono">
          <TrendingUp className="w-3.5 h-3.5 text-emerald-400" />
          <span className="text-ash">False Alarm Reduction:</span>
          <span className="text-emerald-400 font-bold">-71.4% vs IsoForest</span>
        </div>
      </div>

      {/* Subsystem Health Cards Grid */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        {Object.entries(channels).map(([key, ch]) => {
          const isSelected = selectedChannel === key;
          return (
            <button
              key={key}
              onClick={() => setSelectedChannel(key)}
              className={`p-3 rounded-card text-left transition-all border ${
                isSelected
                  ? "bg-smoke border-sky-400/80 shadow-glass"
                  : "bg-charcoal border-white/10 hover:border-white/20"
              }`}
            >
              <div className="flex items-center justify-between text-[11px] font-mono text-ash mb-1">
                <span className="truncate">{ch.subsystem.split(" ")[0]}</span>
                {ch.anomalous ? (
                  <span className="w-2 h-2 rounded-full bg-arterial animate-ping" />
                ) : (
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                )}
              </div>
              <div className="text-lg font-bold font-mono text-bone">
                {ch.current} <span className="text-xs text-pebble">{ch.unit}</span>
              </div>
              <div className="text-[10px] text-pebble truncate mt-0.5">{ch.name}</div>
            </button>
          );
        })}
      </div>

      {/* Main Analysis Dual Section */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Telemetry Time Series Chart */}
        <div className="lg:col-span-8 p-5 rounded-card bg-charcoal border border-white/10 space-y-4">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 border-b border-white/10 pb-3">
            <div>
              <h2 className="text-sm font-bold font-mono text-bone flex items-center gap-2">
                {active.name} ({active.subsystem})
              </h2>
              <span className="text-xs text-pebble font-mono">
                Nominal Range: [{active.normalRange[0]} - {active.normalRange[1]} {active.unit}]
              </span>
            </div>
            <div className="flex items-center gap-2 font-mono text-xs">
              {active.anomalous ? (
                <span className="px-2.5 py-0.5 rounded bg-red-950/50 border border-arterial text-red-300 flex items-center gap-1 font-semibold">
                  <AlertTriangle className="w-3.5 h-3.5 text-arterial" /> ANOMALY DETECTED
                </span>
              ) : (
                <span className="px-2.5 py-0.5 rounded bg-emerald-950/40 border border-emerald-500/40 text-emerald-400 flex items-center gap-1">
                  <CheckCircle className="w-3.5 h-3.5" /> NOMINAL ENVELOPE
                </span>
              )}
            </div>
          </div>

          {/* SVG Telemetry Visualizer */}
          <div className="w-full overflow-x-auto bg-void/80 p-2 rounded-card border border-white/5">
            <svg
              viewBox={`0 0 ${chartWidth} ${chartHeight}`}
              className="w-full h-56 overflow-visible"
            >
              {/* Nominal Range Band */}
              <rect
                x={padding}
                y={normalMaxY}
                width={chartWidth - padding * 2}
                height={normalMinY - normalMaxY}
                fill="rgba(56, 189, 248, 0.05)"
                stroke="rgba(56, 189, 248, 0.2)"
                strokeDasharray="4 4"
              />

              {/* Grid Lines */}
              <line
                x1={padding}
                y1={chartHeight - padding}
                x2={chartWidth - padding}
                y2={chartHeight - padding}
                stroke="#333"
                strokeWidth="1"
              />
              <line
                x1={padding}
                y1={padding}
                x2={padding}
                y2={chartHeight - padding}
                stroke="#333"
                strokeWidth="1"
              />

              {/* Timeseries Path */}
              <path
                d={pointsPath}
                fill="none"
                stroke={active.anomalous ? "#fe1e34" : "#38bdf8"}
                strokeWidth="2.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              />

              {/* Data Point Markers */}
              {active.history.map((val, idx) => {
                const cx = getX(idx);
                const cy = getY(val);
                const isOutOfRange =
                  val > active.normalRange[1] || val < active.normalRange[0];
                return (
                  <circle
                    key={idx}
                    cx={cx}
                    cy={cy}
                    r={isOutOfRange ? "5" : "3.5"}
                    fill={isOutOfRange ? "#fe1e34" : "#38bdf8"}
                    stroke="#000"
                    strokeWidth="1.5"
                  />
                );
              })}
            </svg>
          </div>

          <div className="flex items-center justify-between text-[11px] font-mono text-pebble px-2">
            <span>T - 80 min</span>
            <span>T - 40 min</span>
            <span className="text-bone font-semibold">T - 0 (Live Acquisition)</span>
          </div>
        </div>

        {/* Right: LSTM AE & Calibrator Status */}
        <div className="lg:col-span-4 space-y-4">
          {/* Architecture Card */}
          <div className="p-4 rounded-card bg-charcoal border border-white/10 space-y-3">
            <h3 className="text-xs uppercase font-mono tracking-wider text-ash flex items-center gap-1.5 border-b border-white/10 pb-2">
              <Cpu className="w-4 h-4 text-sky-400" />
              Model Architecture & Pipeline
            </h3>
            <div className="space-y-2 text-xs font-mono">
              <div className="flex justify-between py-1 border-b border-white/5">
                <span className="text-pebble">Network:</span>
                <span className="text-bone">PyTorch LSTM Autoencoder</span>
              </div>
              <div className="flex justify-between py-1 border-b border-white/5">
                <span className="text-pebble">Latent Bottleneck:</span>
                <span className="text-bone">16 units (64-dim window)</span>
              </div>
              <div className="flex justify-between py-1 border-b border-white/5">
                <span className="text-pebble">Calibration Cutoff:</span>
                <span className="text-amber-400">99.5th %ile (Empirical)</span>
              </div>
              <div className="flex justify-between py-1 border-b border-white/5">
                <span className="text-pebble">Persistence Filter:</span>
                <span className="text-emerald-400">3-of-4 Active Windows</span>
              </div>
            </div>
          </div>

          {/* Subsystem Health Attribution */}
          <div className="p-4 rounded-card bg-charcoal border border-white/10 space-y-3">
            <h3 className="text-xs uppercase font-mono tracking-wider text-ash border-b border-white/10 pb-2">
              Subsystem Residual Attribution
            </h3>
            <div className="space-y-2 text-xs font-mono">
              <div>
                <div className="flex justify-between text-[11px] mb-1">
                  <span className="text-bone">EPS Battery Thermal</span>
                  <span className="text-arterial font-bold">69.7%</span>
                </div>
                <div className="w-full h-1.5 bg-black rounded-full overflow-hidden">
                  <div className="h-full bg-arterial" style={{ width: "69.7%" }} />
                </div>
              </div>
              <div>
                <div className="flex justify-between text-[11px] mb-1">
                  <span className="text-bone">Power Bus Voltage</span>
                  <span className="text-sky-400">14.5%</span>
                </div>
                <div className="w-full h-1.5 bg-black rounded-full overflow-hidden">
                  <div className="h-full bg-sky-400" style={{ width: "14.5%" }} />
                </div>
              </div>
              <div>
                <div className="flex justify-between text-[11px] mb-1">
                  <span className="text-bone">ADCS Gyro Stability</span>
                  <span className="text-emerald-400">8.9%</span>
                </div>
                <div className="w-full h-1.5 bg-black rounded-full overflow-hidden">
                  <div className="h-full bg-emerald-400" style={{ width: "8.9%" }} />
                </div>
              </div>
              <div>
                <div className="flex justify-between text-[11px] mb-1">
                  <span className="text-bone">OBC Telecommand Bus</span>
                  <span className="text-ash">6.9%</span>
                </div>
                <div className="w-full h-1.5 bg-black rounded-full overflow-hidden">
                  <div className="h-full bg-ash" style={{ width: "6.9%" }} />
                </div>
              </div>
            </div>
          </div>

          {/* Operational Advisory */}
          <div className="p-4 rounded-card bg-charcoal border border-white/10 space-y-2">
            <div className="text-xs uppercase font-mono text-ash flex items-center gap-1.5">
              <Zap className="w-3.5 h-3.5 text-amber-400" />
              Flight Director Advisory
            </div>
            <p className="text-xs text-ash font-sans">
              EPS Battery cell temperature excursion detected (38.6°C). Cross-system safety rule active: Secondary Earth Observation optical payloads are automatically deferred until cell stabilizes below 32.0°C.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
