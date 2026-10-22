"use client";

import React, { useEffect, useState } from "react";
import {
  Bell,
  CheckCircle2,
  AlertTriangle,
  X,
  Send,
  Smartphone,
  Mail,
  Globe,
  MessageSquare,
  ShieldAlert,
  Clock,
  RefreshCw,
  Plus,
  Trash2,
  ExternalLink,
  Layers,
  Archive,
} from "lucide-react";
import {
  NotificationHealthResponse,
  NotificationChannelItem,
  EscalationPolicyItem,
  DeadLetterItem,
} from "@/lib/types";
import {
  fetchNotificationHealth,
  fetchNotificationChannels,
  createNotificationChannel,
  deleteNotificationChannel,
  verifyNotificationChannel,
  testNotificationChannel,
  fetchEscalationPolicies,
  createEscalationPolicy,
  fetchDeadLetterQueue,
  retryDeadLetter,
  fireTestAlert,
} from "@/lib/api";

interface NotificationSettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  operatorUser?: string;
}

export function NotificationSettingsModal({
  isOpen,
  onClose,
  operatorUser = "FlightDirector",
}: NotificationSettingsModalProps) {
  const [activeTab, setActiveTab] = useState<"providers" | "channels" | "escalation" | "dlq">("providers");
  const [loading, setLoading] = useState(false);
  const [health, setHealth] = useState<NotificationHealthResponse | null>(null);
  const [channels, setChannels] = useState<NotificationChannelItem[]>([]);
  const [policies, setPolicies] = useState<EscalationPolicyItem[]>([]);
  const [dlq, setDlq] = useState<DeadLetterItem[]>([]);

  // Add channel form state
  const [newChName, setNewChName] = useState("");
  const [newChType, setNewChType] = useState("email");
  const [newChAddress, setNewChAddress] = useState("");
  const [formSubmitting, setFormSubmitting] = useState(false);
  const [statusMessage, setStatusMessage] = useState<{ text: string; error?: boolean } | null>(null);

  // Escalation policy form state
  const [l2DelaySec, setL2DelaySec] = useState(300);
  const [l3DelaySec, setL3DelaySec] = useState(900);

  const loadAll = React.useCallback(async () => {
    setLoading(true);
    try {
      const [h, ch, pol, dead] = await Promise.all([
        fetchNotificationHealth().catch(() => null),
        fetchNotificationChannels(operatorUser).catch(() => []),
        fetchEscalationPolicies().catch(() => []),
        fetchDeadLetterQueue().catch(() => []),
      ]);
      if (h) setHealth(h);
      setChannels(ch);
      setPolicies(pol);
      setDlq(dead);
      if (pol.length > 0) {
        setL2DelaySec(pol[0].l2_delay_sec);
        setL3DelaySec(pol[0].l3_delay_sec);
      }
    } finally {
      setLoading(false);
    }
  }, [operatorUser]);

  useEffect(() => {
    if (isOpen) {
      loadAll();
      setStatusMessage(null);
    }
  }, [isOpen, loadAll]);

  if (!isOpen) return null;

  const handleCreateChannel = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newChName || !newChAddress) return;
    setFormSubmitting(true);
    setStatusMessage(null);
    try {
      await createNotificationChannel({
        name: newChName,
        type: newChType,
        address: newChAddress,
        user_id: operatorUser,
      });
      setStatusMessage({ text: `Channel "${newChName}" created successfully.` });
      setNewChName("");
      setNewChAddress("");
      await loadAll();
    } catch (err: any) {
      setStatusMessage({ text: `Failed to create channel: ${err.message}`, error: true });
    } finally {
      setFormSubmitting(false);
    }
  };

  const handleDeleteChannel = async (id: string) => {
    if (!confirm("Are you sure you want to delete this notification channel?")) return;
    try {
      await deleteNotificationChannel(id);
      setChannels((prev) => prev.filter((c) => c.id !== id));
      setStatusMessage({ text: "Channel deleted." });
    } catch (err: any) {
      setStatusMessage({ text: `Delete failed: ${err.message}`, error: true });
    }
  };

  const handleTestChannel = async (id: string) => {
    setStatusMessage({ text: "Dispatching verification test notification..." });
    try {
      const res = await testNotificationChannel(id);
      if (res.status === "delivered") {
        setStatusMessage({ text: `Delivery verified! Provider message ID: ${res.provider_message_id || "OK"}` });
      } else {
        setStatusMessage({ text: `Test failed: ${res.error}`, error: true });
      }
      await loadAll();
    } catch (err: any) {
      setStatusMessage({ text: `Test failed: ${err.message}`, error: true });
    }
  };

  const handleSavePolicy = async () => {
    setFormSubmitting(true);
    try {
      await createEscalationPolicy({
        name: "Mission Default Escalation Policy",
        l1_channels: ["telegram", "webpush", "ntfy"],
        l2_delay_sec: Number(l2DelaySec),
        l2_channels: ["email", "sms"],
        l3_delay_sec: Number(l3DelaySec),
        l3_channels: ["webhook", "sms"],
      });
      setStatusMessage({ text: "Escalation policy updated and persisted." });
      await loadAll();
    } catch (err: any) {
      setStatusMessage({ text: `Failed to update policy: ${err.message}`, error: true });
    } finally {
      setFormSubmitting(false);
    }
  };

  const handleRetryDlq = async (outboxId: string) => {
    try {
      await retryDeadLetter(outboxId);
      setStatusMessage({ text: `Outbox delivery ${outboxId} requeued for immediate retry.` });
      await loadAll();
    } catch (err: any) {
      setStatusMessage({ text: `Retry failed: ${err.message}`, error: true });
    }
  };

  const handleTriggerSimulatedAlert = async () => {
    setStatusMessage({ text: "Firing simulated test alert through outbox..." });
    try {
      const res = await fireTestAlert("CRITICAL", "SENTINEL-2A");
      setStatusMessage({
        text: `Simulated alert ${res.alert.id} fired! ${res.outbox_deliveries_queued} outbox deliveries queued.`,
      });
      await loadAll();
    } catch (err: any) {
      setStatusMessage({ text: `Test alert failed: ${err.message}`, error: true });
    }
  };

  const renderStatusBadge = (status: string) => {
    switch (status.toUpperCase()) {
      case "CONNECTED":
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-bold font-mono bg-emerald-950/60 border border-emerald-500/50 text-emerald-300 flex items-center gap-1">
            <CheckCircle2 className="w-2.5 h-2.5 text-emerald-400" />
            CONNECTED
          </span>
        );
      case "PENDING VERIFICATION":
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-bold font-mono bg-amber-950/60 border border-amber-500/50 text-amber-300 flex items-center gap-1">
            <Clock className="w-2.5 h-2.5 text-amber-400" />
            PENDING VERIFICATION
          </span>
        );
      case "NOT CONFIGURED":
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-bold font-mono bg-void border border-white/20 text-pebble flex items-center gap-1">
            <AlertTriangle className="w-2.5 h-2.5 text-pebble" />
            NOT CONFIGURED
          </span>
        );
      default:
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-bold font-mono bg-red-950/60 border border-arterial/60 text-red-300 flex items-center gap-1">
            <AlertTriangle className="w-2.5 h-2.5 text-arterial" />
            {status}
          </span>
        );
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="w-full max-w-4xl max-h-[90vh] flex flex-col rounded-card bg-charcoal border border-white/20 shadow-2xl overflow-hidden font-sans">
        {/* Header */}
        <div className="p-4 sm:p-5 border-b border-white/10 flex items-center justify-between bg-void/60">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded bg-sky-500/10 border border-sky-500/30">
              <Bell className="w-5 h-5 text-sky-400" />
            </div>
            <div>
              <h2 className="text-base font-bold font-mono text-bone flex items-center gap-2">
                Notification System & Multi-Tier Escalation Console
              </h2>
              <p className="text-xs text-ash font-mono mt-0.5">
                Honest Provider Status &bull; Outbox Deliveries &bull; HMAC Webhooks &bull; Dead-Letter Queue
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={loadAll}
              disabled={loading}
              className="p-1.5 rounded bg-smoke hover:bg-white/10 text-pebble hover:text-bone text-xs font-mono flex items-center gap-1"
              title="Refresh provider status"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin text-sky-400" : ""}`} />
            </button>
            <button
              onClick={onClose}
              className="p-1.5 rounded hover:bg-white/10 text-pebble hover:text-bone"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="flex border-b border-white/10 bg-void/30 text-xs font-mono px-4">
          <button
            onClick={() => setActiveTab("providers")}
            className={`py-3 px-4 border-b-2 font-medium flex items-center gap-2 transition-colors ${
              activeTab === "providers"
                ? "border-sky-400 text-sky-300 font-bold"
                : "border-transparent text-ash hover:text-bone"
            }`}
          >
            <ShieldAlert className="w-3.5 h-3.5" />
            <span>Honest Provider Health</span>
          </button>
          <button
            onClick={() => setActiveTab("channels")}
            className={`py-3 px-4 border-b-2 font-medium flex items-center gap-2 transition-colors ${
              activeTab === "channels"
                ? "border-sky-400 text-sky-300 font-bold"
                : "border-transparent text-ash hover:text-bone"
            }`}
          >
            <Send className="w-3.5 h-3.5" />
            <span>Channels ({channels.length})</span>
          </button>
          <button
            onClick={() => setActiveTab("escalation")}
            className={`py-3 px-4 border-b-2 font-medium flex items-center gap-2 transition-colors ${
              activeTab === "escalation"
                ? "border-sky-400 text-sky-300 font-bold"
                : "border-transparent text-ash hover:text-bone"
            }`}
          >
            <Layers className="w-3.5 h-3.5" />
            <span>Escalation Policies</span>
          </button>
          <button
            onClick={() => setActiveTab("dlq")}
            className={`py-3 px-4 border-b-2 font-medium flex items-center gap-2 transition-colors ${
              activeTab === "dlq"
                ? "border-sky-400 text-sky-300 font-bold"
                : "border-transparent text-ash hover:text-bone"
            }`}
          >
            <Archive className="w-3.5 h-3.5" />
            <span>Dead-Letter Queue ({dlq.length})</span>
          </button>
        </div>

        {/* Status Message Banner */}
        {statusMessage && (
          <div
            className={`px-4 py-2 text-xs font-mono flex items-center justify-between border-b ${
              statusMessage.error
                ? "bg-red-950/70 border-arterial/60 text-red-200"
                : "bg-emerald-950/70 border-emerald-500/50 text-emerald-200"
            }`}
          >
            <span>{statusMessage.text}</span>
            <button onClick={() => setStatusMessage(null)} className="text-white/60 hover:text-white">
              ✕
            </button>
          </div>
        )}

        {/* Content Area */}
        <div className="flex-1 overflow-y-auto p-5 space-y-5">
          {/* TAB 1: PROVIDERS HEALTH */}
          {activeTab === "providers" && (
            <div className="space-y-4">
              <div className="p-3 rounded bg-void/60 border border-white/5 text-xs font-mono text-pebble flex items-center justify-between">
                <span>
                  Honesty Invariant: Status reflects genuine socket handshakes and verified credentials.
                </span>
                <button
                  onClick={handleTriggerSimulatedAlert}
                  className="px-3 py-1 rounded bg-arterial/20 hover:bg-arterial/30 border border-arterial/50 text-red-300 font-semibold flex items-center gap-1.5 transition-colors"
                >
                  <AlertTriangle className="w-3 h-3 text-arterial" />
                  <span>Send Test Alert (End-to-End)</span>
                </button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {health?.providers?.map((p) => (
                  <div
                    key={p.type}
                    className="p-4 rounded-card bg-void border border-white/10 space-y-2 font-mono"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-sm text-bone capitalize flex items-center gap-2">
                        {p.type === "telegram" && <Send className="w-3.5 h-3.5 text-sky-400" />}
                        {p.type === "webpush" && <Bell className="w-3.5 h-3.5 text-amber-400" />}
                        {p.type === "ntfy" && <Smartphone className="w-3.5 h-3.5 text-emerald-400" />}
                        {p.type === "email" && <Mail className="w-3.5 h-3.5 text-purple-400" />}
                        {p.type === "webhook" && <Globe className="w-3.5 h-3.5 text-cyan-400" />}
                        {p.type === "sms" && <MessageSquare className="w-3.5 h-3.5 text-rose-400" />}
                        {p.type}
                      </span>
                      {renderStatusBadge(p.status)}
                    </div>

                    <p className="text-xs text-ash leading-relaxed font-sans">
                      {p.details || "Provider active and ready."}
                    </p>

                    {p.missing_env && p.missing_env.length > 0 && (
                      <div className="p-2 rounded bg-red-950/40 border border-arterial/30 text-[11px] text-red-300 space-y-1">
                        <div className="font-semibold text-[10px] text-red-400 uppercase">
                          Missing Environment Variables:
                        </div>
                        <ul className="list-disc list-inside space-y-0.5">
                          {p.missing_env.map((envVar) => (
                            <li key={envVar} className="font-mono text-[10px]">
                              {envVar}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* TAB 2: CHANNELS */}
          {activeTab === "channels" && (
            <div className="space-y-5">
              {/* Add Channel Form */}
              <div className="p-4 rounded-card bg-void border border-white/10 space-y-3 font-mono text-xs">
                <h3 className="font-bold text-bone flex items-center gap-2">
                  <Plus className="w-4 h-4 text-sky-400" />
                  <span>Register New Notification Channel</span>
                </h3>
                <form onSubmit={handleCreateChannel} className="grid grid-cols-1 sm:grid-cols-4 gap-3">
                  <div>
                    <label className="text-pebble block mb-1">Channel Name:</label>
                    <input
                      type="text"
                      placeholder="e.g. Flight Director Email"
                      value={newChName}
                      onChange={(e) => setNewChName(e.target.value)}
                      required
                      className="w-full px-3 py-1.5 rounded bg-smoke border border-white/15 text-bone focus:outline-none focus:border-sky-500"
                    />
                  </div>

                  <div>
                    <label className="text-pebble block mb-1">Channel Type:</label>
                    <select
                      value={newChType}
                      onChange={(e) => setNewChType(e.target.value)}
                      className="w-full px-3 py-1.5 rounded bg-smoke border border-white/15 text-bone focus:outline-none focus:border-sky-500"
                    >
                      <option value="email">Email (SMTP)</option>
                      <option value="webhook">Webhook (HMAC)</option>
                      <option value="sms">SMS (Twilio E.164)</option>
                      <option value="telegram">Telegram (Chat ID)</option>
                      <option value="ntfy">ntfy.sh (Topic)</option>
                    </select>
                  </div>

                  <div>
                    <label className="text-pebble block mb-1">Destination Address:</label>
                    <input
                      type="text"
                      placeholder={
                        newChType === "email"
                          ? "ops@space.org"
                          : newChType === "sms"
                          ? "+1234567890"
                          : newChType === "webhook"
                          ? "https://ops.corp/hook"
                          : "Target ID or Topic"
                      }
                      value={newChAddress}
                      onChange={(e) => setNewChAddress(e.target.value)}
                      required
                      className="w-full px-3 py-1.5 rounded bg-smoke border border-white/15 text-bone focus:outline-none focus:border-sky-500"
                    />
                  </div>

                  <div className="flex items-end">
                    <button
                      type="submit"
                      disabled={formSubmitting}
                      className="w-full px-3 py-1.5 rounded bg-sky-600 hover:bg-sky-500 text-white font-bold transition-colors disabled:opacity-50"
                    >
                      {formSubmitting ? "Adding..." : "Add Channel"}
                    </button>
                  </div>
                </form>
              </div>

              {/* Channels List */}
              <div className="space-y-2">
                {channels.length === 0 ? (
                  <div className="p-8 text-center text-xs font-mono text-pebble rounded bg-void border border-white/5">
                    No notification channels registered. Add a channel above or configure Web Push / Telegram.
                  </div>
                ) : (
                  channels.map((ch) => (
                    <div
                      key={ch.id}
                      className="p-3 rounded-card bg-void border border-white/10 flex flex-col sm:flex-row sm:items-center justify-between gap-3 font-mono text-xs"
                    >
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-bone">{ch.name}</span>
                          <span className="text-[10px] uppercase px-1.5 py-0.2 rounded bg-smoke text-pebble">
                            {ch.type}
                          </span>
                          {renderStatusBadge(ch.status)}
                        </div>
                        <div className="text-pebble text-[11px]">
                          Address: <span className="text-ash">{ch.masked_address}</span>
                          {ch.verified_at && (
                            <span className="ml-3 text-emerald-400/80">
                              Verified: {new Date(ch.verified_at).toLocaleTimeString()}
                            </span>
                          )}
                          {ch.last_error && (
                            <span className="ml-3 text-red-400">Error: {ch.last_error}</span>
                          )}
                        </div>
                      </div>

                      <div className="flex items-center gap-2 shrink-0">
                        <button
                          onClick={() => handleTestChannel(ch.id)}
                          className="px-2.5 py-1 rounded bg-smoke hover:bg-white/10 border border-white/10 text-ash hover:text-bone text-[11px] flex items-center gap-1"
                        >
                          <Send className="w-3 h-3 text-sky-400" />
                          <span>Test</span>
                        </button>
                        <button
                          onClick={() => handleDeleteChannel(ch.id)}
                          className="p-1 rounded bg-smoke hover:bg-red-950/60 border border-white/10 hover:border-arterial/60 text-pebble hover:text-red-300"
                          title="Delete channel"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}

          {/* TAB 3: ESCALATION POLICIES */}
          {activeTab === "escalation" && (
            <div className="space-y-4 font-mono text-xs">
              <div className="p-3 rounded bg-void/60 border border-white/5 text-pebble">
                Multi-tier escalation dispatches notifications according to time elapsed without operator acknowledgement.
              </div>

              <div className="p-4 rounded-card bg-void border border-white/10 space-y-4">
                <h3 className="font-bold text-bone">Tiered Escalation Matrix</h3>

                {/* Tier L1 */}
                <div className="p-3 rounded bg-smoke/40 border border-white/10 space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-sky-300">Tier L1 (Immediate Dispatch)</span>
                    <span className="text-emerald-400 font-bold">0s delay</span>
                  </div>
                  <p className="text-ash text-[11px] font-sans">
                    Fires instantaneously upon critical safety condition creation.
                  </p>
                  <div className="flex gap-2 pt-1">
                    <span className="px-2 py-0.5 rounded bg-void text-[10px] text-bone">Telegram</span>
                    <span className="px-2 py-0.5 rounded bg-void text-[10px] text-bone">Web Push</span>
                    <span className="px-2 py-0.5 rounded bg-void text-[10px] text-bone">ntfy Mobile</span>
                  </div>
                </div>

                {/* Tier L2 */}
                <div className="p-3 rounded bg-smoke/40 border border-white/10 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-amber-300">Tier L2 (Secondary Escalation)</span>
                    <div className="flex items-center gap-1.5">
                      <span className="text-pebble">Delay:</span>
                      <input
                        type="number"
                        min="30"
                        max="3600"
                        value={l2DelaySec}
                        onChange={(e) => setL2DelaySec(Number(e.target.value))}
                        className="w-20 px-2 py-0.5 rounded bg-void border border-white/20 text-bone text-center font-bold"
                      />
                      <span className="text-pebble">seconds ({Math.round(l2DelaySec / 60)}m)</span>
                    </div>
                  </div>
                  <p className="text-ash text-[11px] font-sans">
                    Dispatched if no human operator acknowledges or dismisses the alert within {l2DelaySec}s.
                  </p>
                  <div className="flex gap-2 pt-1">
                    <span className="px-2 py-0.5 rounded bg-void text-[10px] text-bone">SMTP Email</span>
                    <span className="px-2 py-0.5 rounded bg-void text-[10px] text-bone">SMS Primary</span>
                  </div>
                </div>

                {/* Tier L3 */}
                <div className="p-3 rounded bg-smoke/40 border border-white/10 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-red-400">Tier L3 (Flight Director Escalation)</span>
                    <div className="flex items-center gap-1.5">
                      <span className="text-pebble">Delay:</span>
                      <input
                        type="number"
                        min="60"
                        max="7200"
                        value={l3DelaySec}
                        onChange={(e) => setL3DelaySec(Number(e.target.value))}
                        className="w-20 px-2 py-0.5 rounded bg-void border border-white/20 text-bone text-center font-bold"
                      />
                      <span className="text-pebble">seconds ({Math.round(l3DelaySec / 60)}m)</span>
                    </div>
                  </div>
                  <p className="text-ash text-[11px] font-sans">
                    Dispatched if unacknowledged after {l3DelaySec}s. Alerts standby engineering and mission director.
                  </p>
                  <div className="flex gap-2 pt-1">
                    <span className="px-2 py-0.5 rounded bg-void text-[10px] text-bone">Mission Webhook</span>
                    <span className="px-2 py-0.5 rounded bg-void text-[10px] text-bone">Director SMS</span>
                  </div>
                </div>

                <div className="pt-2 flex justify-end">
                  <button
                    onClick={handleSavePolicy}
                    disabled={formSubmitting}
                    className="px-4 py-2 rounded bg-sky-600 hover:bg-sky-500 font-bold text-white transition-colors disabled:opacity-50"
                  >
                    {formSubmitting ? "Saving..." : "Save Escalation Delays"}
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* TAB 4: DEAD-LETTER QUEUE */}
          {activeTab === "dlq" && (
            <div className="space-y-3 font-mono text-xs">
              <div className="p-3 rounded bg-void/60 border border-white/5 text-pebble flex items-center justify-between">
                <span>
                  Dead-Letter Queue records delivery attempts that failed after max retries (exponential backoff).
                </span>
                <span className="text-bone font-bold">Total: {dlq.length}</span>
              </div>

              {dlq.length === 0 ? (
                <div className="p-8 text-center text-pebble rounded bg-void border border-white/5">
                  <CheckCircle2 className="w-6 h-6 text-emerald-400 mx-auto mb-2 opacity-60" />
                  <span>Dead-letter queue is completely clear. All outbox dispatches delivered.</span>
                </div>
              ) : (
                <div className="space-y-2">
                  {dlq.map((item) => (
                    <div
                      key={item.outbox_id}
                      className="p-3.5 rounded-card bg-void border border-arterial/40 space-y-2"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-bone">{item.channel_name}</span>
                          <span className="text-[10px] px-1.5 py-0.2 rounded bg-smoke text-pebble uppercase">
                            {item.channel_type}
                          </span>
                          <span className="text-red-400 font-bold text-[10px]">
                            {item.attempts}/{item.max_attempts} attempts failed
                          </span>
                        </div>
                        <button
                          onClick={() => handleRetryDlq(item.outbox_id)}
                          className="px-3 py-1 rounded bg-smoke hover:bg-white/10 border border-white/20 text-sky-300 hover:text-white font-bold flex items-center gap-1.5"
                        >
                          <RefreshCw className="w-3 h-3" />
                          <span>Retry Delivery</span>
                        </button>
                      </div>

                      <div className="text-[11px] text-ash space-y-0.5">
                        <div>Alert: <span className="text-bone">{item.alert_title}</span></div>
                        <div className="text-red-300 font-sans break-words">
                          Last Error: {item.last_error}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-white/10 bg-void/80 flex items-center justify-between text-xs font-mono">
          <span className="text-pebble">
            ASTRA-GUARD Advisory Delivery Subsystem &bull; Operator: {operatorUser}
          </span>
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-nav bg-smoke hover:bg-white/10 border border-white/20 text-bone"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
