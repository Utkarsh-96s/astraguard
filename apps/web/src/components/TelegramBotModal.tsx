"use client";

import React, { useState, useEffect } from "react";
import {
  Send,
  X,
  Shield,
  CheckCircle,
  AlertOctagon,
  Clock,
  Radio,
  Smartphone,
  Check,
  QrCode,
  ExternalLink,
  AlertTriangle,
} from "lucide-react";
import { soundFx } from "../lib/audio";
import { voiceAnnouncer } from "../lib/voice";

interface TelegramBotModalProps {
  alertId: string;
  onClose: () => void;
  onActionComplete?: () => void;
}

interface TelegramPayload {
  chat_id: string;
  text: string;
  parse_mode: string;
  reply_markup: {
    inline_keyboard: Array<Array<{ text: string; callback_data?: string; url?: string }>>;
  };
}

interface BotPreviewData {
  alert_id: string;
  asset_id: string;
  level: string;
  status: string;
  telegram_payload: TelegramPayload;
  dispatched_at: string;
  channel: string;
  is_live_configured: boolean;
}

interface LinkInfo {
  linking_code: string;
  deep_link: string;
  instructions: string;
}

export function TelegramBotModal({ alertId, onClose, onActionComplete }: TelegramBotModalProps) {
  const [data, setData] = useState<BotPreviewData | null>(null);
  const [activeTab, setActiveTab] = useState<"phone" | "connect">("phone");
  const [linkInfo, setLinkInfo] = useState<LinkInfo | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [actionStatus, setActionStatus] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isActing, setIsActing] = useState(false);

  const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  useEffect(() => {
    async function loadPreview() {
      try {
        const res = await fetch(`${API_BASE}/api/v1/bot/preview/${alertId}`);
        if (res.ok) {
          const json = await res.json();
          setData(json);
        } else {
          setErrorMessage("Failed to load bot dispatch preview from backend.");
        }
      } catch (err) {
        setErrorMessage(err instanceof Error ? err.message : "Failed to connect to backend.");
      } finally {
        setIsLoading(false);
      }
    }

    async function loadLinkInfo() {
      try {
        // Try getting telegram channel verification code
        const res = await fetch(`${API_BASE}/api/v1/notifications/channels`);
        if (res.ok) {
          const channels = await res.json();
          const tg = channels.find((c: any) => c.type === "telegram");
          if (tg) {
            const vRes = await fetch(`${API_BASE}/api/v1/notifications/channels/${tg.id}/verify`, { method: "POST" });
            if (vRes.ok) {
              const vData = await vRes.json();
              if (vData.linking_code) {
                setLinkInfo(vData);
              }
            }
          }
        }
      } catch (err) {
        console.warn("Could not fetch Telegram link info:", err);
      }
    }

    loadPreview();
    loadLinkInfo();
  }, [alertId, API_BASE]);

  const handleAction = async (action: "approve" | "dismiss" | "snooze") => {
    setIsActing(true);
    setErrorMessage(null);
    soundFx.playClickFx();

    try {
      const res = await fetch(`${API_BASE}/api/v1/bot/action`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          alert_id: alertId,
          action: action,
          operator: "FlightDirector_Mobile",
          note: `Authorized via Telegram Mobile Bot inline button (${action.toUpperCase()})`,
        }),
      });

      if (res.ok) {
        soundFx.playSuccessChirp();
        const resJson = await res.json();
        setActionStatus(`ACTION RECORDED: ${resJson.action} (${resJson.new_status})`);
        voiceAnnouncer.announce(`Alert ${action === "approve" ? "approved" : action} via mobile Telegram bot.`);
        if (onActionComplete) onActionComplete();
      } else {
        const errJson = await res.json().catch(() => ({ detail: "Action execution failed." }));
        setErrorMessage(errJson.detail || "Failed to record action.");
      }
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : "Network error recording action.");
    } finally {
      setIsActing(false);
    }
  };

  return (
    <div data-lenis-prevent className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-void/80 backdrop-blur-md animate-in fade-in duration-200">
      <div data-lenis-prevent className="relative w-full max-w-md rounded-2xl bg-charcoal border border-cyan-500/40 shadow-2xl overflow-hidden flex flex-col">
        {/* Modal Top Header */}
        <div className="flex items-center justify-between px-4 py-3 bg-smoke/80 border-b border-white/10">
          <div className="flex items-center gap-2">
            <Smartphone className="w-4 h-4 text-cyan-400" />
            <span className="text-xs font-mono font-bold text-bone">
              Telegram Alert Bot (F10)
            </span>
          </div>

          {/* Tab Selector */}
          <div className="flex items-center gap-1 bg-void/60 p-0.5 rounded-lg text-[10px] font-mono">
            <button
              onClick={() => setActiveTab("phone")}
              className={`px-2 py-0.5 rounded ${
                activeTab === "phone" ? "bg-white/15 text-bone font-bold" : "text-ash hover:text-bone"
              }`}
            >
              Simulator
            </button>
            <button
              onClick={() => setActiveTab("connect")}
              className={`px-2 py-0.5 rounded flex items-center gap-1 ${
                activeTab === "connect" ? "bg-cyan-500/20 text-cyan-300 font-bold" : "text-ash hover:text-cyan-300"
              }`}
            >
              <QrCode className="w-3 h-3" />
              <span>Connect</span>
            </button>
          </div>

          <button
            onClick={onClose}
            className="p-1 text-ash hover:text-bone rounded hover:bg-white/10 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Tab 1: Simulator */}
        {activeTab === "phone" && (
          <div className="p-4 bg-void/90 flex flex-col items-center">
            {/* Phone Frame */}
            <div className="w-full max-w-sm rounded-[24px] bg-[#0e1621] border-2 border-white/20 p-3 shadow-2xl space-y-3 font-sans">
              {/* Status Bar */}
              <div className="flex items-center justify-between text-[11px] text-gray-400 px-2 font-mono">
                <span>09:41</span>
                <div className="flex items-center gap-1.5">
                  <Radio className="w-3 h-3 text-cyan-400" />
                  <span>5G</span>
                  <span>100%</span>
                </div>
              </div>

              {/* Telegram Channel Bar */}
              <div className="flex items-center gap-2.5 px-2 py-1.5 bg-[#17212b] rounded-xl border border-white/5">
                <div className="w-8 h-8 rounded-full bg-arterial flex items-center justify-center text-white font-bold text-xs shrink-0 shadow-md">
                  <Shield className="w-4 h-4" />
                </div>
                <div className="min-w-0 flex-1">
                  <div className="text-xs font-bold text-white flex items-center gap-1">
                    <span>ASTRA-GUARD Bot</span>
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 inline-block" />
                  </div>
                  <div className="text-[10px] text-gray-400 font-mono">bot · Mission Safety Stream</div>
                </div>

                {data?.is_live_configured ? (
                  <span className="px-1.5 py-0.5 rounded bg-emerald-950/80 border border-emerald-500/40 text-[9px] font-mono text-emerald-300">
                    LIVE
                  </span>
                ) : (
                  <span className="px-1.5 py-0.5 rounded bg-amber-950/80 border border-amber-500/40 text-[9px] font-mono text-amber-300">
                    SIMULATED
                  </span>
                )}
              </div>

              {/* Message Bubble */}
              <div className="space-y-2">
                <div className="bg-[#182533] p-3 rounded-2xl rounded-tl-sm border border-cyan-500/20 text-xs text-gray-200 space-y-2 shadow-md">
                  {isLoading ? (
                    <div className="py-6 text-center text-xs font-mono text-gray-400">
                      Formatting Telegram dispatch payload...
                    </div>
                  ) : errorMessage ? (
                    <div className="p-2 rounded bg-red-950/40 border border-red-500/40 text-red-300 text-xs flex items-center gap-1.5">
                      <AlertTriangle className="w-4 h-4 shrink-0 text-red-400" />
                      <span>{errorMessage}</span>
                    </div>
                  ) : (
                    <>
                      <div className="flex items-center justify-between pb-1 border-b border-white/10">
                        <span className="font-bold text-white flex items-center gap-1">
                          <AlertOctagon className="w-3.5 h-3.5 text-arterial" />
                          MISSION ALERT
                        </span>
                        <span className="text-[10px] text-cyan-300 font-mono font-semibold">
                          {data?.level}
                        </span>
                      </div>

                      <div
                        className="text-[11px] whitespace-pre-line font-sans text-gray-300 leading-relaxed"
                        dangerouslySetInnerHTML={{
                          __html: data?.telegram_payload.text || "",
                        }}
                      />

                      <div className="text-[10px] text-gray-500 font-mono text-right pt-1">
                        09:41 ✓✓
                      </div>
                    </>
                  )}
                </div>

                {/* Telegram Inline Keyboard Buttons */}
                <div className="space-y-1.5 pt-1">
                  <div className="grid grid-cols-2 gap-1.5">
                    <button
                      onClick={() => handleAction("approve")}
                      disabled={isActing}
                      className="py-2 px-2.5 rounded-lg bg-[#2b5278] hover:bg-[#346696] active:bg-[#1f3d5a] text-white text-[11px] font-semibold flex items-center justify-center gap-1.5 transition-colors shadow-sm disabled:opacity-50"
                    >
                      <CheckCircle className="w-3.5 h-3.5 text-emerald-300" />
                      <span>Approve Advisory</span>
                    </button>
                    <button
                      onClick={() => handleAction("dismiss")}
                      disabled={isActing}
                      className="py-2 px-2.5 rounded-lg bg-[#243547] hover:bg-[#2e435a] active:bg-[#1a2836] text-gray-300 text-[11px] font-semibold flex items-center justify-center gap-1.5 transition-colors shadow-sm disabled:opacity-50"
                    >
                      <X className="w-3.5 h-3.5 text-red-400" />
                      <span>Dismiss</span>
                    </button>
                  </div>

                  <div className="grid grid-cols-2 gap-1.5">
                    <button
                      onClick={() => handleAction("snooze")}
                      disabled={isActing}
                      className="py-1.5 px-2.5 rounded-lg bg-[#1f2d3d] hover:bg-[#293b4f] text-gray-400 text-[11px] font-mono flex items-center justify-center gap-1.5 transition-colors disabled:opacity-50"
                    >
                      <Clock className="w-3 h-3 text-amber-400" />
                      <span>Snooze (30m)</span>
                    </button>
                    <button
                      onClick={onClose}
                      className="py-1.5 px-2.5 rounded-lg bg-[#1f2d3d] hover:bg-[#293b4f] text-gray-400 text-[11px] font-mono flex items-center justify-center gap-1.5 transition-colors"
                    >
                      <span>Close Phone</span>
                    </button>
                  </div>
                </div>
              </div>

              {/* Action Feedback Banner */}
              {actionStatus && (
                <div className="px-3 py-1.5 rounded-lg bg-emerald-950/80 border border-emerald-500/50 text-[11px] font-mono text-emerald-300 flex items-center gap-1.5 animate-in fade-in">
                  <Check className="w-3.5 h-3.5" />
                  <span>{actionStatus}</span>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Tab 2: Real Phone Linking Flow */}
        {activeTab === "connect" && (
          <div className="p-6 bg-void/90 space-y-4 text-xs font-mono">
            <div className="text-center space-y-1">
              <h4 className="text-sm font-bold text-bone">Pair Live Telegram Chat</h4>
              <p className="text-[11px] text-pebble">
                Receive live alerts on your personal phone or flight operations group chat.
              </p>
            </div>

            {/* QR Code / Deep Link Box */}
            <div className="p-4 rounded-xl bg-charcoal border border-cyan-500/30 flex flex-col items-center gap-3 text-center">
              {/* ASCII / SVG QR Frame */}
              <div className="w-36 h-36 bg-white p-2 rounded-lg flex items-center justify-center shadow-lg">
                <QrCode className="w-32 h-32 text-black" />
              </div>

              {linkInfo ? (
                <div className="space-y-2 w-full">
                  <div className="text-[11px] text-ash">
                    One-Time Pairing Code:{" "}
                    <span className="text-cyan-300 font-bold tracking-wider">{linkInfo.linking_code}</span>
                  </div>

                  <a
                    href={linkInfo.deep_link}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="w-full py-2 px-3 rounded-lg bg-[#2b5278] hover:bg-[#346696] text-white font-semibold flex items-center justify-center gap-1.5 transition-colors"
                  >
                    <ExternalLink className="w-3.5 h-3.5" />
                    <span>Open in Telegram (@AstraGuardAlertsBot)</span>
                  </a>
                </div>
              ) : (
                <div className="text-pebble text-[11px]">
                  Generating secure one-time linking token...
                </div>
              )}
            </div>

            {/* Instructions */}
            <div className="p-3 rounded bg-smoke/40 border border-white/5 space-y-1.5 text-[11px] text-ash">
              <div className="text-bone font-semibold">How linking works:</div>
              <ol className="list-decimal list-inside space-y-1 text-pebble">
                <li>Scan the QR code or tap the link above on your phone.</li>
                <li>Tap <strong>Start</strong> in Telegram to execute the pairing handshake.</li>
                <li>The bot maps your chat ID and marks your channel <strong>CONNECTED</strong> live via WebSocket.</li>
              </ol>
            </div>
          </div>
        )}

        {/* Modal Footer Notes */}
        <div className="px-4 py-2.5 bg-smoke/90 border-t border-white/10 flex items-center justify-between text-[11px] font-mono text-pebble">
          <span>Channel: Telegram Bot API</span>
          <span className="text-cyan-400">Advisory HITL Enforced</span>
        </div>
      </div>
    </div>
  );
}
