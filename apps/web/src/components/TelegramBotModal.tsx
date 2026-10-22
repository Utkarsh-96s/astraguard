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

export function TelegramBotModal({ alertId, onClose, onActionComplete }: TelegramBotModalProps) {
  const [data, setData] = useState<BotPreviewData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [actionStatus, setActionStatus] = useState<string | null>(null);
  const [isActing, setIsActing] = useState(false);

  useEffect(() => {
    async function loadPreview() {
      try {
        const res = await fetch(`http://localhost:8000/api/v1/bot/preview/${alertId}`);
        if (res.ok) {
          const json = await res.json();
          setData(json);
        }
      } catch {
        // Fallback simulation preview
        setData({
          alert_id: alertId,
          asset_id: "SENTINEL-2A",
          level: "CRITICAL",
          status: "ACTIVE",
          telegram_payload: {
            chat_id: "@astraguard_alerts_channel",
            text: `🚨 *ASTRA-GUARD MISSION SAFETY ALERT*\n\n🛰 *Asset:* \`SENTINEL-2A\`\n📊 *Level:* *CRITICAL* (Pc: 2.50e-04)\n📝 *Title:* Critical Debris Conjunction Warning\n\n🔍 *Diagnostic Rationale:*\nHigh probability of collision with Cosmos debris fragment. TCA: T-4.2h.\n\n💡 *Advisory Recommendation:*\nExecute 0.42 m/s prograde avoidance burn.\n\n🔒 *HITL Policy:* Operator approval required.`,
            parse_mode: "Markdown",
            reply_markup: {
              inline_keyboard: [
                [
                  { text: "✅ Approve Advisory", callback_data: `approve:${alertId}` },
                  { text: "❌ Dismiss", callback_data: `dismiss:${alertId}` },
                ],
                [
                  { text: "⏱ Snooze (15m)", callback_data: `snooze:${alertId}` },
                  { text: "📊 Open Web Console", url: "http://localhost:3000/alerts" },
                ],
              ],
            },
          },
          dispatched_at: new Date().toISOString(),
          channel: "Telegram Bot (@AstraGuardBot)",
          is_live_configured: false,
        });
      } finally {
        setIsLoading(false);
      }
    }

    loadPreview();
  }, [alertId]);

  const handleAction = async (action: "approve" | "dismiss" | "snooze") => {
    setIsActing(true);
    soundFx.playClickFx();

    try {
      const res = await fetch("http://localhost:8000/api/v1/bot/action", {
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
        setActionStatus(`ACTION RECORDED: ${resJson.status}`);
        voiceAnnouncer.announce(`Alert ${action === "approve" ? "approved" : action} via mobile Telegram bot.`);
        if (onActionComplete) onActionComplete();
      } else {
        setActionStatus(`SIMULATED: ${action.toUpperCase()} EXECUTED`);
      }
    } catch {
      setActionStatus(`SIMULATED: ${action.toUpperCase()} EXECUTED`);
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
              Phone Alert Bot Simulator (F10)
            </span>
          </div>
          <button
            onClick={onClose}
            className="p-1 text-ash hover:text-bone rounded hover:bg-white/10 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Telegram Mobile Phone Canvas */}
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
            </div>

            {/* Message Bubble */}
            <div className="space-y-2">
              <div className="bg-[#182533] p-3 rounded-2xl rounded-tl-sm border border-cyan-500/20 text-xs text-gray-200 space-y-2 shadow-md">
                {isLoading ? (
                  <div className="py-6 text-center text-xs font-mono text-gray-400">
                    Formatting Telegram dispatch payload...
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

                    <p className="text-[11px] whitespace-pre-line font-sans text-gray-300 leading-relaxed">
                      {data?.telegram_payload.text}
                    </p>

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
                    <span>Snooze (15m)</span>
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

        {/* Modal Footer Notes */}
        <div className="px-4 py-2.5 bg-smoke/90 border-t border-white/10 flex items-center justify-between text-[11px] font-mono text-pebble">
          <span>Channel: Telegram Webhook Bot</span>
          <span className="text-cyan-400">HITL Verified</span>
        </div>
      </div>
    </div>
  );
}
