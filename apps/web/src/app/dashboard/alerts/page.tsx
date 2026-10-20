"use client";

import React, { useEffect, useState } from "react";
import {
  AlertTriangle,
  ShieldCheck,
  Check,
  X,
  BellOff,
  Clock,
  History,
  Send,
  UserCheck,
  FileText,
} from "lucide-react";
import { Alert, AlertStatus, RiskLevel } from "@/lib/types";
import { fetchAlerts, submitOperatorAction, FALLBACK_ALERTS } from "@/lib/api";
import { StatusBadge } from "@/components/StatusBadge";
import { SimulatedBadge } from "@/components/SimulatedBadge";
import { ProvenanceModal } from "@/components/ProvenanceModal";
import { TelegramBotModal } from "@/components/TelegramBotModal";
import { IncidentReportModal } from "@/components/IncidentReportModal";

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<Alert[]>(FALLBACK_ALERTS);
  const [selectedAlert, setSelectedAlert] = useState<Alert | null>(null);
  const [provenanceAlertId, setProvenanceAlertId] = useState<string | null>(null);
  const [botAlertId, setBotAlertId] = useState<string | null>(null);
  const [incidentAlert, setIncidentAlert] = useState<Alert | null>(null);
  const [actionType, setActionType] = useState<"approve" | "dismiss" | "snooze">("approve");
  const [operatorUser, setOperatorUser] = useState("FlightDirector_Sarah");
  const [operatorNote, setOperatorNote] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [levelFilter, setLevelFilter] = useState<string>("ALL");

  const loadAlerts = async () => {
    try {
      const data = await fetchAlerts();
      setAlerts(data);
    } catch (e) {
      console.warn("Failed to fetch alerts:", e);
    }
  };

  useEffect(() => {
    loadAlerts();
  }, []);

  const handleActionSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedAlert) return;

    setSubmitting(true);
    try {
      await submitOperatorAction(selectedAlert.id, operatorUser, actionType, operatorNote);
      // Update local alert state immediately
      setAlerts((prev) =>
        prev.map((a) => {
          if (a.id === selectedAlert.id) {
            const newStatus: AlertStatus =
              actionType === "approve"
                ? "ACKNOWLEDGED"
                : actionType === "dismiss"
                ? "DISMISSED"
                : "SNOOZED";
            const newActions = [
              ...(a.audit_actions || []),
              {
                id: `ACT-${Date.now()}`,
                alert_id: a.id,
                user: operatorUser,
                action: actionType,
                note: operatorNote,
                timestamp: new Date().toISOString(),
              },
            ];
            return { ...a, status: newStatus, audit_actions: newActions };
          }
          return a;
        })
      );
      setSelectedAlert(null);
      setOperatorNote("");
    } catch (err) {
      alert(`Action submission failed: ${err}`);
    } finally {
      setSubmitting(false);
    }
  };

  const filteredAlerts = alerts.filter((a) => {
    if (statusFilter !== "ALL" && a.status !== statusFilter) return false;
    if (levelFilter !== "ALL" && a.level !== levelFilter) return false;
    return true;
  });

  return (
    <div className="space-y-6">
      {/* Title Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-4 rounded-card bg-charcoal border border-white/10">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold tracking-tight text-bone flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-arterial" />
              Operational Alerts & HITL Action Console
            </h1>
            <SimulatedBadge />
          </div>
          <p className="text-xs text-ash font-mono mt-0.5">
            Deduplicated Alert Lifecycle (300s Cooldown) + Immutable Operator Audit Trail
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <button
            onClick={() => setIncidentAlert(alerts[0] || FALLBACK_ALERTS[0])}
            className="px-3 py-1.5 rounded-nav bg-charcoal hover:bg-smoke border border-arterial/50 text-xs font-mono text-red-300 hover:text-white flex items-center gap-1.5 transition-colors"
            title="Generate and print formal mission safety incident report"
          >
            <FileText className="w-3.5 h-3.5 text-arterial" />
            <span>Generate Incident Report (F7)</span>
          </button>

          {/* Advisory Only Badge */}
          <div className="px-3 py-1.5 rounded-nav bg-smoke border border-arterial/40 text-xs font-mono text-red-300 flex items-center gap-1.5">
            <UserCheck className="w-3.5 h-3.5 text-arterial" />
            <span>Human-in-the-Loop Required</span>
          </div>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex flex-wrap items-center justify-between gap-3 p-3 rounded-card bg-charcoal border border-white/10">
        {/* Status Filters */}
        <div className="flex flex-wrap items-center gap-1.5 text-xs font-mono">
          <span className="text-pebble mr-1 text-[11px]">STATUS:</span>
          {["ALL", "ACTIVE", "ACKNOWLEDGED", "DISMISSED", "SNOOZED"].map((st) => (
            <button
              key={st}
              onClick={() => setStatusFilter(st)}
              className={`px-2.5 py-1 rounded-nav text-[11px] transition-colors ${
                statusFilter === st
                  ? "bg-smoke text-bone border border-white/20 font-semibold"
                  : "text-ash hover:text-bone"
              }`}
            >
              {st}
            </button>
          ))}
        </div>

        {/* Severity Filters */}
        <div className="flex flex-wrap items-center gap-1.5 text-xs font-mono">
          <span className="text-pebble mr-1 text-[11px]">SEVERITY:</span>
          {["ALL", "CRITICAL", "WARNING", "WATCH"].map((lvl) => (
            <button
              key={lvl}
              onClick={() => setLevelFilter(lvl)}
              className={`px-2.5 py-1 rounded-nav text-[11px] transition-colors ${
                levelFilter === lvl
                  ? "bg-smoke text-bone border border-white/20 font-semibold"
                  : "text-ash hover:text-bone"
              }`}
            >
              {lvl}
            </button>
          ))}
        </div>
      </div>

      {/* Alerts List */}
      <div className="space-y-4">
        {filteredAlerts.length === 0 ? (
          <div className="p-8 text-center text-xs text-pebble font-mono rounded-card bg-charcoal border border-white/10">
            No alerts match the selected status and severity filters.
          </div>
        ) : (
          filteredAlerts.map((alert) => (
            <div
              key={alert.id}
              className={`p-5 rounded-card bg-charcoal border transition-all space-y-4 ${
                alert.level === "CRITICAL"
                  ? "border-arterial/60 shadow-[0_0_15px_rgba(254,30,52,0.1)]"
                  : "border-white/10"
              }`}
            >
              {/* Alert Header */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-white/10 pb-3">
                <div className="flex items-center gap-3">
                  <StatusBadge level={alert.level} size="md" />
                  <span className="text-sm font-bold font-mono text-bone">{alert.title}</span>
                </div>
                <div className="flex items-center gap-3 font-mono text-xs">
                  <span className="text-pebble">ID: {alert.id}</span>
                  <span
                    className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                      alert.status === "ACTIVE"
                        ? "bg-red-950/40 text-red-400 border border-arterial/40"
                        : alert.status === "ACKNOWLEDGED"
                        ? "bg-emerald-950/40 text-emerald-400 border border-emerald-500/40"
                        : "bg-white/5 text-ash"
                    }`}
                  >
                    {alert.status}
                  </span>
                </div>
              </div>

              {/* Rationale & Recommendation */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                <div className="p-3 rounded bg-void/80 border border-white/5 space-y-1">
                  <span className="text-[10px] font-mono uppercase text-pebble">Safety Rationale:</span>
                  <p className="text-ash font-sans leading-relaxed">{alert.rationale}</p>
                </div>
                <div className="p-3 rounded bg-void/80 border border-white/5 space-y-1">
                  <span className="text-[10px] font-mono uppercase text-pebble">
                    Advisory Recommendation:
                  </span>
                  <p className="text-emerald-300 font-mono font-medium">{alert.recommendation}</p>
                </div>
              </div>

              {/* Audit Actions Log & Action Trigger */}
              <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 pt-2">
                <div className="flex items-center gap-2 text-[11px] font-mono text-pebble">
                  <History className="w-3.5 h-3.5 text-ash" />
                  <span>
                    Audit Actions: {alert.audit_actions?.length || 0} recorded
                  </span>
                  {alert.audit_actions && alert.audit_actions.length > 0 && (
                    <span className="text-bone">
                      (Last by {alert.audit_actions[alert.audit_actions.length - 1].user}: {alert.audit_actions[alert.audit_actions.length - 1].action})
                    </span>
                  )}
                </div>

                <div className="flex flex-wrap items-center gap-2">
                  <button
                    onClick={() => setIncidentAlert(alert)}
                    className="px-3.5 py-1.5 rounded-nav bg-charcoal hover:bg-smoke border border-arterial/40 hover:border-arterial/80 text-xs font-mono font-semibold text-red-300 flex items-center gap-1.5 transition-colors"
                    title="Generate formal mission safety incident report (F7)"
                  >
                    <FileText className="w-3.5 h-3.5 text-arterial" />
                    <span>Incident Report (F7)</span>
                  </button>

                  <button
                    onClick={() => setBotAlertId(alert.id)}
                    className="px-3.5 py-1.5 rounded-nav bg-charcoal hover:bg-smoke border border-sky-500/30 hover:border-sky-500/60 text-xs font-mono font-semibold text-sky-300 flex items-center gap-1.5 transition-colors"
                    title="Open Mobile Telegram Alert Bot Simulator (F10)"
                  >
                    <Send className="w-3.5 h-3.5 text-sky-400" />
                    <span>Telegram Bot (F10)</span>
                  </button>

                  <button
                    onClick={() => setProvenanceAlertId(alert.id)}
                    className="px-3.5 py-1.5 rounded-nav bg-charcoal hover:bg-smoke border border-cyan-500/30 hover:border-cyan-500/60 text-xs font-mono font-semibold text-cyan-300 flex items-center gap-1.5 transition-colors"
                    title="View cryptographic provenance and verify mathematical reproducibility"
                  >
                    <ShieldCheck className="w-3.5 h-3.5 text-cyan-400" />
                    <span>Provenance & Reproduce (Q2)</span>
                  </button>

                  <button
                    onClick={() => setSelectedAlert(alert)}
                    className="px-3.5 py-1.5 rounded-nav bg-smoke hover:bg-white/10 border border-white/20 text-xs font-mono font-semibold text-bone flex items-center gap-1.5 transition-colors"
                  >
                    <UserCheck className="w-3.5 h-3.5 text-arterial" />
                    <span>Take Operator Action</span>
                  </button>
                </div>
              </div>

              {/* Chronological Audit Log Trail if present */}
              {alert.audit_actions && alert.audit_actions.length > 0 && (
                <div className="pt-2 border-t border-white/5 space-y-1.5">
                  <span className="text-[10px] font-mono uppercase text-pebble">
                    Tamper-Evident Operator Audit Trail:
                  </span>
                  <div className="space-y-1">
                    {alert.audit_actions.map((act: any, i: number) => (
                      <div
                        key={i}
                        className="px-2.5 py-1 rounded bg-smoke/40 text-[11px] font-mono flex items-center justify-between text-ash"
                      >
                        <div className="flex items-center gap-2">
                          <span className="text-bone font-semibold">{act.user}</span>
                          <span className="text-iron">&rarr;</span>
                          <span className="text-emerald-400 uppercase font-bold">{act.action}</span>
                          {act.note && (
                            <span className="text-pebble italic">&quot;{act.note}&quot;</span>
                          )}
                        </div>
                        <span className="text-pebble text-[10px]">{new Date(act.timestamp).toLocaleTimeString()}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))
        )}
      </div>

      {/* Operator Action Modal / Drawer */}
      {selectedAlert && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="w-full max-w-lg p-6 rounded-card bg-charcoal border border-white/20 shadow-2xl space-y-5">
            <div className="flex items-center justify-between border-b border-white/10 pb-3">
              <div className="flex items-center gap-2">
                <ShieldCheck className="w-5 h-5 text-arterial" />
                <h3 className="text-base font-bold font-mono text-bone">Record Operator Action</h3>
              </div>
              <button
                onClick={() => setSelectedAlert(null)}
                className="text-pebble hover:text-bone text-sm font-mono"
              >
                ✕
              </button>
            </div>

            <div className="p-3 rounded bg-void text-xs font-mono text-ash space-y-1">
              <div>Alert ID: <span className="text-bone">{selectedAlert.id}</span></div>
              <div>Severity: <span className="text-bone">{selectedAlert.level}</span></div>
              <div className="text-pebble line-clamp-1">{selectedAlert.title}</div>
            </div>

            <form onSubmit={handleActionSubmit} className="space-y-4 text-xs font-mono">
              {/* Operator Callsign */}
              <div className="space-y-1">
                <label className="text-pebble">Operator / Flight Director Callsign:</label>
                <input
                  type="text"
                  value={operatorUser}
                  onChange={(e) => setOperatorUser(e.target.value)}
                  className="w-full px-3 py-2 rounded bg-smoke border border-white/15 text-bone focus:outline-none focus:border-arterial"
                  required
                />
              </div>

              {/* Action Selection */}
              <div className="space-y-1">
                <label className="text-pebble">Authorized Protocol Action:</label>
                <div className="grid grid-cols-3 gap-2">
                  <button
                    type="button"
                    onClick={() => setActionType("approve")}
                    className={`p-2 rounded text-center border font-semibold ${
                      actionType === "approve"
                        ? "bg-emerald-950/60 border-emerald-500 text-emerald-300"
                        : "bg-smoke border-white/10 text-ash"
                    }`}
                  >
                    Acknowledge
                  </button>
                  <button
                    type="button"
                    onClick={() => setActionType("dismiss")}
                    className={`p-2 rounded text-center border font-semibold ${
                      actionType === "dismiss"
                        ? "bg-red-950/60 border-arterial text-red-300"
                        : "bg-smoke border-white/10 text-ash"
                    }`}
                  >
                    Dismiss
                  </button>
                  <button
                    type="button"
                    onClick={() => setActionType("snooze")}
                    className={`p-2 rounded text-center border font-semibold ${
                      actionType === "snooze"
                        ? "bg-amber-950/60 border-amber-500 text-amber-300"
                        : "bg-smoke border-white/10 text-ash"
                    }`}
                  >
                    Snooze (1h)
                  </button>
                </div>
              </div>

              {/* Engineering Note */}
              <div className="space-y-1">
                <label className="text-pebble">Engineering Justification Note:</label>
                <textarea
                  rows={3}
                  value={operatorNote}
                  onChange={(e) => setOperatorNote(e.target.value)}
                  placeholder="e.g., Reviewed thermal subsystem telemetry; payload cooling routine authorized."
                  className="w-full px-3 py-2 rounded bg-smoke border border-white/15 text-bone focus:outline-none focus:border-arterial font-sans text-xs"
                />
              </div>

              {/* Advisory Warning */}
              <div className="p-2.5 rounded bg-void/90 border border-white/5 text-[10px] text-pebble leading-relaxed">
                <strong>Advisory Safety Lock:</strong> Automated maneuver execution is disabled. Submitting this form records an immutable entry into the mission audit database.
              </div>

              {/* Modal Buttons */}
              <div className="flex items-center justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setSelectedAlert(null)}
                  className="px-4 py-2 rounded-nav bg-smoke hover:bg-white/10 border border-white/10 text-ash"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-4 py-2 rounded-nav bg-arterial hover:bg-red-600 font-bold text-white flex items-center gap-1.5 disabled:opacity-50"
                >
                  <Send className="w-3.5 h-3.5" />
                  <span>{submitting ? "Submitting..." : "Submit Audit Entry"}</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Phone Alert Bot (Telegram) Simulator Modal (F10) */}
      {botAlertId && (
        <TelegramBotModal
          alertId={botAlertId}
          onClose={() => setBotAlertId(null)}
          onActionComplete={loadAlerts}
        />
      )}

      {/* Cryptographic Provenance & Mathematical Reproducibility Modal (Q2) */}
      {provenanceAlertId && (
        <ProvenanceModal
          alertId={provenanceAlertId}
          isOpen={true}
          onClose={() => setProvenanceAlertId(null)}
        />
      )}

      {/* Formal Printable Mission Safety Incident Report (F7) */}
      {incidentAlert && (
        <IncidentReportModal
          alert={incidentAlert}
          onClose={() => setIncidentAlert(null)}
        />
      )}
    </div>
  );
}
