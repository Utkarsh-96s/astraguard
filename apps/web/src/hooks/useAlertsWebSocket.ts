"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { Alert } from "@/lib/types";

export type WebSocketConnectionStatus = "connecting" | "connected" | "disconnected";

export interface AlertWebSocketEvent {
  event: string;
  alert: Alert;
}

interface UseAlertsWebSocketOptions {
  onAlertEvent?: (event: AlertWebSocketEvent) => void;
  onCatchUp?: (sinceIso: string) => Promise<void> | void;
  enabled?: boolean;
}

export function useAlertsWebSocket({
  onAlertEvent,
  onCatchUp,
  enabled = true,
}: UseAlertsWebSocketOptions = {}) {
  const [status, setStatus] = useState<WebSocketConnectionStatus>("connecting");
  const [lastMessageAt, setLastMessageAt] = useState<Date | null>(null);
  const [reconnectCount, setReconnectCount] = useState<number>(0);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const pingIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const backoffRef = useRef<number>(1000);
  const lastSeenIsoRef = useRef<string>(new Date().toISOString());
  const hasDisconnectedOnceRef = useRef<boolean>(false);

  // Derive WebSocket URL safely for SSR / browser
  const getWebSocketUrl = useCallback(() => {
    if (process.env.NEXT_PUBLIC_WS_URL) {
      return `${process.env.NEXT_PUBLIC_WS_URL}/ws/alerts`;
    }
    const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    if (apiBase.startsWith("http://")) {
      return apiBase.replace("http://", "ws://") + "/ws/alerts";
    }
    if (apiBase.startsWith("https://")) {
      return apiBase.replace("https://", "wss://") + "/ws/alerts";
    }
    if (typeof window !== "undefined") {
      const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
      return `${proto}//${window.location.host}/ws/alerts`;
    }
    return "ws://localhost:8000/ws/alerts";
  }, []);

  const connect = useCallback(() => {
    if (!enabled || typeof window === "undefined") return;

    if (wsRef.current && (wsRef.current.readyState === WebSocket.OPEN || wsRef.current.readyState === WebSocket.CONNECTING)) {
      return;
    }

    setStatus("connecting");
    const wsUrl = getWebSocketUrl();

    try {
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        setStatus("connected");
        setLastMessageAt(new Date());
        backoffRef.current = 1000;

        // Start ping heartbeat
        if (pingIntervalRef.current) clearInterval(pingIntervalRef.current);
        pingIntervalRef.current = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send("ping");
          }
        }, 25000);

        // If previously disconnected, trigger catch-up query
        if (hasDisconnectedOnceRef.current && onCatchUp) {
          try {
            onCatchUp(lastSeenIsoRef.current);
          } catch (e) {
            console.warn("Alerts WebSocket catch-up failed:", e);
          }
        }
      };

      ws.onmessage = (event) => {
        setLastMessageAt(new Date());
        const dataStr = event.data;
        if (dataStr === "pong") return;

        try {
          const parsed = JSON.parse(dataStr);
          if (parsed.event && parsed.alert) {
            const alertEvent: AlertWebSocketEvent = {
              event: parsed.event,
              alert: parsed.alert,
            };
            if (parsed.alert.created_at) {
              lastSeenIsoRef.current = parsed.alert.created_at;
            }
            onAlertEvent?.(alertEvent);
          }
        } catch {
          // Non-JSON ping or greeting message
        }
      };

      ws.onerror = () => {
        // ws.onclose will handle reconnection
      };

      ws.onclose = () => {
        setStatus("disconnected");
        hasDisconnectedOnceRef.current = true;
        if (pingIntervalRef.current) {
          clearInterval(pingIntervalRef.current);
          pingIntervalRef.current = null;
        }

        // Schedule exponential backoff reconnect
        if (enabled) {
          const delay = Math.min(backoffRef.current, 15000);
          backoffRef.current = Math.round(delay * 1.5);
          setReconnectCount((c) => c + 1);

          if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, delay);
        }
      };
    } catch {
      setStatus("disconnected");
      const delay = Math.min(backoffRef.current, 15000);
      backoffRef.current = Math.round(delay * 1.5);
      reconnectTimeoutRef.current = setTimeout(connect, delay);
    }
  }, [enabled, getWebSocketUrl, onAlertEvent, onCatchUp]);

  useEffect(() => {
    connect();

    return () => {
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
      if (pingIntervalRef.current) clearInterval(pingIntervalRef.current);
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [connect]);

  const updateLastSeen = useCallback((isoString: string) => {
    lastSeenIsoRef.current = isoString;
  }, []);

  return {
    status,
    lastMessageAt,
    reconnectCount,
    updateLastSeen,
    reconnect: () => {
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
      if (wsRef.current) wsRef.current.close();
      backoffRef.current = 1000;
      connect();
    },
  };
}
