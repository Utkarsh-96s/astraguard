"use client";

import React, { useEffect, useState } from "react";
import {
  Send,
  Bell,
  Smartphone,
  Mail,
  Globe,
  MessageSquare,
  CheckCircle2,
  Clock,
  AlertCircle,
  RefreshCw,
} from "lucide-react";
import { AlertDeliveryItem } from "@/lib/types";
import { fetchAlertDeliveries } from "@/lib/api";

interface DeliveryChipsProps {
  alertId: string;
}

export function DeliveryChips({ alertId }: DeliveryChipsProps) {
  const [deliveries, setDeliveries] = useState<AlertDeliveryItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [activeTooltip, setActiveTooltip] = useState<string | null>(null);

  const loadDeliveries = React.useCallback(async () => {
    setLoading(true);
    try {
      const items = await fetchAlertDeliveries(alertId);
      setDeliveries(items);
    } catch {
      // Keep empty if API offline
    } finally {
      setLoading(false);
    }
  }, [alertId]);

  useEffect(() => {
    loadDeliveries();
    // Poll delivery status every 10 seconds for active outbox updates
    const interval = setInterval(loadDeliveries, 10000);
    return () => clearInterval(interval);
  }, [loadDeliveries]);

  if (deliveries.length === 0) {
    return (
      <div className="flex items-center gap-1.5 text-[10px] font-mono text-pebble">
        <Clock className="w-3 h-3 text-pebble" />
        <span>No outbox dispatches queued</span>
      </div>
    );
  }

  const getChannelIcon = (type: string) => {
    switch (type.toLowerCase()) {
      case "telegram":
        return <Send className="w-3 h-3" />;
      case "webpush":
        return <Bell className="w-3 h-3" />;
      case "ntfy":
        return <Smartphone className="w-3 h-3" />;
      case "email":
        return <Mail className="w-3 h-3" />;
      case "webhook":
        return <Globe className="w-3 h-3" />;
      case "sms":
        return <MessageSquare className="w-3 h-3" />;
      default:
        return <Send className="w-3 h-3" />;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status.toLowerCase()) {
      case "delivered":
        return {
          bg: "bg-emerald-950/60 border-emerald-500/50 text-emerald-300",
          icon: <CheckCircle2 className="w-2.5 h-2.5 text-emerald-400" />,
          label: "DELIVERED",
        };
      case "sent":
        return {
          bg: "bg-sky-950/60 border-sky-500/50 text-sky-300",
          icon: <CheckCircle2 className="w-2.5 h-2.5 text-sky-400" />,
          label: "SENT",
        };
      case "sending":
      case "queued":
        return {
          bg: "bg-amber-950/60 border-amber-500/50 text-amber-300",
          icon: <Clock className="w-2.5 h-2.5 text-amber-400 animate-spin" />,
          label: status.toUpperCase(),
        };
      case "failed":
      case "dead":
        return {
          bg: "bg-red-950/60 border-arterial/60 text-red-300",
          icon: <AlertCircle className="w-2.5 h-2.5 text-arterial" />,
          label: status.toUpperCase(),
        };
      default:
        return {
          bg: "bg-white/5 border-white/10 text-ash",
          icon: null,
          label: status.toUpperCase(),
        };
    }
  };

  return (
    <div className="flex flex-wrap items-center gap-2">
      <span className="text-[10px] font-mono uppercase text-pebble flex items-center gap-1">
        Outbox Dispatches:
        {loading && <RefreshCw className="w-2.5 h-2.5 animate-spin text-ash ml-0.5" />}
      </span>

      {deliveries.map((item) => {
        const badge = getStatusBadge(item.status);
        const tooltipId = item.outbox_id;
        const isTooltipOpen = activeTooltip === tooltipId;

        return (
          <div
            key={item.outbox_id}
            className="relative"
            onMouseEnter={() => setActiveTooltip(tooltipId)}
            onMouseLeave={() => setActiveTooltip(null)}
          >
            <div
              className={`px-2 py-0.5 rounded text-[10px] font-mono font-medium border flex items-center gap-1.5 cursor-pointer transition-colors ${badge.bg}`}
            >
              {getChannelIcon(item.channel_type)}
              <span className="capitalize">{item.channel_type}</span>
              <span className="text-white/20">|</span>
              <span className="flex items-center gap-1 text-[9px] font-bold">
                {badge.icon}
                {badge.label}
              </span>
              {item.escalation_level > 1 && (
                <span className="px-1 rounded bg-black/40 text-[9px] text-amber-300 font-mono">
                  L{item.escalation_level}
                </span>
              )}
            </div>

            {/* Hover Tooltip */}
            {isTooltipOpen && (
              <div className="absolute bottom-full left-0 mb-2 z-50 w-64 p-3 rounded-card bg-void/95 border border-white/20 shadow-2xl text-[11px] font-mono text-ash space-y-1.5 pointer-events-none backdrop-blur-md">
                <div className="flex items-center justify-between border-b border-white/10 pb-1">
                  <span className="font-bold text-bone capitalize">{item.channel_name || item.channel_type}</span>
                  <span className="text-[10px] px-1.5 py-0.2 rounded bg-smoke text-pebble">
                    Tier L{item.escalation_level}
                  </span>
                </div>

                <div className="space-y-0.5 text-[10px]">
                  <div>
                    <span className="text-pebble">Destination: </span>
                    <span className="text-bone">{item.masked_address || "System Default"}</span>
                  </div>
                  <div>
                    <span className="text-pebble">Status: </span>
                    <span className="text-bone uppercase">{item.status}</span>
                  </div>
                  {item.provider_message_id && (
                    <div className="truncate">
                      <span className="text-pebble">Message ID: </span>
                      <span className="text-emerald-300">{item.provider_message_id}</span>
                    </div>
                  )}
                  {item.sent_at && (
                    <div>
                      <span className="text-pebble">Sent: </span>
                      <span className="text-bone">{new Date(item.sent_at).toLocaleTimeString()}</span>
                    </div>
                  )}
                  <div>
                    <span className="text-pebble">Attempts: </span>
                    <span className="text-bone">{item.attempts} / {item.max_attempts}</span>
                  </div>
                  {item.last_error && (
                    <div className="text-red-400 border-t border-white/10 pt-1 mt-1 break-words">
                      <span className="text-pebble">Error: </span>
                      {item.last_error}
                    </div>
                  )}
                  {item.test && (
                    <div className="text-[9px] text-amber-300 font-bold">
                      [SIMULATED TEST DISPATCH]
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
