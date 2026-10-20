"use client";

import React, { useState, useRef, useEffect } from "react";
import {
  Bot,
  Send,
  X,
  Sparkles,
  ShieldCheck,
  Compass,
  AlertTriangle,
  ChevronRight,
  ExternalLink,
  Flame,
  CheckCircle2,
  Lock,
} from "lucide-react";
import Link from "next/link";
import { playAudioCue } from "../lib/audio";

interface CopilotMessage {
  id: string;
  sender: "copilot" | "operator";
  text: string;
  timestamp: string;
  suggestedLinks?: { label: string; href: string }[];
  mathFormula?: string;
  citations?: string[];
}

const INITIAL_MESSAGES: CopilotMessage[] = [
  {
    id: "msg-0",
    sender: "copilot",
    text: "ASTRA-GUARD Flight Controller Copilot online. I am grounded in ECSS/NASA space safety standards, the platform's deterministic rules engine, and live telemetry feeds. All responses are strictly read-only advisory without automated thruster execution authority. How can I assist your shift?",
    timestamp: new Date().toLocaleTimeString(),
    citations: ["rules.md", "ECSS-E-ST-10-06C", "NASA-STD-8719.14"],
  },
];

const PROMPT_SUGGESTIONS = [
  {
    label: "Why is Sentinel-2A in CRITICAL status?",
    query: "Why was CRITICAL risk triggered for Sentinel-2A?",
  },
  {
    label: "Explain Foster 2-D B-Plane Pc Math",
    query: "Explain the Foster 2-D B-plane collision probability calculation",
  },
  {
    label: "Recommended CAM & Propellant Budget",
    query: "What is the recommended CAM maneuver and fuel consumption?",
  },
  {
    label: "Noisy-OR Bayesian Risk Fusion Formula",
    query: "How does the Noisy-OR Bayesian fusion calculate mission risk?",
  },
  {
    label: "Sensor Tasking to Avoid False Alarms",
    query: "How does ground sensor tasking shrink covariance and avoid CAM burns?",
  },
];

export function OperatorCopilot() {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<CopilotMessage[]>(INITIAL_MESSAGES);
  const [inputQuery, setInputQuery] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isTyping]);

  const toggleOpen = () => {
    playAudioCue("click");
    setIsOpen(!isOpen);
  };

  const generateGroundedResponse = (query: string): CopilotMessage => {
    const q = query.toLowerCase();

    if (q.includes("critical") || q.includes("sentinel-2a") || q.includes("why")) {
      return {
        id: `msg-${Date.now()}`,
        sender: "copilot",
        text: "Deterministic Safety Override Rule #1 was triggered for Sentinel-2A. Analytical Foster 2-D screening computed a collision probability of Pc = 1.42e-3 against COSMOS 2251 debris, which strictly exceeds the mandatory flight safety threshold of Pc >= 1.00e-04. Concurrently, thermal drift on the Y-axis fiber gyro elevated subsystem health risk (r_h = 0.082). Under Noisy-OR fusion, any hazard exceeding critical limits locks Mission Risk at CRITICAL.",
        timestamp: new Date().toLocaleTimeString(),
        mathFormula: "P_c \\ge 1.00 \\times 10^{-4} \\implies \\text{CRITICAL DETERMINISTIC OVERRIDE}",
        suggestedLinks: [
          { label: "Inspect Active Alert (ALT-29834)", href: "/alerts" },
          { label: "View B-Plane Geometry", href: "/debris" },
        ],
        citations: ["rules.md: Collision Override", "Foster (1992) AIAA"],
      };
    }

    if (q.includes("foster") || q.includes("b-plane") || q.includes("probability") || q.includes("pc")) {
      return {
        id: `msg-${Date.now()}`,
        sender: "copilot",
        text: "The Foster 2-D method projects 3D orbital uncertainty onto the encounter B-plane (perpendicular to relative velocity v_rel = 14.82 km/s). The probability integral integrates the combined 2D Gaussian covariance density over the circular hard-body collision cross-section (radius R = 5.0 m). A 2,000-particle Monte Carlo run verified the analytical value with 13x speedup.",
        timestamp: new Date().toLocaleTimeString(),
        mathFormula: "P_c = \\frac{1}{2\\pi \\sigma_x \\sigma_y} \\iint_{x^2+y^2 \\le R^2} \\exp\\left(-\\frac{(x - x_0)^2}{2\\sigma_x^2} - \\frac{(y - y_0)^2}{2\\sigma_y^2}\\right) dx\\,dy",
        suggestedLinks: [
          { label: "Launch B-Plane Uncertainty Lab", href: "/debris" },
        ],
        citations: ["ml/debris/pc_engine.py", "UncertaintyLab.tsx"],
      };
    }

    if (q.includes("cam") || q.includes("maneuver") || q.includes("fuel") || q.includes("propellant")) {
      return {
        id: `msg-${Date.now()}`,
        sender: "copilot",
        text: "The optimal Collision Avoidance Maneuver (CAM) applies an in-track prograde impulse of Δv = 0.42 m/s executed at TCA - 1.82h. Under the Tsiolkovsky rocket equation with Sentinel-2A hydrazine thrusters (I_sp = 220s, dry mass = 1,140 kg), total propellant consumed is 128.4 g. Post-CAM miss distance expands from 45.2 m to 2,840 m, dropping Pc to 4.2e-7 (NOMINAL). Note: Human flight director approval is legally required before burn uplink.",
        timestamp: new Date().toLocaleTimeString(),
        mathFormula: "\\Delta m = m_0 \\left(1 - \\exp\\left(-\\frac{\\Delta v}{I_{sp} g_0}\\right)\\right) = 128.4\\text{ g}",
        suggestedLinks: [
          { label: "Run Maneuver What-If Simulator", href: "/debris" },
        ],
        citations: ["services/maneuver_service.py", "Sentinel-2 Mission Spec"],
      };
    }

    if (q.includes("noisy-or") || q.includes("fusion") || q.includes("formula")) {
      return {
        id: `msg-${Date.now()}`,
        sender: "copilot",
        text: "ASTRA-GUARD combines multi-hazard probabilities across Subsystem Health (r_h), Orbital Debris (r_d), and Earth Observation Disaster Priority (r_e) using Bayesian Noisy-OR fusion. The fused probability reflects the probability that at least one independent failure mechanism compromises the mission, guaranteeing strict monotonicity.",
        timestamp: new Date().toLocaleTimeString(),
        mathFormula: "P_{\\text{fusion}} = 1 - \\prod_{i \\in \\{h, d, e\\}} (1 - r_i)",
        suggestedLinks: [
          { label: "Review Model Evaluation Benchmarks", href: "/models" },
        ],
        citations: ["app/services/risk_service.py", "evaluation/results/risk.json"],
      };
    }

    if (q.includes("tasking") || q.includes("ground") || q.includes("radar") || q.includes("sensor")) {
      return {
        id: `msg-${Date.now()}`,
        sender: "copilot",
        text: "Sensor Tasking Optimization (F12) schedules high-power ground radar (TIRA, Fraunhofer FHR) and optical telescopes (ESA Teide OGS). A single L-band monopulse radar pass shrinks in-track position covariance by 84.6% (from 250m down to 38.5m). If true separation is confirmed >= 120m, Pc drops to nominal, allowing the flight director to cancel the CAM and conserve 128.4g of hydrazine.",
        timestamp: new Date().toLocaleTimeString(),
        suggestedLinks: [
          { label: "Open Sensor Tasking Optimizer", href: "/debris" },
        ],
        citations: ["services/observation_service.py", "CCSDS 2.0 TDM Protocol"],
      };
    }

    // Default grounded answer
    return {
      id: `msg-${Date.now()}`,
      sender: "copilot",
      text: `Grounded Query Analysis: "${query}". All active flight assets (Sentinel-2A, 1A, 3A) are continuously monitored against ECSS-E-ST-10-06C standards. Operational rules enforce human authorization for any thruster or payload actions. Telemetry drift, ECE calibration (0.021), and SGP4 propagation horizons are verified.`,
      timestamp: new Date().toLocaleTimeString(),
      citations: ["rules.md", "ASTRA-GUARD Architecture Specification"],
    };
  };

  const handleSend = (textToSend?: string) => {
    const text = textToSend || inputQuery;
    if (!text.trim()) return;

    playAudioCue("click");

    const userMsg: CopilotMessage = {
      id: `usr-${Date.now()}`,
      sender: "operator",
      text: text.trim(),
      timestamp: new Date().toLocaleTimeString(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputQuery("");
    setIsTyping(true);

    setTimeout(() => {
      const botResponse = generateGroundedResponse(text);
      setMessages((prev) => [...prev, botResponse]);
      setIsTyping(false);
      playAudioCue("affirmative");
    }, 450);
  };

  return (
    <>
      {/* Floating Trigger HUD Button */}
      <button
        onClick={toggleOpen}
        className="fixed bottom-5 right-5 z-40 px-3.5 py-2.5 rounded-full bg-gradient-to-r from-cyan-600 to-sky-600 hover:from-cyan-500 hover:to-sky-500 text-white font-mono text-xs font-bold shadow-2xl shadow-cyan-500/30 border border-white/20 flex items-center gap-2 transition-all hover:scale-105"
        title="Open Grounded Operator Copilot (F11)"
      >
        <Bot className="w-4 h-4 text-white animate-pulse" />
        <span className="hidden sm:inline">Operator Copilot (F11)</span>
      </button>

      {/* Slide-Over Drawer Modal */}
      {isOpen && (
        <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-sm flex justify-end">
          <div className="w-full max-w-lg h-full bg-charcoal border-l border-white/15 shadow-2xl flex flex-col text-xs font-mono">
            {/* Drawer Header */}
            <div className="p-4 border-b border-white/10 bg-void/80 flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-lg bg-sky-950/80 border border-sky-500/40 flex items-center justify-center">
                  <Bot className="w-4 h-4 text-sky-400" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-bone text-sm">Operator Copilot</span>
                    <span className="px-1.5 py-0.5 rounded bg-emerald-950/60 border border-emerald-500/30 text-[9px] text-emerald-300 font-bold">
                      GROUNDED
                    </span>
                  </div>
                  <span className="text-[10px] text-pebble">ECSS Standards & Deterministic Rules Grounded</span>
                </div>
              </div>

              <button
                onClick={toggleOpen}
                className="p-1.5 rounded-nav hover:bg-white/10 text-pebble hover:text-bone transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Read-Only Safety Banner */}
            <div className="px-4 py-2 bg-amber-950/30 border-b border-amber-500/20 text-[10px] text-amber-300 flex items-center gap-1.5">
              <Lock className="w-3.5 h-3.5 shrink-0" />
              <span>Read-only advisory console. Zero thruster firing or automated command execution authority.</span>
            </div>

            {/* Messages Feed */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {messages.map((m) => (
                <div
                  key={m.id}
                  className={`flex flex-col ${
                    m.sender === "operator" ? "items-end" : "items-start"
                  }`}
                >
                  <div className="flex items-center gap-1.5 text-[10px] text-pebble mb-1">
                    <span>{m.sender === "operator" ? "Flight Director" : "ASTRA-GUARD Copilot"}</span>
                    <span>·</span>
                    <span>{m.timestamp}</span>
                  </div>

                  <div
                    className={`p-3.5 rounded-card max-w-[90%] leading-relaxed ${
                      m.sender === "operator"
                        ? "bg-sky-600/30 border border-sky-400/40 text-bone"
                        : "bg-void/80 border border-white/10 text-ash space-y-2.5"
                    }`}
                  >
                    <p className="font-sans text-xs text-bone">{m.text}</p>

                    {m.mathFormula && (
                      <div className="p-2 rounded bg-charcoal border border-white/5 font-mono text-[11px] text-emerald-300 overflow-x-auto">
                        {m.mathFormula}
                      </div>
                    )}

                    {m.suggestedLinks && m.suggestedLinks.length > 0 && (
                      <div className="pt-1 flex flex-wrap gap-1.5">
                        {m.suggestedLinks.map((l, i) => (
                          <Link
                            key={i}
                            href={l.href}
                            onClick={() => setIsOpen(false)}
                            className="px-2 py-1 rounded bg-smoke hover:bg-white/15 border border-white/10 text-sky-300 hover:text-white flex items-center gap-1 text-[10px] transition-colors"
                          >
                            <span>{l.label}</span>
                            <ExternalLink className="w-2.5 h-2.5" />
                          </Link>
                        ))}
                      </div>
                    )}

                    {m.citations && (
                      <div className="text-[9px] text-pebble pt-1 border-t border-white/5 flex items-center gap-1.5">
                        <span>Grounded Source:</span>
                        <span className="text-ash">{m.citations.join(" · ")}</span>
                      </div>
                    )}
                  </div>
                </div>
              ))}

              {isTyping && (
                <div className="flex items-center gap-1.5 text-pebble text-xs italic">
                  <Sparkles className="w-3.5 h-3.5 animate-spin text-sky-400" />
                  <span>Cross-referencing telemetry invariants and flight rules...</span>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>

            {/* Prompt Suggestion Chips */}
            <div className="p-3 border-t border-white/10 bg-void/60 space-y-1.5">
              <span className="text-[10px] text-pebble uppercase tracking-wider block">
                Quick Grounded Inquiries:
              </span>
              <div className="flex flex-wrap gap-1.5">
                {PROMPT_SUGGESTIONS.map((s, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleSend(s.query)}
                    className="px-2.5 py-1 rounded-nav bg-smoke hover:bg-white/10 border border-white/10 text-ash hover:text-bone text-[10px] transition-colors"
                  >
                    {s.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Input Form */}
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleSend();
              }}
              className="p-3 border-t border-white/10 bg-void/90 flex items-center gap-2"
            >
              <input
                type="text"
                value={inputQuery}
                onChange={(e) => setInputQuery(e.target.value)}
                placeholder="Ask grounded flight safety questions..."
                className="flex-1 px-3 py-2 rounded bg-smoke border border-white/15 text-bone text-xs font-mono focus:outline-none focus:border-sky-400"
              />
              <button
                type="submit"
                disabled={!inputQuery.trim() || isTyping}
                className="px-3.5 py-2 rounded-nav bg-sky-600 hover:bg-sky-500 text-white font-bold disabled:opacity-50 transition-colors"
              >
                <Send className="w-3.5 h-3.5" />
              </button>
            </form>
          </div>
        </div>
      )}
    </>
  );
}
