import React from "react";
import { RiskLevel } from "../lib/types";
import { StatusBadge } from "./StatusBadge";

interface RiskGaugeProps {
  score: number;
  level: RiskLevel;
  size?: number;
}

export function RiskGauge({ score, level, size = 240 }: RiskGaugeProps) {
  const clampedScore = Math.min(100, Math.max(0, score));

  // Semicircle gauge: angle from -180 to 0 degrees (or -90 to 90)
  // Radius and circumference
  const strokeWidth = 16;
  const radius = (size - strokeWidth * 2) / 2;
  const cx = size / 2;
  const cy = size / 2 + 20;

  // Semicircular arc length
  const arcLength = Math.PI * radius;
  const strokeDashoffset = arcLength - (clampedScore / 100) * arcLength;

  let strokeColor = "#10b981"; // Emerald
  let glowColor = "rgba(16, 185, 129, 0.4)";
  if (level === "WATCH") {
    strokeColor = "#f59e0b"; // Amber
    glowColor = "rgba(245, 158, 11, 0.4)";
  } else if (level === "WARNING") {
    strokeColor = "#f97316"; // Orange
    glowColor = "rgba(249, 115, 22, 0.5)";
  } else if (level === "CRITICAL") {
    strokeColor = "#fe1e34"; // Arterial Red
    glowColor = "rgba(254, 30, 52, 0.6)";
  }

  return (
    <div className="flex flex-col items-center justify-center p-4">
      <div className="relative" style={{ width: size, height: size * 0.65 }}>
        <svg
          width={size}
          height={size * 0.65}
          viewBox={`0 0 ${size} ${size * 0.65}`}
          className="overflow-visible"
        >
          <defs>
            <filter id={`glow-${level}`} x="-20%" y="-20%" width="140%" height="140%">
              <feDropShadow dx="0" dy="0" stdDeviation="6" floodColor={glowColor} />
            </filter>
          </defs>

          {/* Background Arc */}
          <path
            d={`M ${strokeWidth} ${cy} A ${radius} ${radius} 0 0 1 ${size - strokeWidth} ${cy}`}
            fill="none"
            stroke="#262525"
            strokeWidth={strokeWidth}
            strokeLinecap="round"
          />

          {/* Value Arc */}
          <path
            d={`M ${strokeWidth} ${cy} A ${radius} ${radius} 0 0 1 ${size - strokeWidth} ${cy}`}
            fill="none"
            stroke={strokeColor}
            strokeWidth={strokeWidth}
            strokeDasharray={arcLength}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            filter={`url(#glow-${level})`}
            className="transition-all duration-700 ease-out"
          />
        </svg>

        {/* Center Readout */}
        <div className="absolute inset-0 flex flex-col items-center justify-end pb-2">
          <div className="text-4xl font-extrabold tracking-tight text-bone font-mono">
            {clampedScore.toFixed(1)}
          </div>
          <div className="text-[10px] uppercase font-mono tracking-widest text-ash">
            Score / 100
          </div>
        </div>
      </div>

      <div className="mt-2 flex flex-col items-center gap-1.5">
        <StatusBadge level={level} size="lg" />
        <span className="text-[10px] text-pebble font-mono">
          R_mission = 100 × (0.85·R_safety + 0.15·r_e)
        </span>
      </div>
    </div>
  );
}
