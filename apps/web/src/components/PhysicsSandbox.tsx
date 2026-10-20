"use client";

import React, { useState } from "react";
import {
  Cpu,
  Orbit,
  Layers,
  Sparkles,
  Sliders,
  Download,
  RotateCcw,
  CheckCircle2,
  Zap,
  Activity,
  Play,
} from "lucide-react";
import { SimulatedBadge } from "./SimulatedBadge";
import { playAudioCue } from "../lib/audio";
import { speakAdvisory } from "../lib/voice";

export function PhysicsSandbox() {
  // Telemetry physics controls
  const [tempDrift, setTempDrift] = useState<number>(4.2);
  const [noiseSigma, setNoiseSigma] = useState<number>(0.25);
  const [batteryResistance, setBatteryResistance] = useState<number>(18.5);

  // Debris conjunction physics controls
  const [missDist, setMissDist] = useState<number>(45.0);
  const [relVel, setRelVel] = useState<number>(12.4);
  const [sigmaAlongTrack, setSigmaAlongTrack] = useState<number>(250.0);

  // Disaster EO physics controls
  const [floodArea, setFloodArea] = useState<number>(380.0);
  const [backscatterDrop, setBackscatterDrop] = useState<number>(-4.2);

  // Live computed scores
  const [computedRisk, setComputedRisk] = useState<number>(90.0);
  const [computedPc, setComputedPc] = useState<number>(6.7e-4);
  const [isGenerated, setIsGenerated] = useState<boolean>(false);

  const handleSimulate = () => {
    playAudioCue("affirmative");
    // Analytical Foster approximation
    const sigX = 50.0;
    const sigY = sigmaAlongTrack;
    const exponent = -0.5 * Math.pow(missDist / sigX, 2);
    const pc = (25.0 / (2.0 * sigX * sigY)) * Math.exp(exponent);
    setComputedPc(pc);

    // Risk score calculation
    const rh = Math.min(1.0, 0.04 + (tempDrift / 10.0) * 0.7);
    const rd = pc >= 1e-4 ? 1.0 : Math.min(1.0, pc * 10000);
    const re = Math.min(1.0, (floodArea / 1000.0) * 0.85);

    let safetyRisk = 1.0 - (1.0 - rh) * (1.0 - rd);
    if (pc >= 1e-4) {
      safetyRisk = 1.0; // Hard override
    }
    const score = Math.min(100.0, (safetyRisk * 0.85 + re * 0.15) * 100);
    setComputedRisk(Math.round(score * 10) / 10);
    setIsGenerated(true);

    speakAdvisory(`Physics sandbox recomputed. Mission risk score is ${Math.round(score)}.`);
  };

  const handleReset = () => {
    playAudioCue("click");
    setTempDrift(4.2);
    setNoiseSigma(0.25);
    setBatteryResistance(18.5);
    setMissDist(45.0);
    setRelVel(12.4);
    setSigmaAlongTrack(250.0);
    setFloodArea(380.0);
    setBackscatterDrop(-4.2);
    setComputedRisk(90.0);
    setComputedPc(6.7e-4);
    setIsGenerated(false);
  };

  const exportJson = () => {
    playAudioCue("click");
    const payload = {
      timestamp: new Date().toISOString(),
      spacecraft: "SENTINEL-2A",
      telemetry: {
        eps_battery_temp_drift_c: tempDrift,
        sensor_noise_sigma: noiseSigma,
        battery_internal_resistance_mohm: batteryResistance,
      },
      orbital_conjunction: {
        secondary_name: "FENGYUN-1C-DEB-29834",
        miss_distance_m: missDist,
        relative_velocity_kms: relVel,
        along_track_sigma_m: sigmaAlongTrack,
        calculated_foster_pc: computedPc,
      },
      disaster_eo: {
        inundated_area_km2: floodArea,
        sar_backscatter_drop_db: backscatterDrop,
      },
      fused_mission_risk_score: computedRisk,
    };

    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `astra_guard_synthetic_scenario_${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="p-5 rounded-card bg-charcoal border border-white/10 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-white/10 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-sky-400" />
            <h2 className="text-base font-bold text-bone">
              Synthetic Data Studio & Orbital Physics Sandbox (F6)
            </h2>
            <SimulatedBadge />
          </div>
          <p className="text-xs text-ash font-mono mt-0.5">
            Parametric Ground Truth Generators for Spacecraft Bus, SGP4 Orbit Mechanics & SAR Remote Sensing
          </p>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-2">
          <button
            onClick={handleReset}
            className="px-3 py-1.5 rounded-card bg-smoke hover:bg-white/10 text-ash hover:text-bone text-xs font-mono flex items-center gap-1.5 transition-all"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Reset</span>
          </button>
          <button
            onClick={exportJson}
            className="px-3 py-1.5 rounded-card bg-smoke hover:bg-sky-500/20 text-sky-300 border border-sky-500/30 text-xs font-mono flex items-center gap-1.5 transition-all"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export Scenario JSON</span>
          </button>
        </div>
      </div>

      {/* Tri-Subsystem Sliders Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Module 1: Spacecraft Telemetry Physics */}
        <div className="p-4 rounded-card bg-void/80 border border-white/10 space-y-4">
          <div className="flex items-center gap-2 text-xs font-mono uppercase font-bold text-sky-300 border-b border-white/10 pb-2">
            <Cpu className="w-4 h-4 text-sky-400" />
            <span>1. Spacecraft Bus Telemetry</span>
          </div>

          {/* Temp Drift Slider */}
          <div className="space-y-1.5 font-mono text-xs">
            <div className="flex justify-between">
              <span className="text-pebble">Thermal Drift:</span>
              <span className="text-bone font-bold">+{tempDrift.toFixed(1)}°C</span>
            </div>
            <input
              type="range"
              min="0.0"
              max="15.0"
              step="0.5"
              value={tempDrift}
              onChange={(e) => setTempDrift(parseFloat(e.target.value))}
              className="w-full accent-sky-400 cursor-pointer"
            />
          </div>

          {/* Noise Sigma Slider */}
          <div className="space-y-1.5 font-mono text-xs">
            <div className="flex justify-between">
              <span className="text-pebble">Sensor Noise (&sigma;):</span>
              <span className="text-bone font-bold">{noiseSigma.toFixed(2)}</span>
            </div>
            <input
              type="range"
              min="0.05"
              max="1.0"
              step="0.05"
              value={noiseSigma}
              onChange={(e) => setNoiseSigma(parseFloat(e.target.value))}
              className="w-full accent-sky-400 cursor-pointer"
            />
          </div>

          {/* Battery Resistance */}
          <div className="space-y-1.5 font-mono text-xs">
            <div className="flex justify-between">
              <span className="text-pebble">Internal Resistance:</span>
              <span className="text-bone font-bold">{batteryResistance.toFixed(1)} m&Omega;</span>
            </div>
            <input
              type="range"
              min="10.0"
              max="50.0"
              step="1.0"
              value={batteryResistance}
              onChange={(e) => setBatteryResistance(parseFloat(e.target.value))}
              className="w-full accent-sky-400 cursor-pointer"
            />
          </div>
        </div>

        {/* Module 2: Orbital Debris Physics */}
        <div className="p-4 rounded-card bg-void/80 border border-white/10 space-y-4">
          <div className="flex items-center gap-2 text-xs font-mono uppercase font-bold text-rose-300 border-b border-white/10 pb-2">
            <Orbit className="w-4 h-4 text-rose-400" />
            <span>2. Orbital Conjunction Mechanics</span>
          </div>

          {/* Miss Distance */}
          <div className="space-y-1.5 font-mono text-xs">
            <div className="flex justify-between">
              <span className="text-pebble">Miss Distance:</span>
              <span className="text-bone font-bold">{missDist.toFixed(1)} m</span>
            </div>
            <input
              type="range"
              min="10.0"
              max="500.0"
              step="5.0"
              value={missDist}
              onChange={(e) => setMissDist(parseFloat(e.target.value))}
              className="w-full accent-rose-500 cursor-pointer"
            />
          </div>

          {/* Relative Velocity */}
          <div className="space-y-1.5 font-mono text-xs">
            <div className="flex justify-between">
              <span className="text-pebble">Rel Velocity:</span>
              <span className="text-bone font-bold">{relVel.toFixed(1)} km/s</span>
            </div>
            <input
              type="range"
              min="2.0"
              max="16.0"
              step="0.2"
              value={relVel}
              onChange={(e) => setRelVel(parseFloat(e.target.value))}
              className="w-full accent-rose-500 cursor-pointer"
            />
          </div>

          {/* Along-track Covariance */}
          <div className="space-y-1.5 font-mono text-xs">
            <div className="flex justify-between">
              <span className="text-pebble">In-Track Uncertainty (&sigma;_t):</span>
              <span className="text-bone font-bold">{sigmaAlongTrack.toFixed(0)} m</span>
            </div>
            <input
              type="range"
              min="100.0"
              max="600.0"
              step="25.0"
              value={sigmaAlongTrack}
              onChange={(e) => setSigmaAlongTrack(parseFloat(e.target.value))}
              className="w-full accent-rose-500 cursor-pointer"
            />
          </div>
        </div>

        {/* Module 3: Disaster EO Physics */}
        <div className="p-4 rounded-card bg-void/80 border border-white/10 space-y-4">
          <div className="flex items-center gap-2 text-xs font-mono uppercase font-bold text-amber-300 border-b border-white/10 pb-2">
            <Layers className="w-4 h-4 text-amber-400" />
            <span>3. Earth Observation Remote Sensing</span>
          </div>

          {/* Inundated Area */}
          <div className="space-y-1.5 font-mono text-xs">
            <div className="flex justify-between">
              <span className="text-pebble">Flood / Fire Extent:</span>
              <span className="text-bone font-bold">{floodArea.toFixed(0)} km²</span>
            </div>
            <input
              type="range"
              min="50.0"
              max="1000.0"
              step="25.0"
              value={floodArea}
              onChange={(e) => setFloodArea(parseFloat(e.target.value))}
              className="w-full accent-amber-400 cursor-pointer"
            />
          </div>

          {/* SAR Backscatter Drop */}
          <div className="space-y-1.5 font-mono text-xs">
            <div className="flex justify-between">
              <span className="text-pebble">Backscatter Drop (&Delta;&sigma;⁰):</span>
              <span className="text-bone font-bold">{backscatterDrop.toFixed(1)} dB</span>
            </div>
            <input
              type="range"
              min="-8.0"
              max="-1.0"
              step="0.2"
              value={backscatterDrop}
              onChange={(e) => setBackscatterDrop(parseFloat(e.target.value))}
              className="w-full accent-amber-400 cursor-pointer"
            />
          </div>

          {/* Sensor GSD */}
          <div className="p-2.5 rounded bg-smoke text-[11px] font-mono text-pebble flex justify-between">
            <span>Spatial Resolution:</span>
            <span className="text-bone font-semibold">10m GSD (Sentinel-1/2)</span>
          </div>
        </div>
      </div>

      {/* Recalculate CTA & Output Banner */}
      <div className="p-4 rounded-card bg-smoke border border-sky-500/30 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="space-y-1">
          <div className="text-xs font-mono uppercase text-sky-300 font-bold flex items-center gap-2">
            <Activity className="w-4 h-4 text-sky-400" />
            <span>Fused Mission Risk Output (Real-Time Physics Evaluation)</span>
          </div>
          <div className="flex items-center gap-6 text-xs font-mono text-pebble">
            <div>
              <span>Mission Risk Score: </span>
              <strong className={computedRisk >= 75 ? "text-arterial text-sm" : "text-amber-400 text-sm"}>
                {computedRisk.toFixed(1)} / 100
              </strong>
            </div>
            <div>
              <span>Foster Pc: </span>
              <strong className={computedPc >= 1e-4 ? "text-arterial" : "text-bone"}>
                {computedPc.toExponential(2)}
              </strong>
            </div>
          </div>
        </div>

        <button
          onClick={handleSimulate}
          className="px-5 py-2.5 rounded bg-sky-500 hover:bg-sky-400 text-void font-bold text-xs font-mono flex items-center gap-2 shadow-glass transition-all"
        >
          <Play className="w-4 h-4 fill-current" />
          <span>Execute Physics Simulation</span>
        </button>
      </div>
    </div>
  );
}
