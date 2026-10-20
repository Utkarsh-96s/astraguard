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

const DEFAULT_ASSET: AssetRiskSummary = {
  id: "SENTINEL-2A",
  name: "SENTINEL-2A",
  norad_id: 40697,
  type: "satellite",
  latest_score: 6.5,
  latest_level: "NOMINAL",
  active_alerts_count: 0,
  last_updated: new Date().toISOString(),
  created_at: new Date().toISOString(),
};

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
  selectedAsset: DEFAULT_ASSET,
  assets: [DEFAULT_ASSET],
  isLoading: false,
  setSelectedAssetId: () => {},
  refreshAssets: async () => {},
});

export function AssetProvider({ children }: { children: React.ReactNode }) {
  const [selectedAssetId, setSelectedAssetId] = useState<string>("SENTINEL-2A");
  const [assets, setAssets] = useState<AssetRiskSummary[]>([DEFAULT_ASSET]);
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
    DEFAULT_ASSET;

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
