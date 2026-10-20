import React from "react";

interface SimulatedBadgeProps {
  className?: string;
}

export function SimulatedBadge({ className = "" }: SimulatedBadgeProps) {
  return (
    <span
      className={`inline-flex items-center gap-1 badge-simulated font-mono tracking-wider ${className}`}
      title="Data generated using physics-informed synthetic orbital and sensor generators"
    >
      <span className="w-1.5 h-1.5 rounded-full bg-arterial animate-ping" />
      SIMULATED
    </span>
  );
}
