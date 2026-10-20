"use client";

import React, { useState, useEffect } from "react";
import {
  PlayCircle,
  PauseCircle,
  RotateCcw,
  FastForward,
  CheckCircle,
  AlertTriangle,
  ShieldAlert,
  Flame,
  Orbit,
  Layers,
  ChevronRight,
  Sparkles,
} from "lucide-react";
import { RiskSnapshot, RiskLevel } from "../../lib/types";
import { RiskGauge } from "../../components/RiskGauge";
import { StatusBadge } from "../../components/StatusBadge";
import { SimulatedBadge } from "../../components/SimulatedBadge";
import { PhysicsSandbox } from "../../components/PhysicsSandbox";
import { playAudioCue } from "../../lib/audio";

interface Scenario {
  id: string;
  hour: number;
  name: string;
  description: string;
  snapshot: RiskSnapshot;
}

export default function DemoPage() {
  const scenarios: Scenario[] = [
    {
      id: "SCENARIO-01",
      hour: 2,
      name: "Nominal Flight Operations",
      description: "Satellite Sentinel-2A bus telemetry and orbit are completely normal. No hazards present.",
      snapshot: {
        id: "RSN-DEMO-01",
        asset_id: "SENTINEL-2A",
        ts: new Date().toISOString(),
        score: 6.53,
        level: "NOMINAL",
        r_h: 0.04,
        r_d: 0.02,
        r_e: 0.10,
        drivers: [
          {
            module: "health",
            driver: "eps_battery_temp_c",
            contribution: 0.04,
            share_pct: 52.3,
            evidence: { temp_c: 24.1 },
          },
        ],
        rationale: "NOMINAL MISSION OPERATIONS: All subsystems and orbit nominal. No director action required.",
        recommendations: [
          {
            action: "MONITOR_NOMINAL",
            priority: 1,
            rationale: "Routine telemetry polling active.",
            source_module: "fusion",
          },
        ],
        defer_eo_payloads: false,
        critical_override_applied: false,
        synthetic: true,
        created_at: new Date().toISOString(),
      },
    },
    {
      id: "SCENARIO-02",
      hour: 8,
      name: "EPS Battery Thermal Anomaly",
      description: "EPS battery cell temperature elevates to 38.6°C. Cross-system safety rule defers secondary imaging.",
      snapshot: {
        id: "RSN-DEMO-02",
        asset_id: "SENTINEL-2A",
        ts: new Date().toISOString(),
        score: 62.91,
        level: "WARNING",
        r_h: 0.68,
        r_d: 0.05,
        r_e: 0.15,
        drivers: [
          {
            module: "health",
            driver: "eps_battery_temp_c",
            contribution: 0.68,
            share_pct: 69.7,
            evidence: { temp_c: 38.6, threshold: 32.0 },
          },
        ],
        rationale: "SPACECRAFT HEALTH ANOMALY: Battery thermal runaway risk. Secondary imaging payloads deferred.",
        recommendations: [
          {
            action: "TELEMETRY_DIAGNOSTIC",
            priority: 1,
            rationale: "Initiate battery thermal review and disable high-draw payload sensors.",
            source_module: "health",
          },
        ],
        defer_eo_payloads: true,
        critical_override_applied: false,
        synthetic: true,
        created_at: new Date().toISOString(),
      },
    },
    {
      id: "SCENARIO-03",
      hour: 14,
      name: "Critical Fengyun-1C Debris Conjunction",
      description: "Close approach encounter with Fengyun debris (miss: 315m, Pc=2.4e-4). Hard override forces CRITICAL.",
      snapshot: {
        id: "RSN-DEMO-03",
        asset_id: "SENTINEL-2A",
        ts: new Date().toISOString(),
        score: 82.46,
        level: "CRITICAL",
        r_h: 0.05,
        r_d: 0.95,
        r_e: 0.20,
        drivers: [
          {
            module: "debris",
            driver: "pc_collision_probability",
            contribution: 0.95,
            share_pct: 75.4,
            evidence: { miss_m: 315.4, pc: 2.4e-4 },
          },
        ],
        rationale: "CRITICAL CONJUNCTION EMERGENCY: Hard safety override triggered (Pc=2.40e-04 > 1.00e-04 ceiling).",
        recommendations: [
          {
            action: "CAM_ASSESSMENT",
            priority: 1,
            rationale: "Collision Avoidance Maneuver requisition required. Flight dynamics alerted.",
            source_module: "debris",
          },
        ],
        defer_eo_payloads: false,
        critical_override_applied: true,
        synthetic: true,
        created_at: new Date().toISOString(),
      },
    },
    {
      id: "SCENARIO-04",
      hour: 20,
      name: "Cyclone Flood Emergency Tasking",
      description: "Severe cyclone flood event (320 km²) elevates Earth observation urgency. Spacecraft health nominal.",
      snapshot: {
        id: "RSN-DEMO-04",
        asset_id: "SENTINEL-2A",
        ts: new Date().toISOString(),
        score: 32.51,
        level: "WATCH",
        r_h: 0.08,
        r_d: 0.04,
        r_e: 0.78,
        drivers: [
          {
            module: "disaster",
            driver: "flooded_area_km2",
            contribution: 0.78,
            share_pct: 64.7,
            evidence: { flooded_area_km2: 320.0 },
          },
        ],
        rationale: "HIGH-PRIORITY EARTH OBSERVATION TASKING: Active flood event detected (320 km²). Observation urgency elevates Mission Score to 32.5 (WATCH).",
        recommendations: [
          {
            action: "TASK_DISASTER_IMAGERY",
            priority: 1,
            rationale: "Schedule SAR C-Band radar acquisition pass over target coordinates.",
            source_module: "disaster",
          },
        ],
        defer_eo_payloads: false,
        critical_override_applied: false,
        synthetic: true,
        created_at: new Date().toISOString(),
      },
    },
  ];

  const [currentIndex, setCurrentIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [speed, setSpeed] = useState<number>(1);
  const [demoTab, setDemoTab] = useState<"scenario" | "sandbox">("scenario");

  const activeScenario = scenarios[currentIndex];

  useEffect(() => {
    if (!isPlaying) return;
    const intervalTime = 4000 / speed;
    const timer = setInterval(() => {
      setCurrentIndex((prev) => (prev + 1) % scenarios.length);
    }, intervalTime);
    return () => clearInterval(timer);
  }, [isPlaying, speed, scenarios.length]);

  return (
    <div className="space-y-6">
      {/* Title Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-4 rounded-card bg-charcoal border border-white/10">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold tracking-tight text-bone flex items-center gap-2">
              <PlayCircle className="w-5 h-5 text-arterial" />
              Day in the Life Mission Scenario Player
            </h1>
            <SimulatedBadge />
          </div>
          <p className="text-xs text-ash font-mono mt-0.5">
            Interactive Multi-Hazard Replay per PRD §9 · Nominal &rarr; Thermal Anomaly &rarr; Conjunction &rarr; Disaster
          </p>
        </div>

        {/* Sub-Navigation Tabs */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => {
              playAudioCue("click");
              setDemoTab("scenario");
            }}
            className={`px-3 py-1.5 rounded-nav text-xs font-mono transition-all ${
              demoTab === "scenario"
                ? "bg-arterial/20 text-red-300 border border-arterial/50 font-bold"
                : "bg-smoke text-ash hover:text-bone"
            }`}
          >
            Flight Replay (PRD §9)
          </button>
          <button
            onClick={() => {
              playAudioCue("click");
              setDemoTab("sandbox");
            }}
            className={`px-3 py-1.5 rounded-nav text-xs font-mono transition-all flex items-center gap-1.5 ${
              demoTab === "sandbox"
                ? "bg-sky-500/20 text-sky-300 border border-sky-400/50 font-bold"
                : "bg-smoke text-ash hover:text-bone"
            }`}
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Physics Sandbox (F6)</span>
          </button>
        </div>
      </div>

      {demoTab === "sandbox" ? (
        <PhysicsSandbox />
      ) : (
        <>
          {/* Timeline & Playback Card */}
          <div className="flex items-center justify-between gap-4 p-4 rounded-card bg-charcoal border border-white/10">
            <span className="text-xs font-mono uppercase text-ash">Playback Controls (PRD §9 Scenario):</span>
            <div className="flex items-center gap-2 p-1.5 rounded-nav bg-smoke border border-white/15 text-xs font-mono">
              <button
                onClick={() => setIsPlaying(!isPlaying)}
                className="flex items-center gap-1.5 px-3 py-1 rounded bg-arterial hover:bg-red-600 text-white font-bold transition-colors"
              >
                {isPlaying ? (
                  <>
                    <PauseCircle className="w-4 h-4" /> Pause
                  </>
                ) : (
                  <>
                <PlayCircle className="w-4 h-4" /> Play
              </>
            )}
          </button>

          <button
            onClick={() => setCurrentIndex(0)}
            className="p-1.5 text-ash hover:text-bone rounded hover:bg-white/5"
            title="Reset to Beginning"
          >
            <RotateCcw className="w-3.5 h-3.5" />
          </button>

          <button
            onClick={() => setSpeed(speed === 1 ? 2 : speed === 2 ? 4 : 1)}
            className="px-2 py-1 rounded text-pebble hover:text-bone"
            title="Toggle playback speed"
          >
            {speed}x
          </button>
        </div>
      </div>

      {/* Timeline Scrubber Card */}
      <div className="p-5 rounded-card bg-charcoal border border-white/10 space-y-4">
        <div className="flex items-center justify-between text-xs font-mono">
          <span className="text-ash uppercase tracking-wider">Mission Timeline: 24-Hour Orbital Span</span>
          <span className="text-bone font-bold">Hour {activeScenario.hour}:00 / 24:00</span>
        </div>

        {/* Timeline Bar */}
        <div className="grid grid-cols-4 gap-2">
          {scenarios.map((s, idx) => {
            const isSelected = currentIndex === idx;
            return (
              <button
                key={s.id}
                onClick={() => {
                  setCurrentIndex(idx);
                  setIsPlaying(false);
                }}
                className={`p-3 rounded-card text-left transition-all border ${
                  isSelected
                    ? "bg-smoke border-arterial shadow-glass"
                    : "bg-void/60 border-white/5 hover:border-white/15"
                }`}
              >
                <div className="flex items-center justify-between text-[11px] font-mono mb-1">
                  <span className="text-pebble">T + {s.hour}h</span>
                  <StatusBadge level={s.snapshot.level} size="sm" />
                </div>
                <div className="text-xs font-bold font-mono text-bone truncate">{s.name}</div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Reactive Live Evaluation Result Card */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Simulated Gauge */}
        <div className="lg:col-span-5 p-6 rounded-card bg-charcoal border border-white/10 flex flex-col items-center justify-between">
          <div className="w-full flex items-center justify-between border-b border-white/10 pb-3">
            <span className="text-xs uppercase font-mono tracking-wider text-ash">
              Reactive Risk Score
            </span>
            <StatusBadge level={activeScenario.snapshot.level} size="md" />
          </div>

          <RiskGauge
            score={activeScenario.snapshot.score}
            level={activeScenario.snapshot.level}
            size={280}
          />

          <div className="w-full pt-3 border-t border-white/10 flex justify-between text-xs font-mono text-pebble">
            <span>r_h: <strong className="text-bone">{activeScenario.snapshot.r_h.toFixed(2)}</strong></span>
            <span>r_d: <strong className="text-bone">{activeScenario.snapshot.r_d.toFixed(2)}</strong></span>
            <span>r_e: <strong className="text-bone">{activeScenario.snapshot.r_e.toFixed(2)}</strong></span>
          </div>
        </div>

        {/* Right Column: Scenario Details & Rationale */}
        <div className="lg:col-span-7 space-y-4">
          {/* Active Scenario Card */}
          <div className="p-5 rounded-card bg-charcoal border border-white/10 space-y-3">
            <div className="flex items-center justify-between border-b border-white/10 pb-2">
              <span className="text-xs font-mono uppercase tracking-wider text-pebble">
                Active Flight Stage #{currentIndex + 1}
              </span>
              <span className="text-xs font-mono text-bone font-semibold">
                {activeScenario.name}
              </span>
            </div>
            <p className="text-xs text-ash font-sans leading-relaxed">
              {activeScenario.description}
            </p>
          </div>

          {/* Deterministic Safety Rationale */}
          <div className="p-5 rounded-card bg-charcoal border border-white/10 space-y-2">
            <div className="text-xs font-mono uppercase tracking-wider text-pebble">
              Safety Engine Decision Rationale
            </div>
            <div className="p-3 rounded bg-void text-xs font-sans text-bone border border-white/5">
              {activeScenario.snapshot.rationale}
            </div>
          </div>

          {/* Action Advisory */}
          <div className="p-5 rounded-card bg-charcoal border border-white/10 space-y-2">
            <div className="text-xs font-mono uppercase tracking-wider text-pebble">
              Actionable Flight Recommendation
            </div>
            {activeScenario.snapshot.recommendations.map((rec, i) => (
              <div
                key={i}
                className="p-3 rounded bg-smoke/40 border border-white/5 flex items-center justify-between text-xs font-mono"
              >
                <span className="text-bone font-semibold">{rec.action}</span>
                <span className="text-pebble text-[11px]">{rec.rationale}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
      </>
      )}
    </div>
  );
}
