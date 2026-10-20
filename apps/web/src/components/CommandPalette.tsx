"use client";

import React, { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import {
  Search,
  Activity,
  Orbit,
  Layers,
  AlertTriangle,
  Radio,
  PlayCircle,
  Shield,
  Volume2,
  VolumeX,
  Mic,
  MicOff,
  Compass,
  Zap,
  Sliders,
  Send,
  CornerDownLeft,
  X,
} from "lucide-react";
import { soundFx } from "../lib/audio";
import { voiceAnnouncer } from "../lib/voice";

interface CommandItem {
  id: string;
  category: "Navigation" | "Interactive Labs" | "Controls & Toggles";
  title: string;
  subtitle: string;
  icon: React.ElementType;
  shortcut?: string;
  action: () => void;
}

interface CommandPaletteProps {
  onStartTour?: () => void;
}

export function CommandPalette({ onStartTour }: CommandPaletteProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [soundMuted, setSoundMuted] = useState(false);
  const [voiceEnabled, setVoiceEnabled] = useState(true);
  const router = useRouter();
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    setSoundMuted(soundFx.getMuted());
    setVoiceEnabled(voiceAnnouncer.getEnabled());

    const handleKeyDown = (e: KeyboardEvent) => {
      // Toggle palette on Ctrl+K or Cmd+K
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setIsOpen((prev) => !prev);
        soundFx.playClickFx();
      } else if (e.key === "Escape" && isOpen) {
        setIsOpen(false);
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen]);

  useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 50);
      setSelectedIndex(0);
    } else {
      setQuery("");
    }
  }, [isOpen]);

  const commands: CommandItem[] = [
    // Navigation
    {
      id: "nav-overview",
      category: "Navigation",
      title: "Fleet Overview & Risk Engine",
      subtitle: "Unified Noisy-OR mission risk matrix and 3-factor radar",
      icon: Shield,
      shortcut: "G O",
      action: () => router.push("/"),
    },
    {
      id: "nav-health",
      category: "Navigation",
      title: "Spacecraft Health AI",
      subtitle: "LSTM Autoencoder telemetry reconstruction & persistence filter",
      icon: Activity,
      shortcut: "G H",
      action: () => router.push("/health"),
    },
    {
      id: "nav-debris",
      category: "Navigation",
      title: "Debris Collision Conjunctions",
      subtitle: "SGP4 orbit propagation, TCA refinement & Foster 2-D Pc",
      icon: Orbit,
      shortcut: "G D",
      action: () => router.push("/debris"),
    },
    {
      id: "nav-disaster",
      category: "Navigation",
      title: "Satellite Disaster Earth Observation",
      subtitle: "SAR U-Net flood segmentation & differential damage mapping",
      icon: Layers,
      shortcut: "G E",
      action: () => router.push("/disaster"),
    },
    {
      id: "nav-alerts",
      category: "Navigation",
      title: "Alerts & HITL Command Console",
      subtitle: "Operator action audit trail, approval modal & bot dispatcher",
      icon: AlertTriangle,
      shortcut: "G A",
      action: () => router.push("/alerts"),
    },
    {
      id: "nav-models",
      category: "Navigation",
      title: "Model Registry & Benchmarks",
      subtitle: "Audited performance metrics, data hashes & references",
      icon: Radio,
      shortcut: "G M",
      action: () => router.push("/models"),
    },
    {
      id: "nav-demo",
      category: "Navigation",
      title: "Deterministic Demo Player",
      subtitle: "Replay 'Day in the life of Sentinel-2A' scenario",
      icon: PlayCircle,
      shortcut: "G P",
      action: () => router.push("/demo"),
    },

    // Interactive Labs
    {
      id: "lab-incident-report",
      category: "Interactive Labs",
      title: "Generate Mission Safety Incident Report (F7)",
      subtitle: "Formal printable ECSS/NASA report with cryptographic seal",
      icon: Shield,
      action: () => router.push("/alerts"),
    },
    {
      id: "lab-trust-layer",
      category: "Interactive Labs",
      title: "AI Trust Layer & Calibration Engine (F9)",
      subtitle: "ECE reliability curves, KS-drift hypothesis test, OOD scoring",
      icon: Radio,
      action: () => router.push("/models"),
    },
    {
      id: "lab-sensor-tasking",
      category: "Interactive Labs",
      title: "Ground Sensor Tasking Optimizer (F12)",
      subtitle: "Schedule TIRA & Teide passes to shrink covariance and avoid CAM burns",
      icon: Orbit,
      action: () => router.push("/debris"),
    },
    {
      id: "lab-fault-injection",
      category: "Interactive Labs",
      title: "Fault Injection Lab & Detector Arena (F5)",
      subtitle: "Simulate drift, spike, or stuck sensors & benchmark LSTM vs IsoForest",
      icon: Sliders,
      action: () => router.push("/health#fault-lab"),
    },
    {
      id: "lab-bot-dispatch",
      category: "Interactive Labs",
      title: "Phone Alert Bot & Telegram Dispatcher (F10)",
      subtitle: "Send mission alert to Telegram bot with inline action buttons",
      icon: Send,
      action: () => router.push("/alerts#bot-simulator"),
    },
    {
      id: "lab-judge-tour",
      category: "Interactive Labs",
      title: "Start Guided Judge Tour (Q1)",
      subtitle: "6-step interactive walkthrough of all platform capabilities",
      icon: Compass,
      shortcut: "Shift+?",
      action: () => {
        if (onStartTour) onStartTour();
      },
    },

    // Controls & Toggles
    {
      id: "toggle-sound",
      category: "Controls & Toggles",
      title: soundMuted ? "Unmute Sound FX (Q6)" : "Mute Sound FX (Q6)",
      subtitle: "Web Audio API space telemetry chirps, pings, and alarms",
      icon: soundMuted ? VolumeX : Volume2,
      action: () => {
        const next = soundFx.toggleMute();
        setSoundMuted(next);
      },
    },
    {
      id: "toggle-voice",
      category: "Controls & Toggles",
      title: voiceEnabled ? "Disable Voice Announcer (Q5)" : "Enable Voice Announcer (Q5)",
      subtitle: "Web Speech API synthesized flight controller advisories",
      icon: voiceEnabled ? MicOff : Mic,
      action: () => {
        const next = voiceAnnouncer.toggle();
        setVoiceEnabled(next);
      },
    },
  ];

  const filteredCommands = commands.filter((cmd) => {
    if (!query.trim()) return true;
    const q = query.toLowerCase();
    return (
      cmd.title.toLowerCase().includes(q) ||
      cmd.subtitle.toLowerCase().includes(q) ||
      cmd.category.toLowerCase().includes(q)
    );
  });

  const handleSelect = (cmd: CommandItem) => {
    soundFx.playSuccessChirp();
    setIsOpen(false);
    cmd.action();
  };

  const handleKeyDownInMenu = (e: React.KeyboardEvent) => {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setSelectedIndex((prev) => (prev + 1) % (filteredCommands.length || 1));
      soundFx.playClickFx();
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setSelectedIndex((prev) => (prev - 1 + filteredCommands.length) % (filteredCommands.length || 1));
      soundFx.playClickFx();
    } else if (e.key === "Enter") {
      e.preventDefault();
      if (filteredCommands[selectedIndex]) {
        handleSelect(filteredCommands[selectedIndex]);
      }
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-20 px-4 bg-void/80 backdrop-blur-md animate-in fade-in duration-150">
      <div className="relative w-full max-w-2xl rounded-card bg-charcoal border border-white/20 shadow-2xl overflow-hidden flex flex-col max-h-[75vh]">
        {/* Search Input Bar */}
        <div className="flex items-center px-4 py-3.5 border-b border-white/10 gap-3 bg-smoke/60">
          <Search className="w-5 h-5 text-ash shrink-0" />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setSelectedIndex(0);
            }}
            onKeyDown={handleKeyDownInMenu}
            placeholder="Search commands, pages, or labs... (e.g., 'fault', 'tour', 'bot')"
            className="w-full bg-transparent text-bone placeholder-pebble text-sm font-sans focus:outline-none"
          />
          {query && (
            <button
              onClick={() => setQuery("")}
              className="p-1 text-pebble hover:text-bone text-xs"
            >
              <X className="w-4 h-4" />
            </button>
          )}
          <kbd className="hidden sm:inline-block px-2 py-0.5 rounded bg-void border border-white/15 text-[10px] font-mono text-ash">
            ESC
          </kbd>
        </div>

        {/* Results List */}
        <div className="overflow-y-auto p-2 space-y-1 divide-y divide-white/5 scrollbar-thin scrollbar-thumb-white/10">
          {filteredCommands.length === 0 ? (
            <div className="py-12 text-center text-xs font-mono text-pebble">
              No matching commands or actions found for &quot;{query}&quot;
            </div>
          ) : (
            filteredCommands.map((cmd, idx) => {
              const isSelected = idx === selectedIndex;
              const Icon = cmd.icon;
              return (
                <button
                  key={cmd.id}
                  onClick={() => handleSelect(cmd)}
                  onMouseEnter={() => setSelectedIndex(idx)}
                  className={`w-full text-left px-3 py-2.5 rounded-nav flex items-center justify-between transition-colors ${
                    isSelected
                      ? "bg-smoke text-bone border border-cyan-500/40 shadow-sm"
                      : "text-ash hover:bg-white/5 hover:text-bone border border-transparent"
                  }`}
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <div
                      className={`w-7 h-7 rounded flex items-center justify-center shrink-0 border ${
                        isSelected
                          ? "bg-cyan-950/60 border-cyan-500/50 text-cyan-300"
                          : "bg-void border-white/10 text-ash"
                      }`}
                    >
                      <Icon className="w-3.5 h-3.5" />
                    </div>
                    <div className="min-w-0">
                      <div className="text-xs font-semibold text-bone flex items-center gap-2 truncate">
                        <span>{cmd.title}</span>
                        <span className="text-[10px] font-mono text-pebble uppercase px-1.5 py-0.2 rounded bg-void/60 border border-white/5">
                          {cmd.category}
                        </span>
                      </div>
                      <p className="text-[11px] text-pebble font-mono truncate">{cmd.subtitle}</p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 shrink-0 pl-2">
                    {cmd.shortcut && (
                      <kbd className="px-1.5 py-0.5 rounded bg-void border border-white/10 text-[10px] font-mono text-ash">
                        {cmd.shortcut}
                      </kbd>
                    )}
                    {isSelected && (
                      <CornerDownLeft className="w-3.5 h-3.5 text-cyan-400 animate-pulse" />
                    )}
                  </div>
                </button>
              );
            })
          )}
        </div>

        {/* Footer Navigation Hints */}
        <div className="px-4 py-2 bg-void/90 border-t border-white/10 flex items-center justify-between text-[11px] font-mono text-pebble">
          <div className="flex items-center gap-3">
            <span>
              <kbd className="px-1 rounded bg-charcoal border border-white/10 text-[10px]">↑</kbd>{" "}
              <kbd className="px-1 rounded bg-charcoal border border-white/10 text-[10px]">↓</kbd> to navigate
            </span>
            <span>
              <kbd className="px-1 rounded bg-charcoal border border-white/10 text-[10px]">↵</kbd> to select
            </span>
          </div>
          <div className="flex items-center gap-1.5 text-ash">
            <Zap className="w-3 h-3 text-arterial" />
            <span>ASTRA-GUARD Command Center</span>
          </div>
        </div>
      </div>
    </div>
  );
}
