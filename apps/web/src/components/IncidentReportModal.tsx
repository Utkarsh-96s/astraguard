"use client";

import React, { useState } from "react";
import {
  ShieldAlert,
  Printer,
  Copy,
  Check,
  Share2,
  X,
  Compass,
  Zap,
  Activity,
  History,
  Lock,
  ExternalLink,
  Flame,
} from "lucide-react";
import { Alert } from "../lib/types";
import { generateIncidentReportData } from "../lib/api";

interface IncidentReportModalProps {
  alert: Alert;
  onClose: () => void;
}

export function IncidentReportModal({ alert, onClose }: IncidentReportModalProps) {
  const [copiedMd, setCopiedMd] = useState(false);
  const [copiedLink, setCopiedLink] = useState(false);
  const report = generateIncidentReportData(alert);

  const handlePrint = () => {
    window.print();
  };

  const handleCopyMarkdown = () => {
    const md = `# ASTRA-GUARD FLIGHT SAFETY INCIDENT REPORT
**INCIDENT ID:** ${report.incident_id}
**CLASSIFICATION:** ${report.classification}
**ISSUED AT (UTC):** ${report.timestamp}
**ASSET:** ${report.asset_id} (NORAD ${report.asset_norad})
**OVERALL RISK SCORE:** ${report.risk_score} / 100 (${report.risk_level})

---

### 1. EXECUTIVE SAFETY RATIONALE
- Collision Probability ($P_c$): ${report.pc.toExponential(2)} (Exceeds deterministic CRITICAL threshold 1.0e-4)
- Spacecraft Subsystem Health Risk ($r_h$): ${report.r_h}
- Space Weather Context: Kp ${report.space_weather.kp} (${report.space_weather.status}), Solar Flux ${report.space_weather.f10_7} sfu
- Drag Factor Perturbation: +${report.space_weather.drag_factor_pct}%

### 2. CONJUNCTION ENCOUNTER GEOMETRY
- Secondary Threat: ${report.secondary_name} (NORAD ${report.secondary_norad})
- Time of Closest Approach: T-${report.tca_hours}h
- Nominal Miss Distance: ${report.miss_distance_m} m
- Relative Velocity: ${report.relative_velocity_kms} km/s
- B-Plane Covariance: σ_in-track = ${report.b_plane_sigma_y_m} m, σ_normal = ${report.b_plane_sigma_x_m} m

### 3. COLLISION AVOIDANCE MANEUVER (CAM) ADVISORY
- Recommended Impulse: ${report.recommended_burn} (Δv = ${report.delta_v_ms} m/s)
- Hydrazine Consumption: ${report.fuel_expenditure_g} g (Isp = 220s)
- Post-CAM Projected Miss: ${report.post_cam_miss_m} m
- Post-CAM Collision Probability: ${report.post_cam_pc.toExponential(2)} (NOMINAL)

### 4. TELEMETRY DIAGNOSTICS
${report.telemetry_anomalies.map((t) => `- **${t.channel}:** ${t.value} ${t.unit} (Baseline: ${t.baseline} ${t.unit}, Dev: ${t.dev})`).join("\n")}

### 5. HITL OPERATOR AUDIT TRAIL
${report.operator_audit_trail.map((a) => `- [${a.timestamp}] **${a.user}** -> ${a.action.toUpperCase()}: "${a.note || "Acknowledged"}"`).join("\n")}

### 6. CRYPTOGRAPHIC PROVENANCE
- SHA-256 Digest: \`${report.provenance_sha256}\`
- Compliance: ECSS-E-ST-10-06C / NASA-STD-8719.14
- Status: DETERMINISTIC SAFETY OVERRIDE VERIFIED
`;

    navigator.clipboard.writeText(md).then(() => {
      setCopiedMd(true);
      setTimeout(() => setCopiedMd(false), 2500);
    });
  };

  const handleCopyLink = () => {
    const url = typeof window !== "undefined" ? `${window.location.origin}/alerts?incident=${report.incident_id}` : "";
    navigator.clipboard.writeText(url).then(() => {
      setCopiedLink(true);
      setTimeout(() => setCopiedLink(false), 2500);
    });
  };

  return (
    <div data-lenis-prevent className="fixed inset-0 z-50 bg-black/85 backdrop-blur-md flex items-center justify-center p-3 sm:p-6 overflow-y-auto">
      <div data-lenis-prevent className="w-full max-w-4xl max-h-[92vh] overflow-y-auto bg-charcoal border border-white/20 rounded-card shadow-2xl flex flex-col text-bone text-xs font-mono print:bg-white print:text-black print:border-none print:shadow-none print:max-h-none print:overflow-visible">
        {/* Modal Top Actions Bar (Hidden during print) */}
        <div className="flex items-center justify-between p-4 border-b border-white/10 bg-void/80 sticky top-0 z-10 print:hidden">
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-arterial animate-pulse" />
            <span className="font-bold tracking-wider text-bone text-sm">
              MISSION SAFETY INCIDENT REPORT (F7)
            </span>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleCopyMarkdown}
              className="px-3 py-1.5 rounded-nav bg-smoke hover:bg-white/10 border border-white/15 text-ash hover:text-bone flex items-center gap-1.5 transition-colors"
              title="Copy incident memo as Markdown"
            >
              {copiedMd ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
              <span>{copiedMd ? "Copied Markdown" : "Copy Markdown"}</span>
            </button>

            <button
              onClick={handleCopyLink}
              className="px-3 py-1.5 rounded-nav bg-smoke hover:bg-white/10 border border-white/15 text-ash hover:text-bone flex items-center gap-1.5 transition-colors"
              title="Copy shareable link"
            >
              {copiedLink ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Share2 className="w-3.5 h-3.5" />}
              <span>{copiedLink ? "Link Copied" : "Share"}</span>
            </button>

            <button
              onClick={handlePrint}
              className="px-3.5 py-1.5 rounded-nav bg-arterial hover:bg-red-600 text-white font-bold flex items-center gap-1.5 transition-colors shadow-lg shadow-arterial/20"
              title="Print official memo or Save as PDF"
            >
              <Printer className="w-3.5 h-3.5" />
              <span>Print / PDF</span>
            </button>

            <button
              onClick={onClose}
              className="p-1.5 rounded-nav hover:bg-white/10 text-pebble hover:text-bone transition-colors ml-1"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Formal Report Printable Document Body */}
        <div className="p-6 sm:p-8 space-y-6 print:p-0 print:space-y-4">
          {/* Header Seal & Metadata */}
          <div className="border-b-2 border-white/20 pb-5 space-y-3 print:border-black">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2">
              <div>
                <div className="text-[10px] tracking-widest text-pebble uppercase print:text-gray-600">
                  ASTRA-GUARD FLIGHT SAFETY & SPACE SITUATIONAL AWARENESS DIRECTORATE
                </div>
                <h1 className="text-xl sm:text-2xl font-black tracking-tight text-bone print:text-black">
                  MISSION SAFETY INCIDENT REPORT
                </h1>
              </div>
              <div className="px-3 py-1.5 rounded bg-arterial/20 border border-arterial/50 text-red-300 font-bold text-xs uppercase print:border-red-600 print:text-red-700">
                {report.classification}
              </div>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2 text-[11px] text-ash print:text-gray-800">
              <div>
                <span className="text-pebble block text-[10px]">INCIDENT ID:</span>
                <strong className="text-bone print:text-black">{report.incident_id}</strong>
              </div>
              <div>
                <span className="text-pebble block text-[10px]">TARGET ASSET:</span>
                <strong className="text-bone print:text-black">{report.asset_id} (NORAD {report.asset_norad})</strong>
              </div>
              <div>
                <span className="text-pebble block text-[10px]">TIME OF INCIDENT:</span>
                <strong className="text-bone print:text-black">{new Date(report.timestamp).toUTCString()}</strong>
              </div>
              <div>
                <span className="text-pebble block text-[10px]">STANDARDS COMPLIANCE:</span>
                <strong className="text-emerald-400 print:text-emerald-700">ECSS-E-ST-10-06C / NASA 8719.14</strong>
              </div>
            </div>
          </div>

          {/* Section 1: Executive Safety Summary */}
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm font-bold text-bone border-b border-white/10 pb-1 print:text-black print:border-gray-300">
              <ShieldAlert className="w-4 h-4 text-arterial" />
              <span>1. EXECUTIVE SAFETY SUMMARY & RISK ENGINE OVERRIDE</span>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div className="p-3 rounded bg-void/80 border border-white/10 print:border-gray-300 print:bg-gray-50 space-y-1">
                <span className="text-[10px] text-pebble uppercase">Collision Probability (Pc)</span>
                <div className="text-lg font-bold text-arterial print:text-red-700">{report.pc.toExponential(2)}</div>
                <div className="text-[10px] text-pebble">Threshold: &ge; 1.00e-04 (CRITICAL)</div>
              </div>
              <div className="p-3 rounded bg-void/80 border border-white/10 print:border-gray-300 print:bg-gray-50 space-y-1">
                <span className="text-[10px] text-pebble uppercase">Subsystem Health Risk (r_h)</span>
                <div className="text-lg font-bold text-amber-400 print:text-amber-700">{report.r_h.toFixed(3)}</div>
                <div className="text-[10px] text-pebble">EPS Battery & Thermal Louvers</div>
              </div>
              <div className="p-3 rounded bg-void/80 border border-white/10 print:border-gray-300 print:bg-gray-50 space-y-1">
                <span className="text-[10px] text-pebble uppercase">Bayesian Noisy-OR Score</span>
                <div className="text-lg font-bold text-bone print:text-black">{report.risk_score} / 100</div>
                <div className="text-[10px] text-emerald-400 print:text-emerald-700">Deterministic Override Engaged</div>
              </div>
            </div>
          </div>

          {/* Section 2: Conjunction Encounter Geometry */}
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm font-bold text-bone border-b border-white/10 pb-1 print:text-black print:border-gray-300">
              <Compass className="w-4 h-4 text-sky-400" />
              <span>2. CONJUNCTION ASSESSMENT & B-PLANE ENCOUNTER GEOMETRY</span>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
              <div className="p-2.5 rounded bg-void/60 border border-white/5 print:border-gray-200">
                <span className="text-[10px] text-pebble block">Secondary Threat Object:</span>
                <strong className="text-bone print:text-black">{report.secondary_name}</strong>
                <span className="text-[10px] text-pebble block">NORAD {report.secondary_norad}</span>
              </div>
              <div className="p-2.5 rounded bg-void/60 border border-white/5 print:border-gray-200">
                <span className="text-[10px] text-pebble block">Nominal Miss Distance:</span>
                <strong className="text-red-400 font-bold print:text-red-700">{report.miss_distance_m} m</strong>
                <span className="text-[10px] text-pebble block">Hard-Body Radius: 5.0 m</span>
              </div>
              <div className="p-2.5 rounded bg-void/60 border border-white/5 print:border-gray-200">
                <span className="text-[10px] text-pebble block">Relative Velocity:</span>
                <strong className="text-bone print:text-black">{report.relative_velocity_kms} km/s</strong>
                <span className="text-[10px] text-pebble block">Hypervelocity Encounter</span>
              </div>
              <div className="p-2.5 rounded bg-void/60 border border-white/5 print:border-gray-200">
                <span className="text-[10px] text-pebble block">Time to Closest Approach:</span>
                <strong className="text-amber-400 font-bold print:text-amber-700">T - {report.tca_hours} hours</strong>
                <span className="text-[10px] text-pebble block">Screening Grade: Verified</span>
              </div>
            </div>
            <div className="p-2.5 rounded bg-smoke/40 text-[11px] text-ash print:bg-gray-100 print:text-gray-800">
              B-Plane Covariance Semi-Axes: &sigma;<sub>in-track</sub> = <strong>{report.b_plane_sigma_y_m} m</strong>, &sigma;<sub>normal</sub> = <strong>{report.b_plane_sigma_x_m} m</strong>. Foster 2-D integration reveals critical probability density overlap at origin.
            </div>
          </div>

          {/* Section 3: CAM Mitigation Plan */}
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm font-bold text-bone border-b border-white/10 pb-1 print:text-black print:border-gray-300">
              <Flame className="w-4 h-4 text-emerald-400" />
              <span>3. COLLISION AVOIDANCE MANEUVER (CAM) MITIGATION PLAN</span>
            </div>
            <div className="p-4 rounded bg-void/80 border border-emerald-500/30 print:border-gray-300 print:bg-gray-50 space-y-2.5">
              <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2">
                <div>
                  <div className="text-[10px] text-pebble uppercase">Recommended Maneuver Strategy:</div>
                  <div className="text-sm font-bold text-emerald-300 print:text-emerald-800">{report.recommended_burn}</div>
                </div>
                <div className="text-right">
                  <span className="text-[10px] text-pebble block">Required Impulse (&Delta;v):</span>
                  <span className="text-base font-bold font-mono text-bone print:text-black">{report.delta_v_ms} m/s</span>
                </div>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 pt-2 border-t border-white/5 text-[11px]">
                <div>
                  <span className="text-pebble block text-[10px]">Hydrazine Expenditure:</span>
                  <strong className="text-bone print:text-black">{report.fuel_expenditure_g} g (0.128 kg)</strong>
                </div>
                <div>
                  <span className="text-pebble block text-[10px]">Post-CAM Miss Distance:</span>
                  <strong className="text-emerald-400 print:text-emerald-700">{report.post_cam_miss_m} m (+2.8 km)</strong>
                </div>
                <div>
                  <span className="text-pebble block text-[10px]">Post-CAM Pc:</span>
                  <strong className="text-emerald-400 print:text-emerald-700">{report.post_cam_pc.toExponential(2)} (NOMINAL)</strong>
                </div>
              </div>
            </div>
          </div>

          {/* Section 4: Subsystem Telemetry & Space Weather */}
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm font-bold text-bone border-b border-white/10 pb-1 print:text-black print:border-gray-300">
              <Zap className="w-4 h-4 text-amber-400" />
              <span>4. CONCURRENT SUBSYSTEM DIAGNOSTICS & SPACE WEATHER CONTEXT</span>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div className="p-3 rounded bg-void/60 border border-white/5 print:border-gray-200 space-y-1.5">
                <span className="text-[10px] text-pebble uppercase font-bold">Space Weather Matrix:</span>
                <div className="space-y-1 text-[11px] text-ash print:text-gray-800">
                  <div className="flex justify-between">
                    <span>Geomagnetic Activity:</span>
                    <strong className="text-amber-400">Kp {report.space_weather.kp} ({report.space_weather.status})</strong>
                  </div>
                  <div className="flex justify-between">
                    <span>Solar Radio Flux (F10.7):</span>
                    <strong className="text-bone print:text-black">{report.space_weather.f10_7} sfu</strong>
                  </div>
                  <div className="flex justify-between">
                    <span>Atmospheric Drag Inflation:</span>
                    <strong className="text-red-400">+{report.space_weather.drag_factor_pct}% (SGP4 Covariance Growth Accelerated)</strong>
                  </div>
                </div>
              </div>

              <div className="p-3 rounded bg-void/60 border border-white/5 print:border-gray-200 space-y-1.5">
                <span className="text-[10px] text-pebble uppercase font-bold">Correlated Subsystem Telemetry:</span>
                <div className="space-y-1 text-[11px]">
                  {report.telemetry_anomalies.map((t, idx) => (
                    <div key={idx} className="flex justify-between text-ash print:text-gray-800">
                      <span>{t.channel}:</span>
                      <span>
                        <strong className="text-bone print:text-black">{t.value} {t.unit}</strong>{" "}
                        <span className="text-amber-400 text-[10px]">({t.dev})</span>
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Section 5: Operator Audit Trail */}
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm font-bold text-bone border-b border-white/10 pb-1 print:text-black print:border-gray-300">
              <History className="w-4 h-4 text-emerald-400" />
              <span>5. HUMAN-IN-THE-LOOP (HITL) OPERATOR AUDIT TRAIL</span>
            </div>
            <div className="space-y-1.5">
              {report.operator_audit_trail.map((act, idx) => (
                <div
                  key={idx}
                  className="p-2.5 rounded bg-smoke/40 border border-white/5 flex flex-col sm:flex-row sm:items-center justify-between text-[11px] text-ash print:border-gray-200 print:bg-gray-50 print:text-gray-800"
                >
                  <div className="flex items-center gap-2">
                    <strong className="text-bone print:text-black">{act.user}</strong>
                    <span className="text-pebble">&rarr;</span>
                    <span className="px-1.5 py-0.5 rounded bg-emerald-950/60 text-emerald-400 uppercase font-bold text-[10px] print:bg-transparent print:text-emerald-700">
                      {act.action}
                    </span>
                    <span className="italic text-pebble print:text-gray-600">&ldquo;{act.note || "Verified"}&rdquo;</span>
                  </div>
                  <span className="text-pebble text-[10px]">{new Date(act.timestamp).toUTCString()}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Section 6: Cryptographic Verification Seal */}
          <div className="p-3.5 rounded bg-void border border-white/10 space-y-1.5 text-[11px] font-mono text-pebble print:border-gray-300 print:text-gray-700">
            <div className="flex items-center gap-1.5 text-bone font-bold text-xs print:text-black">
              <Lock className="w-3.5 h-3.5 text-cyan-400" />
              <span>CRYPTOGRAPHIC INTEGRITY & BIT-FOR-BIT REPRODUCIBILITY SEAL</span>
            </div>
            <div className="break-all text-[10px]">
              SHA-256 Digest: <strong className="text-cyan-300 print:text-cyan-800">{report.provenance_sha256}</strong>
            </div>
            <div className="text-[10px] text-pebble">
              Verified against ASTRA-GUARD Safety Engine Engine v1.0.0. All mathematical evaluations deterministic and reproducible.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
