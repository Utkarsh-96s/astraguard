"use client";

import React, { createContext, useContext, useEffect, useState, useCallback } from "react";
import { RiskLevel } from "./types";

export interface AssetRiskSummary {
  id: string;
  name: string;
  norad_id: number;
  type: string;
  tle_epoch?: string | null;
  created_at: string;
  latest_score: number;
  latest_level: RiskLevel;
  active_alerts_count: number;
  last_updated: string;
}

const DEFAULT_ASSETS: AssetRiskSummary[] = [
  {
    id: "SENTINEL-2A",
    name: "Sentinel-2A (Optical MSI)",
    norad_id: 40697,
    type: "Optical Earth Observation",
    latest_score: 84.8,
    latest_level: "CRITICAL",
    active_alerts_count: 6,
    last_updated: new Date().toISOString(),
    created_at: new Date().toISOString(),
  },
  {
    id: "SENTINEL-1A",
    name: "Sentinel-1A (C-SAR Radar)",
    norad_id: 39634,
    type: "Synthetic Aperture Radar",
    latest_score: 12.4,
    latest_level: "NOMINAL",
    active_alerts_count: 0,
    last_updated: new Date().toISOString(),
    created_at: new Date().toISOString(),
  },
  {
    id: "SENTINEL-3A",
    name: "Sentinel-3A (OLCI & SLSTR)",
    norad_id: 41335,
    type: "Ocean & Land Environment",
    latest_score: 28.1,
    latest_level: "NOMINAL",
    active_alerts_count: 0,
    last_updated: new Date().toISOString(),
    created_at: new Date().toISOString(),
  },
];

interface AssetContextType {
  selectedAssetId: string;
  selectedAsset: AssetRiskSummary;
  assets: AssetRiskSummary[];
  isLoading: boolean;
  setSelectedAssetId: (id: string) => void;
  refreshAssets: () => Promise<void>;
}

const AssetContext = createContext<AssetContextType>({
  selectedAssetId: "SENTINEL-2A",
  selectedAsset: DEFAULT_ASSETS[0],
  assets: DEFAULT_ASSETS,
  isLoading: false,
  setSelectedAssetId: () => {},
  refreshAssets: async () => {},
});

export function AssetProvider({ children }: { children: React.ReactNode }) {
  const [selectedAssetId, setSelectedAssetId] = useState<string>("SENTINEL-2A");
  const [assets, setAssets] = useState<AssetRiskSummary[]>(DEFAULT_ASSETS);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const refreshAssets = useCallback(async () => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const res = await fetch(`${apiUrl}/api/v1/assets`, { cache: "no-store" });
      if (res.ok) {
        const data = await res.json();
        if (Array.isArray(data) && data.length > 0) {
          setAssets(data);
        }
      }
    } catch {
      // Fallback graceful degradation for offline mode
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshAssets();
    // Poll every 10 seconds for risk summary updates
    const interval = setInterval(refreshAssets, 10000);
    return () => clearInterval(interval);
  }, [refreshAssets]);

  const selectedAsset =
    assets.find((a) => a.id === selectedAssetId) ||
    assets[0] ||
    DEFAULT_ASSETS[0];

  return (
    <AssetContext.Provider
      value={{
        selectedAssetId,
        selectedAsset,
        assets,
        isLoading,
        setSelectedAssetId,
        refreshAssets,
      }}
    >
      {children}
    </AssetContext.Provider>
  );
}

export function useAsset() {
  return useContext(AssetContext);
}
