"use client";

import React, { useState, useEffect, useCallback } from "react";
import {
  Rocket,
  ShieldCheck,
  Fuel,
  ArrowRight,
  TrendingDown,
  AlertTriangle,
  RotateCcw,
  CheckCircle2,
  Sliders,
  Send,
  Zap,
} from "lucide-react";
import { ManeuverRequest, ManeuverResponse } from "../lib/types";
import { simulateManeuver } from "../lib/api";
import { StatusBadge } from "./StatusBadge";
import { SimulatedBadge } from "./SimulatedBadge";
import { playAudioCue } from "../lib/audio";
import { speakAdvisory } from "../lib/voice";

interface ManeuverSimulatorProps {
  conjunctionId?: string;
  secondaryName?: string;
  initialMissM?: number;
  relativeVelocityKms?: number;
  onManeuverRequisition?: (req: ManeuverResponse) => void;
}

export function ManeuverSimulator({
  conjunctionId = "CONJ-29834",
  secondaryName = "FENGYUN-1C-DEB-29834",
  initialMissM = 315.4,
  relativeVelocityKms = 12.42,
  onManeuverRequisition,
}: ManeuverSimulatorProps) {
  const [direction, setDirection] = useState<
    "prograde" | "retrograde" | "radial_out" | "radial_in" | "out_of_plane"
  >("prograde");
  const [deltaV, setDeltaV] = useState<number>(0.35);
  const [leadTime, setLeadTime] = useState<number>(8.0);
  const [simResult, setSimResult] = useState<ManeuverResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [requisitionSubmitted, setRequisitionSubmitted] = useState<boolean>(false);

  const runSimulation = useCallback(
    async (dir = direction, dv = deltaV, lt = leadTime) => {
      setLoading(true);
      try {
        const req: ManeuverRequest = {
          conjunction_id: conjunctionId,
          secondary_name: secondaryName,
          initial_miss_m: initialMissM,
          relative_velocity_kms: relativeVelocityKms,
          delta_v_ms: dv,
          direction: dir,
          lead_time_hours: lt,
        };
        const res = await simulateManeuver(req);
        setSimResult(res);
      } catch (err) {
        console.error("Maneuver simulation error:", err);
      } finally {
        setLoading(false);
      }
    },
    [conjunctionId, secondaryName, initialMissM, relativeVelocityKms, direction, deltaV, leadTime]
  );

  useEffect(() => {
    runSimulation();
  }, [runSimulation]);

  const handleApplyPreset = (dir: typeof direction, dv: number, lt: number) => {
    playAudioCue("click");
    setDirection(dir);
    setDeltaV(dv);
    setLeadTime(lt);
    runSimulation(dir, dv, lt);
  };

  const handleRequisition = () => {
    if (!simResult) return;
    playAudioCue("affirmative");
    speakAdvisory(`Collision avoidance maneuver requisition submitted for ${secondaryName}. Expected miss distance ${simResult.simulated.miss_distance_m.toFixed(0)} meters.`);
    setRequisitionSubmitted(true);
    if (onManeuverRequisition) {
      onManeuverRequisition(simResult);
    }
  };

  const orig = simResult?.original;
  const sim = simResult?.simulated;

  return (
    <div className="p-5 rounded-card bg-charcoal border border-white/10 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-white/10 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <Rocket className="w-5 h-5 text-sky-400" />
            <h2 className="text-base font-bold text-bone">
              Collision Avoidance Maneuver (CAM) What-If Simulator
            </h2>
            <SimulatedBadge />
          </div>
          <p className="text-xs text-ash font-mono mt-0.5">
            Hill-Clohessy-Wiltshire (HCW) Relative Motion Model & Tsiolkovsky Hydrazine Propellant Budget
          </p>
        </div>

        {/* Quick Presets */}
        <div className="flex items-center gap-1.5 flex-wrap">
          <span className="text-[10px] uppercase font-mono text-pebble mr-1">Presets:</span>
          <button
            onClick={() => handleApplyPreset("prograde", 0.15, 12.0)}
            className="px-2.5 py-1 text-[11px] font-mono rounded bg-smoke hover:bg-white/10 text-ash hover:text-bone transition-all"
          >
            Conserve Fuel (0.15 m/s)
          </button>
          <button
            onClick={() => handleApplyPreset("prograde", 0.35, 8.0)}
            className="px-2.5 py-1 text-[11px] font-mono rounded bg-smoke hover:bg-sky-500/20 text-sky-300 border border-sky-500/30 transition-all font-semibold"
          >
            Recommended CAM (0.35 m/s)
          </button>
          <button
            onClick={() => handleApplyPreset("retrograde", 0.8, 4.0)}
            className="px-2.5 py-1 text-[11px] font-mono rounded bg-smoke hover:bg-white/10 text-ash hover:text-bone transition-all"
          >
            Emergency Burn (0.80 m/s)
          </button>
        </div>
      </div>

      {/* Control Sliders & Direction Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Thrust Vector Direction */}
        <div className="lg:col-span-5 space-y-3">
          <label className="text-xs font-mono uppercase text-ash flex items-center justify-between">
            <span className="flex items-center gap-1.5">
              <Sliders className="w-3.5 h-3.5 text-sky-400" />
              Impulse Thrust Vector
            </span>
            <span className="text-sky-300 font-semibold">{direction.toUpperCase()}</span>
          </label>

          <div className="grid grid-cols-2 gap-2">
            {[
              { id: "prograde", label: "Prograde (+T)", desc: "Along-track lead phasing" },
              { id: "retrograde", label: "Retrograde (-T)", desc: "Along-track lag phasing" },
              { id: "radial_out", label: "Radial Out (+R)", desc: "Altitude boost pulse" },
              { id: "radial_in", label: "Radial In (-R)", desc: "Altitude decrease pulse" },
            ].map((btn) => (
              <button
                key={btn.id}
                onClick={() => {
                  playAudioCue("click");
                  setDirection(btn.id as typeof direction);
                  runSimulation(btn.id as typeof direction, deltaV, leadTime);
                }}
                className={`p-2.5 rounded-card text-left transition-all border ${
                  direction === btn.id
                    ? "bg-sky-500/15 border-sky-400/80 text-bone shadow-glass"
                    : "bg-smoke/60 border-white/5 hover:border-white/20 text-ash"
                }`}
              >
                <div className="font-mono text-xs font-bold text-bone">{btn.label}</div>
                <div className="text-[10px] text-pebble mt-0.5">{btn.desc}</div>
              </button>
            ))}
          </div>

          <button
            onClick={() => {
              playAudioCue("click");
              setDirection("out_of_plane");
              runSimulation("out_of_plane", deltaV, leadTime);
            }}
            className={`w-full p-2.5 rounded-card text-left transition-all border ${
              direction === "out_of_plane"
                ? "bg-sky-500/15 border-sky-400/80 text-bone shadow-glass"
                : "bg-smoke/60 border-white/5 hover:border-white/20 text-ash"
            }`}
          >
            <div className="flex justify-between items-center font-mono text-xs font-bold text-bone">
              <span>Cross-Track / Normal (±N)</span>
              <span className="text-[10px] text-pebble">Orbital Plane Rotation</span>
            </div>
          </button>
        </div>

        {/* Sliders: Delta V & Lead Time */}
        <div className="lg:col-span-7 space-y-5 bg-smoke/40 p-4 rounded-card border border-white/5">
          {/* Delta V Slider */}
          <div className="space-y-2">
            <div className="flex justify-between items-center text-xs font-mono">
              <span className="text-ash flex items-center gap-1.5">
                <Zap className="w-3.5 h-3.5 text-amber-400" />
                Burn Magnitude (&Delta;V):
              </span>
              <span className="text-bone font-bold text-sm bg-void px-2 py-0.5 rounded border border-white/10">
                {deltaV.toFixed(2)} m/s
              </span>
            </div>
            <input
              type="range"
              min="0.05"
              max="1.50"
              step="0.05"
              value={deltaV}
              onChange={(e) => {
                const val = parseFloat(e.target.value);
                setDeltaV(val);
                runSimulation(direction, val, leadTime);
              }}
              className="w-full accent-sky-400 cursor-pointer"
            />
            <div className="flex justify-between text-[10px] font-mono text-pebble">
              <span>0.05 m/s (Micro-burn)</span>
              <span>0.35 m/s (Nominal CAM)</span>
              <span>1.50 m/s (Max Reserve)</span>
            </div>
          </div>

          {/* Lead Time Slider */}
          <div className="space-y-2">
            <div className="flex justify-between items-center text-xs font-mono">
              <span className="text-ash flex items-center gap-1.5">
                <RotateCcw className="w-3.5 h-3.5 text-emerald-400" />
                Execution Lead Time (Prior to TCA):
              </span>
              <span className="text-bone font-bold text-sm bg-void px-2 py-0.5 rounded border border-white/10">
                T - {leadTime.toFixed(1)} Hours
              </span>
            </div>
            <input
              type="range"
              min="1.0"
              max="24.0"
              step="0.5"
              value={leadTime}
              onChange={(e) => {
                const val = parseFloat(e.target.value);
                setLeadTime(val);
                runSimulation(direction, deltaV, val);
              }}
              className="w-full accent-emerald-400 cursor-pointer"
            />
            <div className="flex justify-between text-[10px] font-mono text-pebble">
              <span>1.0h (Late evasion)</span>
              <span>8.0h (Standard orbit phasing)</span>
              <span>24.0h (Max propagation)</span>
            </div>
          </div>
        </div>
      </div>

      {/* Results Comparison Grid */}
      {sim && orig && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Miss Distance Comparison */}
            <div className="p-4 rounded-card bg-void/80 border border-white/10 space-y-2">
              <div className="text-[11px] font-mono text-pebble uppercase flex items-center justify-between">
                <span>Miss Distance at TCA</span>
                <span className="text-emerald-400 font-semibold">
                  +{((sim.miss_distance_m - orig.miss_distance_m) / 1000).toFixed(2)} km
                </span>
              </div>
              <div className="flex items-center gap-3">
                <div className="text-sm font-mono text-arterial line-through">
                  {orig.miss_distance_m < 1000
                    ? `${orig.miss_distance_m.toFixed(1)} m`
                    : `${(orig.miss_distance_m / 1000).toFixed(2)} km`}
                </div>
                <ArrowRight className="w-4 h-4 text-emerald-400" />
                <div className="text-lg font-mono font-bold text-emerald-400">
                  {sim.miss_distance_m < 1000
                    ? `${sim.miss_distance_m.toFixed(1)} m`
                    : `${(sim.miss_distance_m / 1000).toFixed(2)} km`}
                </div>
              </div>
              <div className="text-[10px] font-mono text-pebble">
                Encounter plane clearance: {sim.miss_distance_m > 2000 ? "SAFE (>2 km)" : "CAUTION"}
              </div>
            </div>

            {/* Collision Probability Pc */}
            <div className="p-4 rounded-card bg-void/80 border border-white/10 space-y-2">
              <div className="text-[11px] font-mono text-pebble uppercase flex items-center justify-between">
                <span>Foster 2-D Probability (Pc)</span>
                <StatusBadge level={sim.risk_class} size="sm" />
              </div>
              <div className="flex items-center gap-3">
                <div className="text-sm font-mono text-arterial font-bold line-through">
                  {orig.pc.toExponential(2)}
                </div>
                <ArrowRight className="w-4 h-4 text-emerald-400" />
                <div className="text-lg font-mono font-bold text-emerald-400">
                  {sim.pc < 1e-12 ? "< 1.0e-12" : sim.pc.toExponential(2)}
                </div>
              </div>
              <div className="flex items-center gap-1.5 text-[10px] font-mono text-emerald-300">
                <TrendingDown className="w-3 h-3" />
                <span>
                  {sim.pc_reduction_factor && sim.pc_reduction_factor > 1
                    ? `${sim.pc_reduction_factor.toLocaleString()}x Risk Reduction`
                    : "Zero Residual Risk"}
                </span>
              </div>
            </div>

            {/* Hydrazine Propellant Budget */}
            <div className="p-4 rounded-card bg-void/80 border border-white/10 space-y-2">
              <div className="text-[11px] font-mono text-pebble uppercase flex items-center justify-between">
                <span>Hydrazine Propellant Cost</span>
                <Fuel className="w-3.5 h-3.5 text-amber-400" />
              </div>
              <div className="flex items-baseline gap-2">
                <span className="text-lg font-mono font-bold text-bone">
                  {sim.fuel_consumed_kg ? sim.fuel_consumed_kg.toFixed(3) : "0.000"} kg
                </span>
                <span className="text-xs font-mono text-pebble">
                  / 120.0 kg onboard ({sim.fuel_mass_percent?.toFixed(2)}%)
                </span>
              </div>
              <div className="w-full bg-charcoal rounded-full h-1.5 overflow-hidden">
                <div
                  className="bg-sky-400 h-full rounded-full transition-all"
                  style={{ width: `${Math.min(100, (sim.fuel_mass_percent || 0.1) * 20)}%` }}
                />
              </div>
              <div className="text-[10px] font-mono text-pebble flex justify-between">
                <span>Isp: 220s Monoprop</span>
                <span>Dry Mass: 1,140 kg</span>
              </div>
            </div>
          </div>

          {/* Spatial Vector Breakdown */}
          <div className="p-3.5 rounded bg-smoke/40 border border-white/5 flex flex-wrap items-center justify-between gap-4 text-xs font-mono">
            <div className="flex items-center gap-2">
              <span className="text-pebble">In-Track Phasing (&Delta;T):</span>
              <span className="text-bone font-semibold">
                {sim.delta_in_track_m ? `${sim.delta_in_track_m.toFixed(1)} m` : "0.0 m"}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-pebble">Radial Separation (&Delta;R):</span>
              <span className="text-bone font-semibold">
                {sim.delta_radial_m ? `${sim.delta_radial_m.toFixed(1)} m` : "0.0 m"}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-pebble">Cross-Track Plane (&Delta;N):</span>
              <span className="text-bone font-semibold">
                {sim.delta_normal_m ? `${sim.delta_normal_m.toFixed(1)} m` : "0.0 m"}
              </span>
            </div>
            <div className="flex items-center gap-2 text-sky-400">
              <span className="text-pebble">Total Offset Vector:</span>
              <span className="font-bold">
                {sim.displacement_vector_m ? `${sim.displacement_vector_m.toFixed(1)} m` : "0.0 m"}
              </span>
            </div>
          </div>

          {/* Human-in-the-Loop Flight Safety Directive & Action Banner */}
          <div className="p-4 rounded-card bg-smoke border border-sky-500/30 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div className="space-y-1">
              <div className="flex items-center gap-2 text-xs font-mono text-sky-300 font-bold uppercase">
                <ShieldCheck className="w-4 h-4 text-sky-400" />
                <span>Flight Safety Advisory Directive (Advisory Only)</span>
              </div>
              <p className="text-xs text-ash max-w-xl">
                {simResult?.advisory_directive ||
                  "Autonomous thruster commanding is disabled per rules.md §6. Submit formal maneuver requisition for Flight Dynamics and Space Safety Team validation."}
              </p>
            </div>

            <div className="flex items-center gap-3">
              {requisitionSubmitted ? (
                <div className="flex items-center gap-2 px-4 py-2 rounded bg-emerald-500/20 border border-emerald-500/40 text-emerald-300 text-xs font-mono">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  <span>Requisition Dispatched to Flight Dynamics</span>
                </div>
              ) : (
                <button
                  onClick={handleRequisition}
                  className="px-4 py-2 rounded bg-sky-500 hover:bg-sky-400 text-void font-bold text-xs font-mono flex items-center gap-2 shadow-glass transition-all"
                >
                  <Send className="w-3.5 h-3.5" />
                  <span>Submit Maneuver Requisition</span>
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
