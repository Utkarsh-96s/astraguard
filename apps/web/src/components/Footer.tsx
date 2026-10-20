import React from "react";
import { ShieldAlert } from "lucide-react";

export function Footer() {
  return (
    <footer className="mt-auto border-t border-white/10 bg-charcoal/60 backdrop-blur-sm text-ash text-xs py-6">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col md:flex-row items-center justify-between gap-4">
          {/* Advisory Notice */}
          <div className="flex items-start gap-2 max-w-2xl">
            <ShieldAlert className="w-4 h-4 text-arterial shrink-0 mt-0.5" />
            <p className="text-[11px] leading-relaxed text-pebble">
              <strong className="text-bone uppercase tracking-wider">Advisory Protocol:</strong> ASTRA-GUARD delivers decision-support intelligence for satellite operations. All anomaly diagnoses, conjunction warnings, and maneuver advisories require Human-in-the-Loop review. Automated spacecraft command dispatch is disabled.
            </p>
          </div>

          {/* Team & Event Attribution */}
          <div className="text-right text-[11px] font-mono text-pebble whitespace-nowrap">
            <div>
              <span className="text-bone font-semibold">ASTRA-GUARD</span> · Team OMEN
            </div>
            <div className="text-iron">AITHON 2.0 Aerospace & SpaceTech</div>
          </div>
        </div>
      </div>
    </footer>
  );
}
