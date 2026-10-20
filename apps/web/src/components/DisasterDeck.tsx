"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  Layers,
  MapPin,
  Eye,
  Sliders,
  AlertTriangle,
  Building2,
  Zap,
  Activity,
  Maximize2,
  Minimize2,
  CheckCircle2,
  Radio,
  FileCode,
  Flame,
  Droplets,
  Sparkles,
} from "lucide-react";
import { DisasterScenario } from "../lib/types";
import { fetchDisasterDeck } from "../lib/api";
import { SimulatedBadge } from "./SimulatedBadge";
import { playAudioCue } from "../lib/audio";

interface DisasterDeckProps {
  onScenarioSelect?: (scenario: DisasterScenario) => void;
  simulateDegradedHealth?: boolean;
}

export function DisasterDeck({
  onScenarioSelect,
  simulateDegradedHealth = false,
}: DisasterDeckProps) {
  const [scenarios, setScenarios] = useState<DisasterScenario[]>([]);
  const [selectedId, setSelectedId] = useState<string>("DIS-EMILIA-FLOOD-2023");
  const [sliderPosition, setSliderPosition] = useState<number>(50); // percentage 0-100
  const [showMask, setShowMask] = useState<boolean>(true);
  const [showInfra, setShowInfra] = useState<boolean>(true);
  const [showGeoJson, setShowGeoJson] = useState<boolean>(false);
  const [isDragging, setIsDragging] = useState<boolean>(false);

  const containerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    let mounted = true;
    fetchDisasterDeck().then((deck) => {
      if (mounted) {
        setScenarios(deck.scenarios);
      }
    });
    return () => {
      mounted = false;
    };
  }, []);

  const active = scenarios.find((s) => s.id === selectedId) || scenarios[0];

  // Drag handler for Split Slider
  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isDragging || !containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const x = Math.max(0, Math.min(rect.width, e.clientX - rect.left));
    setSliderPosition(Math.round((x / rect.width) * 100));
  };

  const handleTouchMove = (e: React.TouchEvent) => {
    if (!isDragging || !containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const x = Math.max(0, Math.min(rect.width, e.touches[0].clientX - rect.left));
    setSliderPosition(Math.round((x / rect.width) * 100));
  };

  if (!active) {
    return (
      <div className="p-8 rounded-card bg-charcoal border border-white/10 text-center font-mono text-ash text-xs">
        Loading Earth Observation Disaster Intelligence Deck...
      </div>
    );
  }

  // Priority adjustment if degraded health interlock is simulated
  const effectivePriority = simulateDegradedHealth
    ? Math.max(0.1, active.priority * 0.4)
    : active.priority;

  return (
    <div className="p-5 rounded-card bg-charcoal border border-white/10 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-white/10 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <Layers className="w-5 h-5 text-amber-400" />
            <h2 className="text-base font-bold text-bone">
              Disaster Intelligence Deck & High-Res Tile Visualizer (F7)
            </h2>
            <SimulatedBadge />
          </div>
          <p className="text-xs text-ash font-mono mt-0.5">
            Multi-Sensor SAR & Optical Segmentation, Infrastructure Triage & Priority Engine
          </p>
        </div>

        {/* Sensor & Cloud Badge */}
        <div className="flex items-center gap-2">
          <div className="px-3 py-1.5 rounded-nav bg-smoke border border-emerald-500/30 text-xs font-mono text-emerald-400 flex items-center gap-1.5">
            <Sparkles className="w-3.5 h-3.5" />
            <span>{active.sensor_type === "radar" ? "SAR C-Band: All-Weather Penetration" : "MSI Optical: 13-Band Multi-Spectral"}</span>
          </div>
        </div>
      </div>

      {/* Scenario Selector Pills */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1">
        {scenarios.map((s) => {
          const isSelected = s.id === selectedId;
          const isFlood = s.disaster_type === "flood";
          return (
            <button
              key={s.id}
              onClick={() => {
                playAudioCue("click");
                setSelectedId(s.id);
                if (onScenarioSelect) onScenarioSelect(s);
              }}
              className={`flex items-center gap-2 px-3 py-2 rounded-card text-xs font-mono transition-all whitespace-nowrap border ${
                isSelected
                  ? isFlood
                    ? "bg-sky-500/20 border-sky-400/80 text-sky-200 font-bold shadow-glass"
                    : "bg-rose-500/20 border-rose-400/80 text-rose-200 font-bold shadow-glass"
                  : "bg-void/70 border-white/5 text-ash hover:border-white/20"
              }`}
            >
              {isFlood ? <Droplets className="w-3.5 h-3.5 text-sky-400" /> : <Flame className="w-3.5 h-3.5 text-rose-400" />}
              <span>{s.name}</span>
              <span className="text-[10px] text-pebble">({s.area_km2} km²)</span>
            </button>
          );
        })}
      </div>

      {/* Main Visualizer & Damage Matrix Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Split-View Wipe Canvas */}
        <div className="lg:col-span-7 space-y-3">
          <div className="flex items-center justify-between text-xs font-mono text-ash">
            <span className="flex items-center gap-1.5 uppercase tracking-wider">
              <MapPin className="w-3.5 h-3.5 text-rose-400" />
              {active.location} · {active.sensor}
            </span>
            <div className="flex items-center gap-3 text-[11px]">
              <span className="text-pebble">Drag divider to compare baseline vs AI mask</span>
            </div>
          </div>

          {/* Interactive Split-View Comparison Canvas */}
          <div
            ref={containerRef}
            onMouseDown={() => setIsDragging(true)}
            onMouseUp={() => setIsDragging(false)}
            onMouseLeave={() => setIsDragging(false)}
            onMouseMove={handleMouseMove}
            onTouchStart={() => setIsDragging(true)}
            onTouchEnd={() => setIsDragging(false)}
            onTouchMove={handleTouchMove}
            className="relative w-full aspect-square max-h-[420px] bg-void rounded-card border border-white/10 overflow-hidden select-none cursor-ew-resize"
          >
            {/* SVG Base & Classification Artwork */}
            <svg viewBox="0 0 400 400" className="w-full h-full pointer-events-none">
              <defs>
                <radialGradient id="sar-bg-deep" cx="50%" cy="50%" r="60%">
                  <stop offset="0%" stopColor="#1e1c1f" />
                  <stop offset="100%" stopColor="#0a090b" />
                </radialGradient>
                {/* Clip path for split view */}
                <clipPath id="split-clip-left">
                  <rect x="0" y="0" width={(sliderPosition / 100) * 400} height="400" />
                </clipPath>
                <clipPath id="split-clip-right">
                  <rect x={(sliderPosition / 100) * 400} y="0" width={400 - (sliderPosition / 100) * 400} height="400" />
                </clipPath>
              </defs>

              {/* Background Landscape */}
              <rect width="400" height="400" fill="url(#sar-bg-deep)" />

              {/* Underlying Terrain Topography */}
              <path
                d="M 20 80 Q 120 40 220 90 T 380 70 L 400 400 L 0 400 Z"
                fill="#131215"
                stroke="#242226"
                strokeWidth="1"
              />

              {/* Permanent River / Valley Feature */}
              <path
                d="M 0 150 Q 120 120 200 170 T 320 230 T 400 210"
                fill="none"
                stroke="#080709"
                strokeWidth="16"
                strokeLinecap="round"
              />

              {/* Left Side: Pre-Event Baseline (Clean Topography) */}
              <g clipPath="url(#split-clip-left)">
                <text x="15" y="25" fill="#a1a1aa" fontSize="10" fontFamily="monospace" fontWeight="bold">
                  PRE-EVENT BASELINE ({active.sensor_type.toUpperCase()})
                </text>
                {/* Roads / Fields */}
                <line x1="80" y1="0" x2="160" y2="400" stroke="#2a282d" strokeWidth="1" />
                <line x1="240" y1="0" x2="320" y2="400" stroke="#2a282d" strokeWidth="1" />
              </g>

              {/* Right Side: Post-Event Inundation / Burn Classification */}
              <g clipPath="url(#split-clip-right)">
                <text x="390" y="25" textAnchor="end" fill={active.disaster_type === "flood" ? "#38bdf8" : "#fb7185"} fontSize="10" fontFamily="monospace" fontWeight="bold">
                  AI DETECTION OVERLAY (DICE {active.mean_dice.toFixed(4)})
                </text>

                {/* Flood Inundation or Burn Scar Mask */}
                {showMask && (
                  <path
                    d={
                      active.disaster_type === "flood"
                        ? "M 70 130 Q 150 90 220 140 Q 280 160 340 200 Q 380 240 330 290 Q 250 310 170 260 Q 80 230 50 180 Z"
                        : "M 100 100 Q 200 60 280 120 Q 360 180 340 260 Q 310 320 230 330 Q 140 310 90 240 Q 60 170 100 100 Z"
                    }
                    fill={active.disaster_type === "flood" ? "rgba(56, 189, 248, 0.42)" : "rgba(254, 30, 52, 0.45)"}
                    stroke={active.disaster_type === "flood" ? "#38bdf8" : "#fe1e34"}
                    strokeWidth="2"
                  />
                )}
              </g>

              {/* Critical Infrastructure Nodes Overlay */}
              {showInfra && (
                <g>
                  {/* Power Substation 1 */}
                  <circle cx="180" cy="140" r="4" fill="#facc15" stroke="#ffffff" strokeWidth="1" />
                  <text x="190" y="144" fill="#facc15" fontSize="9" fontFamily="monospace">Substation #04</text>

                  {/* Bridge Node */}
                  <rect x="235" y="175" width="8" height="8" fill="#fe1e34" stroke="#ffffff" strokeWidth="1" />
                  <text x="248" y="182" fill="#ff6b7a" fontSize="9" fontFamily="monospace">Viaduct Bridge</text>

                  {/* Medical Hospital Center */}
                  <polygon points="120,210 125,220 115,220" fill="#38bdf8" stroke="#ffffff" strokeWidth="1" />
                  <text x="130" y="218" fill="#7dd3fc" fontSize="9" fontFamily="monospace">Regional Clinic</text>
                </g>
              )}

              {/* Draggable Divider Line & Knob */}
              <line
                x1={(sliderPosition / 100) * 400}
                y1="0"
                x2={(sliderPosition / 100) * 400}
                y2="400"
                stroke="#ffffff"
                strokeWidth="2"
              />
              <circle
                cx={(sliderPosition / 100) * 400}
                cy="200"
                r="10"
                fill="#ffffff"
                stroke="#000000"
                strokeWidth="2"
              />
              <path
                d={`M ${(sliderPosition / 100) * 400 - 4} 200 L ${(sliderPosition / 100) * 400 + 4} 200`}
                stroke="#000000"
                strokeWidth="1.5"
              />
            </svg>

            {/* Floating Layer Toggles (Bottom-Left) */}
            <div className="absolute bottom-3 left-3 flex items-center gap-2">
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  playAudioCue("click");
                  setShowMask(!showMask)}
                }
                className={`px-2.5 py-1 rounded text-[11px] font-mono border transition-all ${
                  showMask
                    ? "bg-sky-500/20 border-sky-400 text-sky-200"
                    : "bg-charcoal/80 border-white/10 text-ash hover:text-bone"
                }`}
              >
                {showMask ? "Hide AI Mask" : "Show AI Mask"}
              </button>

              <button
                onClick={(e) => {
                  e.stopPropagation();
                  playAudioCue("click");
                  setShowInfra(!showInfra)}
                }
                className={`px-2.5 py-1 rounded text-[11px] font-mono border transition-all ${
                  showInfra
                    ? "bg-amber-500/20 border-amber-400 text-amber-200"
                    : "bg-charcoal/80 border-white/10 text-ash hover:text-bone"
                }`}
              >
                {showInfra ? "Hide Infra" : "Show Infra"}
              </button>

              <button
                onClick={(e) => {
                  e.stopPropagation();
                  playAudioCue("click");
                  setShowGeoJson(!showGeoJson);
                }}
                className="px-2.5 py-1 rounded bg-charcoal/80 border border-white/10 text-[11px] font-mono text-pebble hover:text-bone flex items-center gap-1"
              >
                <FileCode className="w-3 h-3 text-sky-400" />
                <span>GeoJSON</span>
              </button>
            </div>
          </div>
        </div>

        {/* Right: Damage & Humanitarian Impact Triage */}
        <div className="lg:col-span-5 space-y-4">
          {/* Disaster Priority Score Card */}
          <div className="p-4 rounded-card bg-charcoal border border-white/10 space-y-3">
            <div className="flex items-center justify-between border-b border-white/10 pb-2">
              <div>
                <div className="text-[10px] uppercase font-mono text-pebble">Observation Priority Score (r_e)</div>
                <div className="text-xl font-bold font-mono text-amber-400">
                  {effectivePriority.toFixed(3)} / 1.000
                </div>
              </div>
              <div className="px-2.5 py-1 rounded bg-smoke border border-white/10 font-mono text-xs text-bone">
                Confidence: {(active.confidence * 100).toFixed(0)}%
              </div>
            </div>

            {simulateDegradedHealth && (
              <div className="p-2 rounded bg-amber-950/40 border border-amber-500/40 text-[11px] font-mono text-amber-300 flex items-center gap-1.5">
                <AlertTriangle className="w-3.5 h-3.5 shrink-0" />
                <span>Observation tasking score penalized 60% due to active spacecraft bus anomaly.</span>
              </div>
            )}

            {/* Priority Drivers List */}
            <div className="space-y-1.5 text-xs font-mono">
              {active.priority_drivers.map((d, idx) => (
                <div key={idx} className="flex justify-between py-0.5 border-b border-white/5">
                  <span className="text-pebble">{d.factor}:</span>
                  <span className="text-bone font-semibold">+{d.score.toFixed(2)}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Impact Telemetry Counter Grid */}
          <div className="grid grid-cols-2 gap-3">
            <div className="p-3 rounded-card bg-void/80 border border-white/10 space-y-1">
              <div className="text-[10px] font-mono text-pebble uppercase flex items-center gap-1">
                <Activity className="w-3 h-3 text-sky-400" />
                Affected Extent
              </div>
              <div className="text-lg font-bold font-mono text-bone">
                {active.area_km2.toFixed(1)} km²
              </div>
              <div className="text-[10px] font-mono text-pebble">
                {active.infrastructure_impact.agricultural_hectares.toLocaleString()} ha Agriculture
              </div>
            </div>

            <div className="p-3 rounded-card bg-void/80 border border-white/10 space-y-1">
              <div className="text-[10px] font-mono text-pebble uppercase flex items-center gap-1">
                <Building2 className="w-3 h-3 text-rose-400" />
                Population Exposed
              </div>
              <div className="text-lg font-bold font-mono text-bone">
                {active.infrastructure_impact.population_exposed.toLocaleString()}
              </div>
              <div className="text-[10px] font-mono text-pebble">
                {active.infrastructure_impact.hospitals_warning} Hospital Zones
              </div>
            </div>

            <div className="p-3 rounded-card bg-void/80 border border-white/10 space-y-1">
              <div className="text-[10px] font-mono text-pebble uppercase flex items-center gap-1">
                <Zap className="w-3 h-3 text-amber-400" />
                Energy Substations
              </div>
              <div className="text-lg font-bold font-mono text-amber-400">
                {active.infrastructure_impact.substations_affected} Nodes
              </div>
              <div className="text-[10px] font-mono text-pebble">High Flood Inundation</div>
            </div>

            <div className="p-3 rounded-card bg-void/80 border border-white/10 space-y-1">
              <div className="text-[10px] font-mono text-pebble uppercase flex items-center gap-1">
                <MapPin className="w-3 h-3 text-arterial" />
                Critical Bridges
              </div>
              <div className="text-lg font-bold font-mono text-arterial">
                {active.infrastructure_impact.bridges_critical} Crossings
              </div>
              <div className="text-[10px] font-mono text-pebble">Structural Warning</div>
            </div>
          </div>

          {/* AI Segmentation Model Validation Metrics */}
          <div className="p-3.5 rounded bg-smoke/40 border border-white/5 space-y-2 text-xs font-mono">
            <div className="flex justify-between text-pebble">
              <span>U-Net Mean IoU:</span>
              <span className="text-emerald-400 font-bold">{active.mean_iou.toFixed(4)}</span>
            </div>
            <div className="flex justify-between text-pebble">
              <span>Dice F1 Accuracy:</span>
              <span className="text-emerald-400 font-bold">{active.mean_dice.toFixed(4)}</span>
            </div>
            <div className="flex justify-between text-pebble">
              <span>Backscatter Sensitivity:</span>
              <span className="text-bone font-semibold">
                {active.backscatter_drop_db < 0 ? `${active.backscatter_drop_db} dB` : "N/A (Optical NBR)"}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* GeoJSON Footprint Modal / Drawer */}
      {showGeoJson && (
        <div className="p-4 rounded-card bg-void border border-sky-500/40 space-y-2 text-xs font-mono">
          <div className="flex justify-between items-center text-sky-300 font-bold">
            <span className="flex items-center gap-1.5">
              <FileCode className="w-4 h-4" />
              GeoJSON Bounding Coordinates (RFC 7946 Standard)
            </span>
            <button
              onClick={() => setShowGeoJson(false)}
              className="text-ash hover:text-bone text-xs"
            >
              Close
            </button>
          </div>
          <pre className="bg-charcoal p-3 rounded overflow-x-auto text-[11px] text-emerald-300 font-mono">
            {JSON.stringify(active.geojson_footprint, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}
