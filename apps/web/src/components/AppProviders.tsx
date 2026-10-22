"use client";

import React, { useState } from "react";
import { FeaturesProvider } from "../lib/features";
import { TimeProvider } from "../lib/timeContext";
import { AssetProvider } from "../lib/assetContext";
import { Navbar } from "./Navbar";
import { JudgeTourOverlay } from "./JudgeTourOverlay";
import { CommandPalette } from "./CommandPalette";
import { OperatorCopilot } from "./OperatorCopilot";

export function AppProviders({ children }: { children: React.ReactNode }) {
  const [isTourOpen, setIsTourOpen] = useState(false);

  return (
    <FeaturesProvider>
      <TimeProvider>
        <AssetProvider>
          <Navbar onStartTour={() => setIsTourOpen(true)} />
          <main className="flex-1 w-full px-[clamp(16px,2vw,40px)] py-6">
            {children}
          </main>
          <JudgeTourOverlay isOpen={isTourOpen} onClose={() => setIsTourOpen(false)} />
          <CommandPalette onStartTour={() => setIsTourOpen(true)} />
          <OperatorCopilot />
        </AssetProvider>
      </TimeProvider>
    </FeaturesProvider>
  );
}
