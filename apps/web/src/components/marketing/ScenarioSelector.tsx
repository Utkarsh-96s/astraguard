"use client";

import React, { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";

interface ScenarioItem {
  id: string;
  stage_idx: number;
  hour: number;
  name: string;
  description: string;
  expected_level?: string;
}

export function ScenarioSelector() {
  const [scenarios, setScenarios] = useState<ScenarioItem[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const router = useRouter();

  useEffect(() => {
    // Read pre-selected scenario if available
    if (typeof window !== "undefined") {
      const saved = localStorage.getItem("astraguard_demo_scenario");
      if (saved) setSelectedId(saved);
    }

    async function loadScenarios() {
      try {
        const endpoints = [
          "/api/backend/api/v1/demo/scenarios",
          "http://127.0.0.1:8000/api/v1/demo/scenarios",
        ];
        for (const ep of endpoints) {
          try {
            const res = await fetch(ep);
            if (res.ok) {
              const data = await res.json();
              if (Array.isArray(data) && data.length > 0) {
                setScenarios(data);
                return;
              }
            }
          } catch {
            // continue fallback
          }
        }
      } catch {
        // fallback static list if offline
      }

      // Default static catalog fallback
      setScenarios([
        { id: "SCENARIO-01", stage_idx: 0, hour: 0, name: "Nominal Flight Operations", description: "Routine screening active.", expected_level: "NOMINAL" },
        { id: "SCENARIO-02", stage_idx: 1, hour: 5, name: "Reaction Wheel Thermal & Current Drift", description: "Health AI elevates r_h to 0.35.", expected_level: "WATCH" },
        { id: "SCENARIO-03", stage_idx: 2, hour: 10, name: "Debris Conjunction Screening Warning", description: "Foster 2-D Pc rises to 3.5e-5.", expected_level: "WARNING" },
        { id: "SCENARIO-04", stage_idx: 3, hour: 15, name: "Cyclone Flood Detected with Degraded Health Deferral", description: "Secondary EO payloads deferred.", expected_level: "WARNING" },
        { id: "SCENARIO-05", stage_idx: 4, hour: 18, name: "Critical Conjunction Safety Override", description: "Fengyun debris hard override forces CRITICAL.", expected_level: "CRITICAL" },
      ]);
    }

    loadScenarios();
  }, []);

  // Close on outside click
  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    }
    if (isOpen) {
      document.addEventListener("mousedown", handleClickOutside);
    }
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [isOpen]);

  // Close on Escape
  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") {
        setIsOpen(false);
      }
    }
    if (isOpen) {
      document.addEventListener("keydown", handleKeyDown);
    }
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [isOpen]);

  const handleSelect = (scenario: ScenarioItem) => {
    setSelectedId(scenario.id);
    if (typeof window !== "undefined") {
      localStorage.setItem("astraguard_demo_scenario", scenario.id);
      localStorage.setItem("astraguard_demo_stage", String(scenario.stage_idx));
    }
    setIsOpen(false);
    router.push(`/demo?scenario=${encodeURIComponent(scenario.id)}`);
  };

  const currentLabel = selectedId ? selectedId : "SCENARIO";

  return (
    <div ref={containerRef} className="relative inline-block text-left">
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        aria-haspopup="true"
        aria-expanded={isOpen}
        aria-label="Select demo scenario"
        className="inline-flex items-center gap-1.5 border border-space-fg bg-transparent text-space-fg rounded-full px-3.5 py-1.5 text-[11px] font-bold uppercase tracking-[0.10em] leading-none transition-colors duration-200 hover:bg-space-fg/10 focus-visible:outline focus-visible:outline-1 focus-visible:outline-space-fg focus-visible:outline-offset-[3px] select-none"
        style={{ fontFamily: "var(--font-d-din, var(--font-barlow, sans-serif))" }}
      >
        <span>{currentLabel}</span>
        <span className="text-space-secondary text-[9px] select-none" aria-hidden="true">
          {isOpen ? "▲" : "▼"}
        </span>
      </button>

      {isOpen && (
        <div
          role="menu"
          aria-orientation="vertical"
          className="absolute right-0 mt-2 w-72 bg-space-canvas border border-space-separator rounded p-1.5 z-50 flex flex-col gap-1 focus:outline-none"
        >
          <div className="px-3 py-1.5 text-[10px] uppercase font-bold text-space-secondary tracking-[0.10em] border-b border-space-separator">
            SELECT MISSION SCENARIO
          </div>
          {scenarios.map((s) => (
            <button
              key={s.id}
              role="menuitem"
              type="button"
              onClick={() => handleSelect(s)}
              className="w-full text-left px-3 py-2 text-[11px] font-bold uppercase tracking-[0.09em] transition-colors rounded hover:bg-space-fg/10 flex flex-col gap-0.5"
            >
              <div className="flex items-center justify-between w-full">
                <span className="text-space-fg">{s.id}</span>
                {s.expected_level && (
                  <span className="text-[10px] text-space-secondary font-medium">{s.expected_level}</span>
                )}
              </div>
              <span className="text-[10px] font-normal text-space-secondary normal-case truncate max-w-full">
                {s.name}
              </span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
