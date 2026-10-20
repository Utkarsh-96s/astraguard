"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  Radio,
  Play,
  Pause,
  FastForward,
  Volume2,
  VolumeX,
  Activity,
  Zap,
  Thermometer,
  RotateCcw,
  Cpu,
  Compass,
} from "lucide-react";
import { LiveTelemetryPacket } from "../lib/types";
import { fetchLiveTelemetryPacket } from "../lib/api";
import { SimulatedBadge } from "./SimulatedBadge";
import { playAudioCue } from "../lib/audio";

interface LiveTelemetryStreamerProps {
  assetId?: string;
}

export function LiveTelemetryStreamer({ assetId = "SENTINEL-2A" }: LiveTelemetryStreamerProps) {
  const [packet, setPacket] = useState<LiveTelemetryPacket | null>(null);
  const [isPlaying, setIsPlaying] = useState<boolean>(true);
  const [speedMultiplier, setSpeedMultiplier] = useState<number>(1); // 1x, 5x, 20x
  const [soundEnabled, setSoundEnabled] = useState<boolean>(false);
  const [step, setStep] = useState<number>(0);
  const [packetRate, setPacketRate] = useState<number>(1);

  const stepRef = useRef<number>(0);
  stepRef.current = step;

  useEffect(() => {
    if (!isPlaying) return;

    // Interval depending on speed multiplier: 1x=1000ms, 5x=200ms, 20x=50ms
    const intervalMs = Math.max(50, Math.round(1000 / speedMultiplier));
    setPacketRate(speedMultiplier);

    const interval = setInterval(() => {
      const nextStep = stepRef.current + 1;
      setStep(nextStep);
      fetchLiveTelemetryPacket(assetId, nextStep).then((pkt) => {
        setPacket(pkt);
        if (soundEnabled && nextStep % 5 === 0) {
          playAudioCue("ping");
        }
      });
    }, intervalMs);

    return () => clearInterval(interval);
  }, [isPlaying, speedMultiplier, assetId, soundEnabled]);

  // Initial fetch
  useEffect(() => {
    fetchLiveTelemetryPacket(assetId, 0).then(setPacket);
  }, [assetId]);

  const ch = packet?.channels;

  return (
    <div className="p-4 rounded-card bg-charcoal border border-white/10 space-y-3">
      {/* Header & Stream Controller */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-white/10 pb-3">
        <div className="flex items-center gap-2">
          <Radio className={`w-4 h-4 ${isPlaying ? "text-emerald-400 animate-pulse" : "text-ash"}`} />
          <span className="text-xs font-mono font-bold uppercase tracking-wider text-bone">
            Live Telemetry Feed: {assetId}
          </span>
          <SimulatedBadge />
        </div>

        {/* Controls */}
        <div className="flex items-center gap-2 flex-wrap">
          {/* Rate indicator */}
          <div className="px-2 py-0.5 rounded bg-smoke text-[11px] font-mono text-pebble">
            {isPlaying ? `${packetRate} pkt/s` : "PAUSED"} · Seq #{packet?.sequence_number || 0}
          </div>

          {/* Speed Buttons */}
          <div className="flex items-center rounded bg-smoke p-0.5 border border-white/10 text-xs font-mono">
            {[1, 5, 20].map((rate) => (
              <button
                key={rate}
                onClick={() => {
                  playAudioCue("click");
                  setSpeedMultiplier(rate);
                }}
                className={`px-2 py-0.5 rounded transition-all ${
                  speedMultiplier === rate
                    ? "bg-sky-500/20 text-sky-300 font-bold"
                    : "text-ash hover:text-bone"
                }`}
              >
                {rate}x
              </button>
            ))}
          </div>

          {/* Play/Pause */}
          <button
            onClick={() => {
              playAudioCue("click");
              setIsPlaying(!isPlaying);
            }}
            className={`p-1.5 rounded transition-all ${
              isPlaying
                ? "bg-smoke text-ash hover:text-bone"
                : "bg-emerald-500/20 text-emerald-400 border border-emerald-500/40"
            }`}
            title={isPlaying ? "Pause Stream" : "Resume Stream"}
          >
            {isPlaying ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5" />}
          </button>

          {/* Sound Ping Toggle */}
          <button
            onClick={() => {
              playAudioCue("click");
              setSoundEnabled(!soundEnabled);
            }}
            className={`p-1.5 rounded text-xs font-mono transition-all ${
              soundEnabled
                ? "bg-sky-500/20 text-sky-300 border border-sky-400/50"
                : "bg-smoke text-pebble hover:text-ash"
            }`}
            title="Telemetry Ping Audio Cue"
          >
            {soundEnabled ? <Volume2 className="w-3.5 h-3.5" /> : <VolumeX className="w-3.5 h-3.5" />}
          </button>
        </div>
      </div>

      {/* Live Stream Telemetry Gauges */}
      {ch && (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          {/* Battery Temp */}
          <div className="p-2.5 rounded bg-void/80 border border-white/5 space-y-1 font-mono">
            <div className="text-[10px] text-pebble uppercase flex items-center justify-between">
              <span>Battery Temp</span>
              <Thermometer className="w-3 h-3 text-sky-400" />
            </div>
            <div className="text-sm font-bold text-bone">
              {ch.eps_battery_temp_c.toFixed(1)}°C
            </div>
            <div className="text-[10px] text-emerald-400">Nominal 15-35°C</div>
          </div>

          {/* Bus Voltage */}
          <div className="p-2.5 rounded bg-void/80 border border-white/5 space-y-1 font-mono">
            <div className="text-[10px] text-pebble uppercase flex items-center justify-between">
              <span>Bus Voltage</span>
              <Zap className="w-3 h-3 text-amber-400" />
            </div>
            <div className="text-sm font-bold text-bone">
              {ch.eps_bus_voltage_v.toFixed(1)} V
            </div>
            <div className="text-[10px] text-pebble">28V Regulated</div>
          </div>

          {/* Solar Current */}
          <div className="p-2.5 rounded bg-void/80 border border-white/5 space-y-1 font-mono">
            <div className="text-[10px] text-pebble uppercase flex items-center justify-between">
              <span>Array Current</span>
              <Zap className="w-3 h-3 text-amber-400" />
            </div>
            <div className="text-sm font-bold text-bone">
              {ch.eps_solar_array_current_a.toFixed(1)} A
            </div>
            <div className="text-[10px] text-pebble">Sunlit Wing</div>
          </div>

          {/* Wheel RPM */}
          <div className="p-2.5 rounded bg-void/80 border border-white/5 space-y-1 font-mono">
            <div className="text-[10px] text-pebble uppercase flex items-center justify-between">
              <span>Reaction Wheel</span>
              <RotateCcw className="w-3 h-3 text-sky-400" />
            </div>
            <div className="text-sm font-bold text-bone">
              {ch.adcs_reaction_wheel_rpm} RPM
            </div>
            <div className="text-[10px] text-pebble">Momentum Lock</div>
          </div>

          {/* ADCS Jitter */}
          <div className="p-2.5 rounded bg-void/80 border border-white/5 space-y-1 font-mono">
            <div className="text-[10px] text-pebble uppercase flex items-center justify-between">
              <span>Attitude Jitter</span>
              <Compass className="w-3 h-3 text-emerald-400" />
            </div>
            <div className="text-sm font-bold text-bone">
              {ch.adcs_attitude_jitter_deg.toFixed(4)}°
            </div>
            <div className="text-[10px] text-emerald-400">Pointing Margin</div>
          </div>

          {/* CPU Load */}
          <div className="p-2.5 rounded bg-void/80 border border-white/5 space-y-1 font-mono">
            <div className="text-[10px] text-pebble uppercase flex items-center justify-between">
              <span>OBC CPU Load</span>
              <Cpu className="w-3 h-3 text-pebble" />
            </div>
            <div className="text-sm font-bold text-bone">
              {ch.obc_cpu_load_pct}%
            </div>
            <div className="text-[10px] text-pebble">LEON4 Dual-Core</div>
          </div>
        </div>
      )}
    </div>
  );
}
