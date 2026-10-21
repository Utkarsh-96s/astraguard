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
  ChevronDown,
  Cpu,
} from "lucide-react";
import { useAsset } from "../lib/assetContext";
import { ObservabilityWidget } from "./ObservabilityWidget";
import { JudgeTourTriggerButton } from "./JudgeTourOverlay";
import { soundFx } from "../lib/audio";
import { voiceAnnouncer } from "../lib/voice";

export function Navbar({ onStartTour }: { onStartTour?: () => void }) {
  const pathname = usePathname();
  const { selectedAsset, selectedAssetId, setSelectedAssetId, assets } = useAsset();
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
    { href: "/dashboard", label: "Overview", icon: Shield },
    { href: "/dashboard/health", label: "Health", icon: Activity },
    { href: "/dashboard/debris", label: "Debris", icon: Orbit },
    { href: "/dashboard/disaster", label: "Disaster", icon: Layers },
    { href: "/dashboard/alerts", label: "Alerts", icon: AlertTriangle },
    { href: "/dashboard/models", label: "Models", icon: Radio },
    { href: "/dashboard/explore", label: "Explorer", icon: Cpu },
    { href: "/demo", label: "Demo", icon: PlayCircle },
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
    <header className="sticky top-0 z-40 bg-void/90 backdrop-blur-md border-b border-white/10 transition-colors w-full">
      <div className="w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16 w-full gap-2">
          {/* Logo & Platform Name */}
          <div className="flex items-center gap-2.5 shrink-0">
            <Link href="/" className="flex items-center gap-2 group shrink-0">
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

            {/* Interactive Satellite Asset Switcher */}
            <div className="hidden lg:flex items-center gap-1.5 px-2 py-1 rounded-nav bg-smoke/90 border border-white/15 text-[11px] font-mono hover:border-cyan-500/40 transition-colors shrink-0">
              <span className={`w-2 h-2 rounded-full ${levelColor.split(" ")[0]} animate-pulse shrink-0`} />
              <div className="relative flex items-center">
                <select
                  value={selectedAssetId}
                  onChange={(e) => {
                    setSelectedAssetId(e.target.value);
                    soundFx.playClickFx();
                  }}
                  className="bg-transparent text-bone font-semibold focus:outline-none cursor-pointer pr-4 py-0.5 appearance-none text-xs font-mono"
                  title="Switch active monitored satellite asset"
                >
                  {assets.map((a) => (
                    <option key={a.id} value={a.id} className="bg-charcoal text-bone">
                      {a.id}
                    </option>
                  ))}
                </select>
                <ChevronDown className="w-3 h-3 text-pebble pointer-events-none absolute right-0" />
              </div>
              <span className="text-iron">|</span>
              <span className={`${levelColor.split(" ")[1]} font-bold text-[10px]`}>
                {selectedAsset.latest_level}
              </span>
            </div>
          </div>

          {/* Nav Links (Desktop >= 1024px) */}
          <nav className="hidden lg:flex items-center space-x-0.5 shrink-0">
            {navLinks.map((link) => {
              const Icon = link.icon;
              const isActive = pathname === link.href;
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={`flex items-center gap-1 px-2.5 py-1 rounded-nav text-xs font-medium tracking-nav transition-all whitespace-nowrap ${
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
          <div className="flex items-center gap-1 sm:gap-1.5 shrink-0">
            {/* Q1 Guided Judge Tour */}
            {onStartTour && <JudgeTourTriggerButton onStartTour={onStartTour} />}

            {/* Q4 Command Palette Trigger */}
            <button
              onClick={() => {
                soundFx.playClickFx();
                window.dispatchEvent(new KeyboardEvent("keydown", { key: "k", ctrlKey: true }));
              }}
              className="hidden 2xl:flex items-center gap-1.5 px-2.5 py-1 rounded-nav bg-charcoal hover:bg-smoke border border-white/15 text-[11px] font-mono text-ash hover:text-bone transition-colors"
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
            <div className="flex items-center gap-1.5 px-2 py-1 rounded-nav bg-smoke border border-emerald-500/30 text-[10px] sm:text-[11px] font-mono text-emerald-400">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              <span>LIVE</span>
            </div>
          </div>
        </div>
      </div>

      {/* Sub-navigation bar for screens < 1024px */}
      <div className="lg:hidden border-t border-white/5 bg-charcoal px-3 py-2 flex overflow-x-auto space-x-2 scrollbar-none items-center justify-between">
        <div className="flex space-x-2 overflow-x-auto scrollbar-none">
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
