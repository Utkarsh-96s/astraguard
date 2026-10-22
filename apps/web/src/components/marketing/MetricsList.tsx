"use client";

import React, { useEffect, useState } from "react";

interface ModelRecord {
  id: string;
  name: string;
  type: string;
  data_source?: string;
  metrics?: Record<string, number | boolean | string>;
}

interface DisplayMetric {
  label: string;
  value: string;
  dataset: string;
}

export function MetricsList() {
  const [metrics, setMetrics] = useState<DisplayMetric[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let active = true;

    async function loadModels() {
      try {
        const endpoints = [
          "/api/backend/api/v1/models",
          "http://127.0.0.1:8000/api/v1/models",
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
            // continue fallback
          }
        }

        if (res && res.ok) {
          const models: ModelRecord[] = await res.json();
          if (active && Array.isArray(models)) {
            const parsed: DisplayMetric[] = [];

            // 1. Health model
            const health = models.find((m) => m.id.includes("HEALTH") || m.name.toLowerCase().includes("health"));
            const healthF1 = health?.metrics?.point_f1 !== undefined ? Number(health.metrics.point_f1).toFixed(4) : "NOT YET EVALUATED";
            parsed.push({
              label: "SPACECRAFT HEALTH TELEMETRY / POINT F1",
              value: healthF1,
              dataset: health?.data_source || "NOT YET EVALUATED",
            });

            // 2. Debris model
            const debris = models.find((m) => m.id.includes("DEBRIS") || m.name.toLowerCase().includes("debris"));
            const debrisRoc = debris?.metrics?.roc_auc !== undefined ? Number(debris.metrics.roc_auc).toFixed(4) : "NOT YET EVALUATED";
            parsed.push({
              label: "ORBITAL CONJUNCTION SCREENING / ROC-AUC",
              value: debrisRoc,
              dataset: debris?.data_source || "NOT YET EVALUATED",
            });

            // 3. Disaster model
            const disaster = models.find((m) => m.id.includes("DISASTER") || m.name.toLowerCase().includes("disaster") || m.name.toLowerCase().includes("flood"));
            const disasterIou = disaster?.metrics?.iou !== undefined ? Number(disaster.metrics.iou).toFixed(4) : "NOT YET EVALUATED";
            parsed.push({
              label: "SAR FLOOD SEGMENTATION / MEAN IOU",
              value: disasterIou,
              dataset: disaster?.data_source || "NOT YET EVALUATED",
            });

            // 4. Fusion model
            const fusion = models.find((m) => m.id.includes("FUSION") || m.name.toLowerCase().includes("fusion"));
            const violations = fusion?.metrics?.override_violations !== undefined ? `${fusion.metrics.override_violations} VIOLATIONS` : "NOT YET EVALUATED";
            parsed.push({
              label: "MISSION RISK ENGINE / SAFETY OVERRIDE ACCURACY",
              value: violations,
              dataset: fusion?.data_source || "NOT YET EVALUATED",
            });

            setMetrics(parsed);
            setIsLoading(false);
            return;
          }
        }
      } catch {
        // quiet error
      }

      if (active) {
        // Fallback placeholder with explicit NOT YET EVALUATED markers
        setMetrics([
          { label: "SPACECRAFT HEALTH TELEMETRY / POINT F1", value: "NOT YET EVALUATED", dataset: "NOT YET EVALUATED" },
          { label: "ORBITAL CONJUNCTION SCREENING / ROC-AUC", value: "NOT YET EVALUATED", dataset: "NOT YET EVALUATED" },
          { label: "SAR FLOOD SEGMENTATION / MEAN IOU", value: "NOT YET EVALUATED", dataset: "NOT YET EVALUATED" },
          { label: "MISSION RISK ENGINE / SAFETY OVERRIDE ACCURACY", value: "NOT YET EVALUATED", dataset: "NOT YET EVALUATED" },
        ]);
        setIsLoading(false);
      }
    }

    loadModels();
    return () => {
      active = false;
    };
  }, []);

  return (
    <div
      className="w-full flex flex-col pt-4 select-none tnum transition-colors duration-200"
      style={{ fontFamily: "var(--font-d-din, var(--font-barlow, sans-serif))" }}
    >
      {metrics.map((m, idx) => (
        <div
          key={idx}
          className="py-3.5 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-[12px] uppercase font-bold tracking-[0.09em]"
        >
          <div className="flex flex-col gap-0.5 max-w-sm">
            <span className="text-[#f0f0fa] font-bold">{m.label}</span>
            <span className="text-[11px] text-[#f0f0fa]/80 font-medium normal-case tracking-normal truncate">
              {m.dataset}
            </span>
          </div>
          <span className="text-[#f0f0fa] text-[13px] self-start sm:self-auto font-bold tabular-nums">
            {isLoading ? "NOT YET EVALUATED" : m.value}
          </span>
        </div>
      ))}
    </div>
  );
}
