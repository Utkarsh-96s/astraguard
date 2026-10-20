"use client";

import React, { createContext, useContext, useEffect, useState } from "react";

export interface FeatureFlags {
  // Stage 1: Interactive Core
  fault_injection_lab: boolean;
  phone_alert_bot: boolean;
  counterfactual_explainer: boolean;

  // Stage 2: Orbit
  orbit_twin_3d: boolean;
  maneuver_simulator: boolean;
  conjunction_uncertainty: boolean;

  // Stage 3: Evidence & Trust
  real_event_replay: boolean;
  trust_layer: boolean;
  incident_report: boolean;

  // Stage 4: Scale & Stretch
  fleet_command_center: boolean;
  operator_copilot: boolean;
  observation_optimizer: boolean;

  // Quick Wins
  guided_judge_tour: boolean;
  provenance_reproduce: boolean;
  pipeline_observability: boolean;
  command_palette: boolean;
  voice_announcer: boolean;
  night_ops_theme: boolean;

  [key: string]: boolean;
}

export const DEFAULT_FEATURES: FeatureFlags = {
  // Stage 1
  fault_injection_lab: true,
  phone_alert_bot: true,
  counterfactual_explainer: true,

  // Stage 2
  orbit_twin_3d: true,
  maneuver_simulator: true,
  conjunction_uncertainty: true,

  // Stage 3
  real_event_replay: true,
  trust_layer: true,
  incident_report: true,

  // Stage 4
  fleet_command_center: true,
  operator_copilot: true,
  observation_optimizer: true,

  // Quick Wins
  guided_judge_tour: true,
  provenance_reproduce: true,
  pipeline_observability: true,
  command_palette: true,
  voice_announcer: true,
  night_ops_theme: true,
};

interface FeaturesContextType {
  features: FeatureFlags;
  isLoading: boolean;
  toggleFeature: (flag: string) => void;
  isFeatureEnabled: (flag: string) => boolean;
}

const FeaturesContext = createContext<FeaturesContextType>({
  features: DEFAULT_FEATURES,
  isLoading: false,
  toggleFeature: () => {},
  isFeatureEnabled: () => true,
});

export function FeaturesProvider({ children }: { children: React.ReactNode }) {
  const [features, setFeatures] = useState<FeatureFlags>(DEFAULT_FEATURES);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;
    const fetchFlags = async () => {
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
        const res = await fetch(`${apiUrl}/api/v1/features`, { cache: "no-store" });
        if (res.ok) {
          const data = await res.json();
          if (data && data.flags && isMounted) {
            setFeatures((prev) => ({ ...prev, ...data.flags }));
          }
        }
      } catch {
        // Fall back gracefully to default features for offline safety
      } finally {
        if (isMounted) setIsLoading(false);
      }
    };

    fetchFlags();

    // Support URL param overrides e.g. ?disable=guided_judge_tour
    if (typeof window !== "undefined") {
      const params = new URLSearchParams(window.location.search);
      const disableList = params.get("disable")?.split(",") || [];
      const enableList = params.get("enable")?.split(",") || [];

      if (disableList.length > 0 || enableList.length > 0) {
        setFeatures((prev) => {
          const updated = { ...prev };
          disableList.forEach((f) => {
            if (f in updated) updated[f] = false;
          });
          enableList.forEach((f) => {
            if (f in updated) updated[f] = true;
          });
          return updated;
        });
      }
    }

    return () => {
      isMounted = false;
    };
  }, []);

  const toggleFeature = (flag: string) => {
    setFeatures((prev) => ({
      ...prev,
      [flag]: !prev[flag],
    }));
  };

  const isFeatureEnabled = (flag: string): boolean => {
    return features[flag] ?? false;
  };

  return (
    <FeaturesContext.Provider
      value={{
        features,
        isLoading,
        toggleFeature,
        isFeatureEnabled,
      }}
    >
      {children}
    </FeaturesContext.Provider>
  );
}

export function useFeature(flag: string): boolean {
  const context = useContext(FeaturesContext);
  return context.features[flag] ?? false;
}

export function useFeaturesContext() {
  return useContext(FeaturesContext);
}
