"use client";

import React, { useState } from "react";
import {
  Orbit,
  AlertTriangle,
  Compass,
  Crosshair,
  ShieldAlert,
  ArrowUpRight,
  Clock,
  Layers,
} from "lucide-react";
import { SimulatedBadge } from "../../components/SimulatedBadge";
import { StatusBadge } from "../../components/StatusBadge";

export default function DebrisPage() {
  const [selectedConjunction, setSelectedConjunction] = useState<string>("CONJ-29834");

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

      {/* 2D Orbital Ground Track Map Visualization */}
      <div className="p-5 rounded-card bg-charcoal border border-white/10 space-y-3">
        <div className="flex items-center justify-between border-b border-white/10 pb-2">
          <div className="flex items-center gap-2 text-xs font-mono text-ash uppercase tracking-wider">
            <Crosshair className="w-4 h-4 text-rose-400" />
            Equirectangular Orbit Ground Track & Close Encounter Waypoint
          </div>
          <div className="flex items-center gap-3 text-[11px] font-mono">
            <span className="flex items-center gap-1 text-sky-400">
              <span className="w-2 h-0.5 bg-sky-400 inline-block" /> SENTINEL-2A (SSO)
            </span>
            <span className="flex items-center gap-1 text-arterial">
              <span className="w-2 h-0.5 bg-arterial inline-block" /> {active.secondaryName}
            </span>
          </div>
        </div>

        {/* SVG Orbital Ground Track Visualizer */}
        <div className="relative w-full aspect-[2/1] max-h-[300px] bg-void rounded-card border border-white/5 overflow-hidden flex items-center justify-center">
          <svg viewBox="0 0 720 360" className="w-full h-full">
            {/* World Grid Lines */}
            <defs>
              <pattern id="grid" width="60" height="60" patternUnits="userSpaceOnUse">
                <path d="M 60 0 L 0 0 0 60" fill="none" stroke="#171617" strokeWidth="1" />
              </pattern>
            </defs>
            <rect width="720" height="360" fill="url(#grid)" />

            {/* Equator & Prime Meridian */}
            <line x1="0" y1="180" x2="720" y2="180" stroke="#222" strokeWidth="1" />
            <line x1="360" y1="0" x2="360" y2="360" stroke="#222" strokeWidth="1" />

            {/* Simplified Continental Outlines (Abstracted for dark aesthetic) */}
            <path
              d="M 120 100 Q 180 80 220 110 T 260 160 T 220 240 T 160 260 T 120 180 Z"
              fill="#111"
              stroke="#262525"
              strokeWidth="0.8"
            />
            <path
              d="M 380 90 Q 440 70 520 80 T 600 130 T 540 220 T 420 200 Z"
              fill="#111"
              stroke="#262525"
              strokeWidth="0.8"
            />

            {/* Primary Orbit Ground Track (Sinusoidal orbital projection) */}
            <path
              d="M 20 280 Q 180 40 360 280 T 700 40"
              fill="none"
              stroke="#38bdf8"
              strokeWidth="2"
              strokeDasharray="6 3"
              className="opacity-80"
            />

            {/* Secondary Debris Orbit Ground Track */}
            <path
              d="M 20 80 Q 200 320 360 120 T 700 300"
              fill="none"
              stroke="#fe1e34"
              strokeWidth="2"
              strokeDasharray="4 2"
              className="opacity-80"
            />

            {/* Conjunction Encounter Waypoint Intersection */}
            <circle cx="360" cy="180" r="18" fill="rgba(254, 30, 52, 0.2)" className="animate-ping" />
            <circle cx="360" cy="180" r="7" fill="#fe1e34" stroke="#fff" strokeWidth="2" />

            {/* Satellite Live Icon */}
            <circle cx="280" cy="230" r="5" fill="#38bdf8" stroke="#fff" strokeWidth="1.5" />
            <text x="290" y="235" fill="#38bdf8" fontSize="10" fontFamily="monospace">
              S2A (786 km)
            </text>

            {/* Debris Icon */}
            <circle cx="440" cy="140" r="4" fill="#fe1e34" />
            <text x="450" y="145" fill="#fe1e34" fontSize="10" fontFamily="monospace">
              {active.secondaryName.split("-")[0]}-{active.noradId}
            </text>
          </svg>

          {/* Overlay Box */}
          <div className="absolute top-3 left-3 px-3 py-1.5 rounded-nav bg-charcoal/80 backdrop-blur-md border border-white/10 text-xs font-mono">
            <span className="text-pebble">Encounter Lat/Lon: </span>
            <span className="text-bone font-semibold">0.00° N, 0.00° E (B-Plane Apex)</span>
          </div>
        </div>
      </div>

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
                  onClick={() => setSelectedConjunction(c.id)}
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
                      <div className={`font-semibold ${c.missDistanceM < 1000 ? "text-arterial" : "text-bone"}`}>
                        {c.missDistanceM < 1000 ? `${c.missDistanceM.toFixed(1)} m` : `${(c.missDistanceM / 1000).toFixed(2)} km`}
                      </div>
                    </div>
                    <div>
                      <div className="text-[10px] uppercase">Collision Pc</div>
                      <div className={`font-semibold ${c.pc >= 1e-4 ? "text-arterial font-bold" : "text-bone"}`}>
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
                <span className={`font-bold ${active.pc >= 1e-4 ? "text-arterial text-sm" : "text-bone"}`}>
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
              Calculated Pc ({active.pc.toExponential(2)}) breaches flight safety rules. Recommended maneuver window: T - 8.0h using radial thrust pulse (+0.12 m/s &Delta;V).
            </p>
            <div className="p-2.5 rounded bg-void/80 border border-white/5 text-[11px] font-mono text-pebble">
              <strong>Advisory Directive:</strong> Automated thruster firing is strictly disabled. Submit formal maneuver requisition to Flight Dynamics team.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
