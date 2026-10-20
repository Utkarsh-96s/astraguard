"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Shield,
  Radio,
  Activity,
  Orbit,
  AlertTriangle,
  Layers,
  PlayCircle,
  Volume2,
  VolumeX,
  Mic,
  MicOff,
  Command,
} from "lucide-react";
import { useAsset } from "../lib/assetContext";
import { ObservabilityWidget } from "./ObservabilityWidget";
import { JudgeTourTriggerButton } from "./JudgeTourOverlay";
import { soundFx } from "../lib/audio";
import { voiceAnnouncer } from "../lib/voice";

export function Navbar({ onStartTour }: { onStartTour?: () => void }) {
  const pathname = usePathname();
  const { selectedAsset } = useAsset();
  const [soundMuted, setSoundMuted] = useState(false);
  const [voiceEnabled, setVoiceEnabled] = useState(true);

  useEffect(() => {
    setSoundMuted(soundFx.getMuted());
    setVoiceEnabled(voiceAnnouncer.getEnabled());
  }, []);

  const toggleSound = () => {
    const next = soundFx.toggleMute();
    setSoundMuted(next);
  };

  const toggleVoice = () => {
    const next = voiceAnnouncer.toggle();
    setVoiceEnabled(next);
  };

  const navLinks = [
    { href: "/", label: "Overview", icon: Shield },
    { href: "/health", label: "Health AI", icon: Activity },
    { href: "/debris", label: "Debris Risk", icon: Orbit },
    { href: "/disaster", label: "Disaster EO", icon: Layers },
    { href: "/alerts", label: "Alerts & HITL", icon: AlertTriangle },
    { href: "/models", label: "Model Registry", icon: Radio },
    { href: "/demo", label: "Demo Player", icon: PlayCircle },
  ];

  // Dynamic asset health status color
  const getLevelColor = (level: string) => {
    switch (level) {
      case "CRITICAL":
        return "bg-red-500 text-red-400 border-red-500/40";
      case "WARNING":
        return "bg-amber-500 text-amber-400 border-amber-500/40";
      case "WATCH":
        return "bg-cyan-400 text-cyan-400 border-cyan-400/40";
      default:
        return "bg-emerald-400 text-emerald-400 border-emerald-500/40";
    }
  };

  const levelColor = getLevelColor(selectedAsset.latest_level);

  return (
    <header className="sticky top-0 z-40 bg-void/90 backdrop-blur-md border-b border-white/10 transition-colors">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo & Platform Name */}
          <div className="flex items-center gap-3">
            <Link href="/" className="flex items-center gap-2 group">
              <div className="w-8 h-8 rounded-nav bg-charcoal border border-white/20 flex items-center justify-center group-hover:border-arterial transition-colors">
                <Shield className="w-4 h-4 text-arterial" />
              </div>
              <div>
                <span className="font-bold tracking-tight text-bone text-base sm:text-lg flex items-center gap-1.5">
                  ASTRA-GUARD
                  <span className="w-1.5 h-1.5 rounded-full bg-arterial inline-block" />
                </span>
                <span className="block text-[9px] uppercase tracking-widest text-ash font-mono -mt-0.5">
                  Space Safety Platform
                </span>
              </div>
            </Link>

            {/* Enriched Satellite Asset Tag */}
            <div className="hidden lg:flex items-center gap-2 px-2.5 py-1 rounded-nav bg-smoke/80 border border-white/10 text-[11px] font-mono">
              <span className={`w-1.5 h-1.5 rounded-full ${levelColor.split(" ")[0]} animate-pulse`} />
              <span className="text-bone font-semibold">{selectedAsset.name}</span>
              <span className="text-iron">|</span>
              <span className="text-ash">NORAD {selectedAsset.norad_id}</span>
              <span className="text-iron">|</span>
              <span className={levelColor.split(" ")[1]}>
                {selectedAsset.latest_level} ({selectedAsset.latest_score.toFixed(1)})
              </span>
            </div>
          </div>

          {/* Nav Links */}
          <nav className="hidden md:flex items-center space-x-1">
            {navLinks.map((link) => {
              const Icon = link.icon;
              const isActive = pathname === link.href;
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-nav text-xs font-medium tracking-nav transition-all ${
                    isActive
                      ? "bg-smoke text-bone border border-white/20 shadow-glass"
                      : "text-ash hover:text-bone hover:bg-white/5"
                  }`}
                >
                  <Icon className={`w-3.5 h-3.5 ${isActive ? "text-arterial" : "text-pebble"}`} />
                  {link.label}
                </Link>
              );
            })}
          </nav>

          {/* Actions & Telemetry Widgets */}
          <div className="flex items-center gap-2">
            {/* Q1 Guided Judge Tour */}
            {onStartTour && <JudgeTourTriggerButton onStartTour={onStartTour} />}

            {/* Q4 Command Palette Trigger */}
            <button
              onClick={() => {
                soundFx.playClickFx();
                window.dispatchEvent(new KeyboardEvent("keydown", { key: "k", ctrlKey: true }));
              }}
              className="hidden lg:flex items-center gap-1.5 px-2.5 py-1 rounded-nav bg-charcoal hover:bg-smoke border border-white/15 text-[11px] font-mono text-ash hover:text-bone transition-colors"
              title="Open Command Palette (Ctrl+K / Cmd+K)"
            >
              <Command className="w-3 h-3 text-cyan-400" />
              <span>⌘K</span>
            </button>

            {/* Q6 Sound FX Toggle */}
            <button
              onClick={toggleSound}
              className={`p-1.5 rounded-nav border transition-colors ${
                soundMuted
                  ? "bg-charcoal border-white/10 text-pebble hover:text-bone"
                  : "bg-smoke border-cyan-500/30 text-cyan-300 hover:border-cyan-500/60"
              }`}
              title={soundMuted ? "Unmute Sound FX (Q6)" : "Mute Sound FX (Q6)"}
            >
              {soundMuted ? <VolumeX className="w-3.5 h-3.5" /> : <Volume2 className="w-3.5 h-3.5 text-cyan-400" />}
            </button>

            {/* Q5 Voice Announcer Toggle */}
            <button
              onClick={toggleVoice}
              className={`p-1.5 rounded-nav border transition-colors ${
                voiceEnabled
                  ? "bg-smoke border-emerald-500/30 text-emerald-300 hover:border-emerald-500/60"
                  : "bg-charcoal border-white/10 text-pebble hover:text-bone"
              }`}
              title={voiceEnabled ? "Voice Announcer Active (Q5)" : "Voice Announcer Muted (Q5)"}
            >
              {voiceEnabled ? <Mic className="w-3.5 h-3.5 text-emerald-400" /> : <MicOff className="w-3.5 h-3.5" />}
            </button>

            {/* Q3 Pipeline Observability */}
            <ObservabilityWidget />

            {/* Live Stream indicator */}
            <div className="flex items-center gap-2 px-2.5 py-1 rounded-nav bg-smoke border border-emerald-500/30 text-[11px] font-mono text-emerald-400">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              <span className="hidden sm:inline">STREAM:</span> LIVE
            </div>
          </div>
        </div>
      </div>

      {/* Mobile nav bar */}
      <div className="md:hidden border-t border-white/5 bg-charcoal px-3 py-2 flex overflow-x-auto space-x-2 scrollbar-none items-center justify-between">
        <div className="flex space-x-2 overflow-x-auto">
          {navLinks.map((link) => {
            const Icon = link.icon;
            const isActive = pathname === link.href;
            return (
              <Link
                key={link.href}
                href={link.href}
                className={`flex items-center gap-1.5 px-2.5 py-1 rounded-nav text-[11px] whitespace-nowrap ${
                  isActive ? "bg-smoke text-bone border border-white/20" : "text-ash"
                }`}
              >
                <Icon className="w-3 h-3 text-arterial" />
                {link.label}
              </Link>
            );
          })}
        </div>
        {onStartTour && (
          <div className="shrink-0 pl-2">
            <JudgeTourTriggerButton onStartTour={onStartTour} />
          </div>
        )}
      </div>
    </header>
  );
}
