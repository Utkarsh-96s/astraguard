"use client";

import React, { useState } from "react";
import {
  Orbit,
  Compass,
  Crosshair,
  ShieldAlert,
  Clock,
  Layers,
  Rocket,
  Globe,
  Sliders,
  Sparkles,
} from "lucide-react";
import { SimulatedBadge } from "../../components/SimulatedBadge";
import { StatusBadge } from "../../components/StatusBadge";
import { ManeuverSimulator } from "../../components/ManeuverSimulator";
import { UncertaintyLab } from "../../components/UncertaintyLab";
import { OrbitTwin3D } from "../../components/OrbitTwin3D";
import { playAudioCue } from "../../lib/audio";

export default function DebrisPage() {
  const [selectedConjunction, setSelectedConjunction] = useState<string>("CONJ-29834");
  const [activeTab, setActiveTab] = useState<"twin" | "simulator" | "uncertainty" | "overview">("twin");

  const conjunctions = [
    {
      id: "CONJ-29834",
      secondaryName: "FENGYUN-1C-DEB-29834",
      noradId: 29834,
      tcaHours: 14.2,
      tcaIso: "2026-10-20 14:45:00 UTC",
      missDistanceM: 315.4,
      relativeVelocityKms: 12.42,
      pc: 2.4e-4,
      riskClass: "CRITICAL",
      cObsB: 28.5,
      cObsT: 14.2,
      cObsN: 9.8,
    },
    {
      id: "CONJ-40112",
      secondaryName: "COSMOS-2251-DEB-40112",
      noradId: 40112,
      tcaHours: 28.5,
      tcaIso: "2026-10-21 05:15:00 UTC",
      missDistanceM: 4820.0,
      relativeVelocityKms: 9.85,
      pc: 1.1e-6,
      riskClass: "LOW",
      cObsB: 120.4,
      cObsT: 45.1,
      cObsN: 32.7,
    },
    {
      id: "CONJ-33441",
      secondaryName: "IRIDIUM-33-DEB-33441",
      noradId: 33441,
      tcaHours: 42.1,
      tcaIso: "2026-10-21 18:50:00 UTC",
      missDistanceM: 7310.0,
      relativeVelocityKms: 14.15,
      pc: 4.8e-7,
      riskClass: "LOW",
      cObsB: 240.1,
      cObsT: 98.2,
      cObsN: 54.1,
    },
  ];

  const active = conjunctions.find((c) => c.id === selectedConjunction) || conjunctions[0];

  return (
    <div className="space-y-6">
      {/* Title Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-4 rounded-card bg-charcoal border border-white/10">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold tracking-tight text-bone flex items-center gap-2">
              <Orbit className="w-5 h-5 text-rose-400" />
              Debris Conjunction Risk & Orbital Screening
            </h1>
            <SimulatedBadge />
          </div>
          <p className="text-xs text-ash font-mono mt-0.5">
            SGP4 Analytical Propagator + Foster 2-D B-Plane Collision Probability Engine
          </p>
        </div>

        {/* Screening Grade Disclaimer */}
        <div className="px-3 py-1.5 rounded-nav bg-smoke border border-amber-500/30 text-xs font-mono text-amber-300 flex items-center gap-1.5">
          <Compass className="w-3.5 h-3.5" />
          <span>Screening-Grade (Assumed Covariance)</span>
        </div>
      </div>

      {/* Navigation Sub-Tabs */}
      <div className="flex items-center gap-2 border-b border-white/10 pb-2 overflow-x-auto">
        <button
          onClick={() => {
            playAudioCue("click");
            setActiveTab("twin");
          }}
          className={`flex items-center gap-2 px-3.5 py-1.5 rounded-nav text-xs font-mono transition-all whitespace-nowrap ${
            activeTab === "twin"
              ? "bg-sky-500/20 text-sky-300 border border-sky-400/50 shadow-glass font-bold"
              : "text-ash hover:text-bone hover:bg-smoke"
          }`}
        >
          <Globe className="w-3.5 h-3.5" />
          <span>3D Orbit Digital Twin (F1)</span>
        </button>

        <button
          onClick={() => {
            playAudioCue("click");
            setActiveTab("simulator");
          }}
          className={`flex items-center gap-2 px-3.5 py-1.5 rounded-nav text-xs font-mono transition-all whitespace-nowrap ${
            activeTab === "simulator"
              ? "bg-sky-500/20 text-sky-300 border border-sky-400/50 shadow-glass font-bold"
              : "text-ash hover:text-bone hover:bg-smoke"
          }`}
        >
          <Rocket className="w-3.5 h-3.5" />
          <span>CAM What-If Simulator (F2)</span>
        </button>

        <button
          onClick={() => {
            playAudioCue("click");
            setActiveTab("uncertainty");
          }}
          className={`flex items-center gap-2 px-3.5 py-1.5 rounded-nav text-xs font-mono transition-all whitespace-nowrap ${
            activeTab === "uncertainty"
              ? "bg-sky-500/20 text-sky-300 border border-sky-400/50 shadow-glass font-bold"
              : "text-ash hover:text-bone hover:bg-smoke"
          }`}
        >
          <Layers className="w-3.5 h-3.5" />
          <span>B-Plane Uncertainty Lab (F3)</span>
        </button>

        <button
          onClick={() => {
            playAudioCue("click");
            setActiveTab("overview");
          }}
          className={`flex items-center gap-2 px-3.5 py-1.5 rounded-nav text-xs font-mono transition-all whitespace-nowrap ${
            activeTab === "overview"
              ? "bg-sky-500/20 text-sky-300 border border-sky-400/50 shadow-glass font-bold"
              : "text-ash hover:text-bone hover:bg-smoke"
          }`}
        >
          <Sliders className="w-3.5 h-3.5" />
          <span>All Mission Diagnostics</span>
        </button>
      </div>

      {/* Tab 1: 3D Orbit Digital Twin */}
      {(activeTab === "twin" || activeTab === "overview") && (
        <OrbitTwin3D
          assetId="SENTINEL-2A"
          selectedConjunctionName={active.secondaryName}
        />
      )}

      {/* Tab 2: Maneuver What-If Simulator */}
      {(activeTab === "simulator" || activeTab === "overview") && (
        <ManeuverSimulator
          conjunctionId={active.id}
          secondaryName={active.secondaryName}
          initialMissM={active.missDistanceM}
          relativeVelocityKms={active.relativeVelocityKms}
        />
      )}

      {/* Tab 3: B-Plane Uncertainty Lab */}
      {(activeTab === "uncertainty" || activeTab === "overview") && (
        <UncertaintyLab
          conjunctionId={active.id}
          secondaryName={active.secondaryName}
          initialMissM={active.missDistanceM}
        />
      )}

      {/* Conjunction Assessment Table & Selected Diagnostics */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Conjunction Screening List */}
        <div className="lg:col-span-7 p-5 rounded-card bg-charcoal border border-white/10 space-y-4">
          <div className="flex items-center justify-between border-b border-white/10 pb-2">
            <h2 className="text-xs font-mono uppercase tracking-wider text-ash">
              Close Approach Conjunctions ({conjunctions.length} Monitored)
            </h2>
            <span className="text-[10px] text-pebble font-mono">TCA Window: 72 Hours</span>
          </div>

          <div className="space-y-2">
            {conjunctions.map((c) => {
              const isSelected = selectedConjunction === c.id;
              return (
                <div
                  key={c.id}
                  onClick={() => {
                    playAudioCue("click");
                    setSelectedConjunction(c.id);
                  }}
                  className={`p-3.5 rounded-card cursor-pointer transition-all border ${
                    isSelected
                      ? "bg-smoke border-rose-500/80 shadow-glass"
                      : "bg-void/60 border-white/5 hover:border-white/15"
                  }`}
                >
                  <div className="flex items-center justify-between text-xs">
                    <div className="flex items-center gap-2">
                      <StatusBadge level={c.riskClass} size="sm" />
                      <span className="font-mono text-bone font-bold">{c.secondaryName}</span>
                    </div>
                    <span className="font-mono text-ash text-[11px]">NORAD #{c.noradId}</span>
                  </div>

                  <div className="mt-2 grid grid-cols-3 gap-2 text-xs font-mono text-pebble">
                    <div>
                      <div className="text-[10px] uppercase">TCA</div>
                      <div className="text-bone font-semibold">+{c.tcaHours}h</div>
                    </div>
                    <div>
                      <div className="text-[10px] uppercase">Miss Distance</div>
                      <div
                        className={`font-semibold ${c.missDistanceM < 1000 ? "text-arterial" : "text-bone"}`}
                      >
                        {c.missDistanceM < 1000
                          ? `${c.missDistanceM.toFixed(1)} m`
                          : `${(c.missDistanceM / 1000).toFixed(2)} km`}
                      </div>
                    </div>
                    <div>
                      <div className="text-[10px] uppercase">Collision Pc</div>
                      <div
                        className={`font-semibold ${c.pc >= 1e-4 ? "text-arterial font-bold" : "text-bone"}`}
                      >
                        {c.pc.toExponential(2)}
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right: Selected Encounter Diagnostics & CAM Advisory */}
        <div className="lg:col-span-5 space-y-4">
          {/* Foster 2-D B-Plane Card */}
          <div className="p-4 rounded-card bg-charcoal border border-white/10 space-y-3">
            <h3 className="text-xs uppercase font-mono tracking-wider text-ash border-b border-white/10 pb-2 flex items-center justify-between">
              <span>B-Plane Geometry & Pc Details</span>
              <StatusBadge level={active.riskClass} size="sm" />
            </h3>

            <div className="space-y-2 text-xs font-mono">
              <div className="flex justify-between py-1 border-b border-white/5">
                <span className="text-pebble">Relative Velocity:</span>
                <span className="text-bone">{active.relativeVelocityKms.toFixed(2)} km/s</span>
              </div>
              <div className="flex justify-between py-1 border-b border-white/5">
                <span className="text-pebble">Miss Distance:</span>
                <span className="text-bone font-bold">{active.missDistanceM.toFixed(1)} m</span>
              </div>
              <div className="flex justify-between py-1 border-b border-white/5">
                <span className="text-pebble">Foster 2-D Probability:</span>
                <span
                  className={`font-bold ${active.pc >= 1e-4 ? "text-arterial text-sm" : "text-bone"}`}
                >
                  {active.pc.toExponential(2)}
                </span>
              </div>
              <div className="flex justify-between py-1 border-b border-white/5">
                <span className="text-pebble">Safety Threshold:</span>
                <span className="text-ash font-mono">1.00e-04 (Hard Override)</span>
              </div>
            </div>
          </div>

          {/* SGP4 Propagation Drift Horizon */}
          <div className="p-4 rounded-card bg-charcoal border border-white/10 space-y-3">
            <h3 className="text-xs uppercase font-mono tracking-wider text-ash border-b border-white/10 pb-2 flex items-center gap-1.5">
              <Clock className="w-3.5 h-3.5 text-sky-400" />
              SGP4 Error Horizon (Measured)
            </h3>
            <div className="grid grid-cols-3 gap-2 text-center text-xs font-mono">
              <div className="p-2 rounded bg-smoke">
                <div className="text-[10px] text-pebble">24 Hours</div>
                <div className="text-bone font-semibold">3.398 km</div>
              </div>
              <div className="p-2 rounded bg-smoke">
                <div className="text-[10px] text-pebble">48 Hours</div>
                <div className="text-bone font-semibold">7.925 km</div>
              </div>
              <div className="p-2 rounded bg-smoke">
                <div className="text-[10px] text-pebble">72 Hours</div>
                <div className="text-bone font-semibold">13.144 km</div>
              </div>
            </div>
          </div>

          {/* Collision Avoidance Maneuver (CAM) Advisory Card */}
          <div className="p-4 rounded-card bg-charcoal border border-arterial/60 space-y-3">
            <div className="flex items-center gap-2 text-xs font-mono text-red-300 uppercase font-semibold">
              <ShieldAlert className="w-4 h-4 text-arterial" />
              CAM Advisory (Human Approval Required)
            </div>
            <p className="text-xs text-ash font-sans">
              Calculated Pc ({active.pc.toExponential(2)}) breaches flight safety rules. Recommended
              maneuver window: T - 8.0h using radial thrust pulse (+0.12 m/s &Delta;V).
            </p>
            <div className="p-2.5 rounded bg-void/80 border border-white/5 text-[11px] font-mono text-pebble">
              <strong>Advisory Directive:</strong> Automated thruster firing is strictly disabled.
              Submit formal maneuver requisition to Flight Dynamics team.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
