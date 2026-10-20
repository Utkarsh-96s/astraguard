"use client";

import React, { useEffect, useState } from "react";

interface RiskData {
  asset_id: string;
  score: number;
  level: string;
  synthetic?: boolean;
}

export function TelemetryStrip() {
  const [data, setData] = useState<RiskData | null>(null);
  const [isStandby, setIsStandby] = useState(false);
  const [utcTime, setUtcTime] = useState<string>("00:00:00");

  // Keep live UTC clock ticking
  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      const h = String(now.getUTCHours()).padStart(2, "0");
      const m = String(now.getUTCMinutes()).padStart(2, "0");
      const s = String(now.getUTCSeconds()).padStart(2, "0");
      setUtcTime(`${h}:${m}:${s}`);
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  // Fetch telemetry & subscribe to WebSocket
  useEffect(() => {
    let active = true;

    async function fetchLatest() {
      try {
        const endpoints = [
          "/api/backend/api/v1/risk/ASTRA-SAT-1/latest",
          "http://127.0.0.1:8000/api/v1/risk/ASTRA-SAT-1/latest",
        ];
        let res: Response | null = null;
        for (const ep of endpoints) {
          try {
            const r = await fetch(ep, { cache: "no-store" });
            if (r.ok) {
              res = r;
              break;
            }
          } catch {
            // try next
          }
        }

        if (res && res.ok) {
          const json = await res.json();
          if (active) {
            setData(json);
            setIsStandby(false);
          }
        } else if (active) {
          setIsStandby(true);
        }
      } catch {
        if (active) {
          setIsStandby(true);
        }
      }
    }

    fetchLatest();
    const pollInterval = setInterval(fetchLatest, 10000);

    // Optional WebSocket connection
    let ws: WebSocket | null = null;
    try {
      const wsUrl = "ws://127.0.0.1:8000/ws/risk/ASTRA-SAT-1";
      ws = new WebSocket(wsUrl);
      ws.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          if (payload && payload.score !== undefined && active) {
            setData(payload);
            setIsStandby(false);
          }
        } catch {
          // ignore malformed ws frames
        }
      };
      ws.onerror = () => {
        // quiet fallback to poll
      };
    } catch {
      // ws not available
    }

    return () => {
      active = false;
      clearInterval(pollInterval);
      if (ws) ws.close();
    };
  }, []);

  const assetName = data?.asset_id || "ASTRA-SAT-1";
  const rawScore = data?.score !== undefined ? Math.round(data.score) : null;
  const scoreFormatted = rawScore !== null ? String(rawScore).padStart(2, "0") : "--";
  const riskLevel = data?.level ? data.level.toUpperCase() : "STANDBY";
  const isSimulated = data?.synthetic === true;

  return (
    <div
      aria-live="polite"
      className="w-full pt-4 border-t border-[#404040] flex flex-wrap items-center gap-x-4 gap-y-2 text-[11px] uppercase font-bold tracking-[0.10em] select-none tnum"
      style={{ fontFamily: "var(--font-d-din, var(--font-barlow, sans-serif))" }}
    >
      <div className="flex items-center gap-1.5">
        <span className="text-[#545457]">ASSET</span>
        <span className="text-[#404040]">/</span>
        <span className="text-[#f0f0fa]">{assetName}</span>
      </div>

      <div className="flex items-center gap-1.5">
        <span className="text-[#545457]">MISSION RISK</span>
        <span className="text-[#404040]">/</span>
        <span className="text-[#f0f0fa]">{isStandby ? "STANDBY" : scoreFormatted}</span>
      </div>

      <div className="flex items-center gap-1.5">
        <span className="text-[#545457]">LEVEL</span>
        <span className="text-[#404040]">/</span>
        <span className="text-[#f0f0fa]">{isStandby ? "STANDBY" : riskLevel}</span>
      </div>

      <div className="flex items-center gap-1.5">
        <span className="text-[#545457]">UTC</span>
        <span className="text-[#404040]">/</span>
        <span className="text-[#f0f0fa]">{utcTime}</span>
      </div>

      {isSimulated && (
        <div className="flex items-center gap-1.5">
          <span className="text-[#404040]">/</span>
          <span className="text-[#f0f0fa] border border-[#404040] rounded px-1.5 py-0.5 text-[9px] leading-none">
            SIMULATED
          </span>
        </div>
      )}
    </div>
  );
}
