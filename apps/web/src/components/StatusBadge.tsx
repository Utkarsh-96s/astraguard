import React from "react";
import { RiskLevel } from "../lib/types";

interface StatusBadgeProps {
  level: RiskLevel | string;
  size?: "sm" | "md" | "lg";
}

export function StatusBadge({ level, size = "md" }: StatusBadgeProps) {
  const norm = level.toUpperCase();

  let colorClasses = "bg-emerald-950/40 text-emerald-400 border-emerald-500/40";
  let dotClass = "bg-emerald-400 shadow-[0_0_8px_#34d399]";

  if (norm === "WATCH") {
    colorClasses = "bg-amber-950/40 text-amber-300 border-amber-500/40";
    dotClass = "bg-amber-300 shadow-[0_0_8px_#fcd34d]";
  } else if (norm === "WARNING") {
    colorClasses = "bg-orange-950/40 text-orange-400 border-orange-500/50";
    dotClass = "bg-orange-400 shadow-[0_0_8px_#fb923c]";
  } else if (norm === "CRITICAL") {
    colorClasses = "bg-red-950/50 text-red-400 border-arterial";
    dotClass = "bg-arterial shadow-[0_0_10px_#fe1e34]";
  }

  const sizeClasses =
    size === "sm"
      ? "text-[10px] px-2 py-0.5 tracking-wider font-semibold"
      : size === "lg"
      ? "text-xs px-3.5 py-1 tracking-widest font-bold"
      : "text-[11px] px-2.5 py-0.5 tracking-widest font-semibold";

  return (
    <span
      className={`inline-flex items-center gap-1.5 uppercase rounded-nav border ${colorClasses} ${sizeClasses}`}
    >
      <span className={`w-1.5 h-1.5 rounded-full ${dotClass} animate-pulse`} />
      {norm}
    </span>
  );
}
