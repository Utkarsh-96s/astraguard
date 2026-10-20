import React from "react";
import { RiskDriver } from "../lib/types";

interface DriversListProps {
  drivers: RiskDriver[];
}

export function DriversList({ drivers }: DriversListProps) {
  if (!drivers || drivers.length === 0) {
    return (
      <div className="text-xs text-pebble italic py-3 text-center">
        No active anomalous risk drivers detected. All channels nominal.
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {drivers.map((d, idx) => {
        let moduleColor = "text-sky-400 bg-sky-950/40 border-sky-800/40";
        let barColor = "bg-sky-400";
        if (d.module === "debris") {
          moduleColor = "text-rose-400 bg-rose-950/40 border-rose-800/40";
          barColor = "bg-arterial";
        } else if (d.module === "disaster") {
          moduleColor = "text-amber-400 bg-amber-950/40 border-amber-800/40";
          barColor = "bg-amber-400";
        }

        const share = Math.min(100, Math.max(0, d.share_pct || d.contribution * 100));

        return (
          <div key={`${d.driver}-${idx}`} className="p-2.5 rounded-card bg-smoke/40 border border-white/5 space-y-1.5">
            <div className="flex items-center justify-between text-xs">
              <div className="flex items-center gap-2">
                <span className={`text-[10px] font-mono uppercase px-1.5 py-0.5 rounded border ${moduleColor}`}>
                  {d.module}
                </span>
                <span className="font-mono text-bone font-medium">{d.driver}</span>
              </div>
              <div className="flex items-center gap-2 font-mono text-[11px]">
                <span className="text-bone font-semibold">{share.toFixed(1)}%</span>
                <span className="text-pebble">share</span>
              </div>
            </div>

            {/* Contribution bar */}
            <div className="w-full h-1.5 bg-black/60 rounded-full overflow-hidden">
              <div
                className={`h-full ${barColor} rounded-full transition-all duration-500`}
                style={{ width: `${share}%` }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}
