"use client";

import React, { useState, useEffect } from "react";
import {
  Satellite,
  Shield,
  Activity,
  Layers,
  Zap,
  Thermometer,
  RotateCcw,
  Cpu,
  Crosshair,
  AlertTriangle,
  Clock,
  ArrowUpRight,
  Filter,
} from "lucide-react";
import { ConstellationMatrixResponse, FleetAsset, CrossConjunctionItem } from "../lib/types";
import { fetchConstellationMatrix } from "../lib/api";
import { StatusBadge } from "./StatusBadge";
import { SimulatedBadge } from "./SimulatedBadge";
import { playAudioCue } from "../lib/audio";

interface ConstellationMatrixProps {
  onSelectAsset?: (assetId: string) => void;
}

export function ConstellationMatrix({ onSelectAsset }: ConstellationMatrixProps) {
  const [data, setData] = useState<ConstellationMatrixResponse | null>(null);
  const [filterAsset, setFilterAsset] = useState<string>("ALL");
  const [criticalOnly, setCriticalOnly] = useState<boolean>(false);

  useEffect(() => {
    let mounted = true;
    fetchConstellationMatrix().then((res) => {
      if (mounted) setData(res);
    });
    return () => {
      mounted = false;
    };
  }, []);

  if (!data) {
    return (
      <div className="p-8 rounded-card bg-charcoal border border-white/10 text-center font-mono text-ash text-xs">
        Loading Constellation Fleet Matrix & Threat Screening...
      </div>
    );
  }

  // Filter conjunctions
  const filteredConjunctions = data.cross_conjunctions.filter((c) => {
    if (filterAsset !== "ALL" && c.primary_asset_id !== filterAsset) return false;
    if (criticalOnly && c.risk_class !== "CRITICAL") return false;
    return true;
  });

  return (
    <div className="p-5 rounded-card bg-charcoal border border-white/10 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-white/10 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <Satellite className="w-5 h-5 text-sky-400" />
            <h2 className="text-base font-bold text-bone">
              Constellation Mode & Multi-Asset Conjunction Matrix (F8 & F11)
            </h2>
            <SimulatedBadge />
          </div>
          <p className="text-xs text-ash font-mono mt-0.5">
            Fleet-Wide Subsystem Health Barometer & Cross-Orbit Debris Conjunction Heatmap
          </p>
        </div>

        {/* Fleet Health Barometer Pill */}
        <div className="flex items-center gap-3">
          <div className="px-3.5 py-1.5 rounded-card bg-void/80 border border-white/10 flex items-center gap-2 text-xs font-mono">
            <span className="text-pebble">Fleet Aggregate:</span>
            <span className="text-emerald-400 font-bold text-sm">
              {data.aggregate_health_score.toFixed(2)} / 10.0
            </span>
            <StatusBadge level={data.fleet_risk_level} size="sm" />
          </div>
        </div>
      </div>

      {/* Fleet Asset Cards Grid (3 Satellites) */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {data.assets.map((asset) => {
          const isSelected = filterAsset === asset.id;
          return (
            <div
              key={asset.id}
              onClick={() => {
                playAudioCue("click");
                setFilterAsset(isSelected ? "ALL" : asset.id);
                if (onSelectAsset) onSelectAsset(asset.id);
              }}
              className={`p-4 rounded-card cursor-pointer transition-all border ${
                isSelected
                  ? "bg-smoke border-sky-400/80 shadow-glass"
                  : "bg-void/70 border-white/10 hover:border-white/20"
              }`}
            >
              {/* Card Header */}
              <div className="flex items-start justify-between border-b border-white/10 pb-2">
                <div>
                  <div className="font-bold font-mono text-sm text-bone">{asset.name}</div>
                  <div className="text-[11px] text-pebble font-mono">NORAD #{asset.norad_id} · {asset.type}</div>
                </div>
                <StatusBadge level={asset.risk_level} size="sm" />
              </div>

              {/* Orbit Specs */}
              <div className="mt-2 text-xs font-mono text-pebble flex justify-between">
                <span>{asset.orbit.altitude_km} km SSO</span>
                <span>Inc: {asset.orbit.inclination_deg}°</span>
                <span>T: {asset.orbit.period_min}m</span>
              </div>

              {/* Subsystems Mini Bars */}
              <div className="mt-3 space-y-2 text-[11px] font-mono">
                {/* EPS */}
                <div className="flex items-center justify-between text-pebble">
                  <span className="flex items-center gap-1">
                    <Zap className="w-3 h-3 text-amber-400" />
                    EPS Bus:
                  </span>
                  <span className="text-bone font-semibold">{asset.subsystems.eps.bus_voltage_v} V ({asset.subsystems.eps.battery_temp_c}°C)</span>
                </div>

                {/* ADCS */}
                <div className="flex items-center justify-between text-pebble">
                  <span className="flex items-center gap-1">
                    <RotateCcw className="w-3 h-3 text-sky-400" />
                    ADCS Reaction:
                  </span>
                  <span className="text-bone font-semibold">{asset.subsystems.adcs.wheel_rpm} RPM</span>
                </div>

                {/* Payload Duty */}
                <div className="flex items-center justify-between text-pebble">
                  <span className="flex items-center gap-1">
                    <Activity className="w-3 h-3 text-emerald-400" />
                    Payload Duty:
                  </span>
                  <span className="text-emerald-400 font-bold">{asset.subsystems.payload.duty_cycle_pct}% Active</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Cross-Conjunction Screening Heatmap & Table */}
      <div className="p-4 rounded-card bg-void/80 border border-white/10 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-white/10 pb-3">
          <div className="flex items-center gap-2 text-xs font-mono uppercase tracking-wider text-ash">
            <Crosshair className="w-4 h-4 text-rose-400" />
            <span>Cross-Conjunction Screening Matrix ({filteredConjunctions.length} Matches)</span>
          </div>

          {/* Quick Filters */}
          <div className="flex items-center gap-2">
            <button
              onClick={() => {
                playAudioCue("click");
                setCriticalOnly(!criticalOnly);
              }}
              className={`px-2.5 py-1 text-xs font-mono rounded border transition-all ${
                criticalOnly
                  ? "bg-arterial/20 border-arterial text-red-300 font-bold"
                  : "bg-smoke border-white/10 text-ash hover:text-bone"
              }`}
            >
              {criticalOnly ? "Showing Critical Only" : "Filter Critical Only"}
            </button>

            {filterAsset !== "ALL" && (
              <button
                onClick={() => {
                  playAudioCue("click");
                  setFilterAsset("ALL");
                }}
                className="px-2 py-1 text-xs font-mono rounded bg-smoke text-ash hover:text-bone"
              >
                Clear Filter ({filterAsset})
              </button>
            )}
          </div>
        </div>

        {/* Table of Cross Conjunctions */}
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead>
              <tr className="border-b border-white/10 text-pebble uppercase text-[10px]">
                <th className="py-2 px-3">Primary Asset</th>
                <th className="py-2 px-3">Secondary Debris</th>
                <th className="py-2 px-3">TCA (Hours)</th>
                <th className="py-2 px-3">Miss Distance</th>
                <th className="py-2 px-3">Rel Velocity</th>
                <th className="py-2 px-3">Collision Pc</th>
                <th className="py-2 px-3">Risk Severity</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {filteredConjunctions.map((c) => (
                <tr key={c.id} className="hover:bg-smoke/40 transition-colors">
                  <td className="py-2.5 px-3 font-bold text-sky-300">{c.primary_name}</td>
                  <td className="py-2.5 px-3 text-bone font-medium">{c.secondary_name}</td>
                  <td className="py-2.5 px-3 text-pebble">+{c.tca_hours}h</td>
                  <td className="py-2.5 px-3">
                    <span className={c.miss_distance_m < 1000 ? "text-arterial font-bold" : "text-bone"}>
                      {c.miss_distance_m < 1000 ? `${c.miss_distance_m.toFixed(1)} m` : `${(c.miss_distance_m / 1000).toFixed(2)} km`}
                    </span>
                  </td>
                  <td className="py-2.5 px-3 text-pebble">{c.relative_velocity_kms.toFixed(2)} km/s</td>
                  <td className="py-2.5 px-3">
                    <span className={c.pc >= 1e-4 ? "text-arterial font-bold" : "text-bone"}>
                      {c.pc.toExponential(2)}
                    </span>
                  </td>
                  <td className="py-2.5 px-3">
                    <StatusBadge level={c.risk_class} size="sm" />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
