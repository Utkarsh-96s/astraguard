"use client";

import React, { useEffect, useState } from "react";
import {
  Smartphone,
  Bell,
  CheckCircle2,
  AlertTriangle,
  X,
  ExternalLink,
  Send,
  ShieldCheck,
  RefreshCw,
  Copy,
  Check,
  HelpCircle,
  Radio,
} from "lucide-react";
import {
  fetchVapidPublicKey,
  generateVapidKeys,
  subscribeWebPush,
  unsubscribeWebPush,
  sendTestWebPush,
  sendTestNtfy,
  fetchNotificationHealth,
} from "@/lib/api";

interface PhoneAlertsModalProps {
  isOpen: boolean;
  onClose: () => void;
  operatorUser?: string;
}

// Convert Base64 URL-safe string to Uint8Array for PushManager
function urlBase64ToUint8Array(base64String: string): ArrayBuffer {
  const padding = "=".repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, "+").replace(/_/g, "/");
  const rawData = window.atob(base64);
  const buffer = new ArrayBuffer(rawData.length);
  const outputArray = new Uint8Array(buffer);
  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i);
  }
  return buffer;
}

export function PhoneAlertsModal({
  isOpen,
  onClose,
  operatorUser = "FlightDirector",
}: PhoneAlertsModalProps) {
  const [activeTab, setActiveTab] = useState<"webpush" | "ntfy">("webpush");

  // Web Push State
  const [browserSupported, setBrowserSupported] = useState<boolean>(true);
  const [permission, setPermission] = useState<string>("default");
  const [vapidStatus, setVapidStatus] = useState<string>("CHECKING");
  const [vapidKey, setVapidKey] = useState<string | null>(null);
  const [isSubscribed, setIsSubscribed] = useState<boolean>(false);
  const [subscriptionEndpoint, setSubscriptionEndpoint] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [testResult, setTestResult] = useState<string | null>(null);
  const [generatedKeys, setGeneratedKeys] = useState<{ pub: string; priv: string } | null>(null);
  const [copiedKey, setCopiedKey] = useState<boolean>(false);

  // ntfy State
  const [ntfyTopic, setNtfyTopic] = useState<string>("astraguard_alerts");
  const [ntfyServer, setNtfyServer] = useState<string>("https://ntfy.sh");
  const [ntfyHealth, setNtfyHealth] = useState<string>("CHECKING");
  const [ntfySending, setNtfySending] = useState<boolean>(false);
  const [ntfyResult, setNtfyResult] = useState<any | null>(null);

  useEffect(() => {
    if (!isOpen) return;

    // Check browser Push support
    if (typeof window !== "undefined") {
      const supported = "serviceWorker" in navigator && "PushManager" in window && "Notification" in window;
      setBrowserSupported(supported);
      if ("Notification" in window) {
        setPermission(Notification.permission);
      }
    }

    // Check existing push subscription and VAPID key
    checkWebPushStatus();
    checkHealth();
  }, [isOpen]);

  const checkWebPushStatus = async () => {
    try {
      const vapidRes = await fetchVapidPublicKey();
      setVapidStatus(vapidRes.status);
      setVapidKey(vapidRes.public_key);

      if ("serviceWorker" in navigator && "PushManager" in window) {
        const reg = await navigator.serviceWorker.getRegistration();
        if (reg) {
          const sub = await reg.pushManager.getSubscription();
          if (sub) {
            setIsSubscribed(true);
            setSubscriptionEndpoint(sub.endpoint);
          } else {
            setIsSubscribed(false);
            setSubscriptionEndpoint(null);
          }
        }
      }
    } catch (e) {
      console.warn("Failed checking push status:", e);
      setVapidStatus("ERROR");
    }
  };

  const checkHealth = async () => {
    try {
      const health = await fetchNotificationHealth();
      const ntfyProvider = health.providers?.find((p) => p.type === "ntfy");
      if (ntfyProvider) {
        setNtfyHealth(ntfyProvider.status);
      }
    } catch {
      setNtfyHealth("PENDING VERIFICATION");
    }
  };

  const handleSubscribeWebPush = async () => {
    setLoading(true);
    setTestResult(null);
    try {
      if (!("serviceWorker" in navigator)) {
        throw new Error("Service Worker is not supported in this browser.");
      }

      // Request notification permission
      const perm = await Notification.requestPermission();
      setPermission(perm);
      if (perm !== "granted") {
        throw new Error("Notification permission was denied by operator.");
      }

      if (!vapidKey) {
        throw new Error("VAPID public key is not configured on the backend.");
      }

      // Register Service Worker
      const reg = await navigator.serviceWorker.register("/sw.js", { scope: "/" });
      await navigator.serviceWorker.ready;

      // Subscribe to PushManager
      const convertedVapidKey = urlBase64ToUint8Array(vapidKey);
      const sub = await reg.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: convertedVapidKey,
      });

      const subJson = sub.toJSON();
      const p256dh = subJson.keys?.p256dh || "";
      const auth = subJson.keys?.auth || "";

      // Post subscription to backend
      await subscribeWebPush({
        endpoint: sub.endpoint,
        keys: { p256dh, auth },
        user_id: operatorUser,
        user_agent: navigator.userAgent,
      });

      setIsSubscribed(true);
      setSubscriptionEndpoint(sub.endpoint);
      setTestResult("Device successfully subscribed! Push notifications are active.");
    } catch (err: any) {
      setTestResult(`Subscription failed: ${err.message || err}`);
    } finally {
      setLoading(false);
    }
  };

  const handleUnsubscribeWebPush = async () => {
    setLoading(true);
    try {
      if ("serviceWorker" in navigator) {
        const reg = await navigator.serviceWorker.getRegistration();
        if (reg) {
          const sub = await reg.pushManager.getSubscription();
          if (sub) {
            await sub.unsubscribe();
            await unsubscribeWebPush(sub.endpoint);
          }
        }
      }
      setIsSubscribed(false);
      setSubscriptionEndpoint(null);
      setTestResult("Unsubscribed from browser push notifications.");
    } catch (err: any) {
      setTestResult(`Unsubscribe failed: ${err.message || err}`);
    } finally {
      setLoading(false);
    }
  };

  const handleSendTestPush = async () => {
    setLoading(true);
    setTestResult(null);
    try {
      const res = await sendTestWebPush();
      setTestResult(`Test alert dispatched: ${res.delivered_count} delivered to browser drawer.`);
    } catch (err: any) {
      setTestResult(`Test dispatch error: ${err.message || err}`);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateKeys = async () => {
    try {
      const keys = await generateVapidKeys();
      setGeneratedKeys({ pub: keys.VAPID_PUBLIC_KEY, priv: keys.VAPID_PRIVATE_KEY });
    } catch (e: any) {
      alert(`Key generation failed: ${e.message}`);
    }
  };

  const handleSendTestNtfy = async () => {
    setNtfySending(true);
    setNtfyResult(null);
    try {
      const res = await sendTestNtfy(ntfyTopic, ntfyServer);
      setNtfyResult(res);
    } catch (err: any) {
      setNtfyResult({ error: err.message || "Failed to publish test alert." });
    } finally {
      setNtfySending(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="w-full max-w-2xl bg-charcoal border border-white/20 rounded-card shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Modal Header */}
        <div className="p-4 sm:p-5 border-b border-white/10 flex items-center justify-between bg-void/50">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded bg-arterial/10 border border-arterial/30">
              <Smartphone className="w-5 h-5 text-arterial" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base font-bold font-mono text-bone tracking-tight">
                  Mobile & Phone Alerts Center
                </h2>
                <span className="px-1.5 py-0.5 rounded text-[10px] font-mono font-bold bg-white/5 border border-white/10 text-ash">
                  Stage 3 Verified
                </span>
              </div>
              <p className="text-xs text-ash font-mono mt-0.5">
                Real push delivery to iOS / Android devices with signed lock-screen action buttons
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded hover:bg-white/10 text-pebble hover:text-bone transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tab Navigation */}
        <div className="flex items-center border-b border-white/10 bg-void/30 px-5 pt-3 gap-2">
          <button
            onClick={() => setActiveTab("webpush")}
            className={`px-4 py-2 font-mono text-xs font-semibold rounded-t border-t border-x transition-colors flex items-center gap-2 ${
              activeTab === "webpush"
                ? "bg-charcoal text-bone border-white/20 -mb-[1px]"
                : "border-transparent text-ash hover:text-bone hover:bg-white/5"
            }`}
          >
            <Radio className="w-3.5 h-3.5 text-sky-400" />
            <span>Browser Web Push (PWA)</span>
            {isSubscribed && (
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            )}
          </button>
          <button
            onClick={() => setActiveTab("ntfy")}
            className={`px-4 py-2 font-mono text-xs font-semibold rounded-t border-t border-x transition-colors flex items-center gap-2 ${
              activeTab === "ntfy"
                ? "bg-charcoal text-bone border-white/20 -mb-[1px]"
                : "border-transparent text-ash hover:text-bone hover:bg-white/5"
            }`}
          >
            <Bell className="w-3.5 h-3.5 text-cyan-400" />
            <span>ntfy.sh Mobile App (Zero Config)</span>
          </button>
        </div>

        {/* Tab Content */}
        <div className="p-5 overflow-y-auto space-y-5 text-xs font-sans">
          {activeTab === "webpush" ? (
            <div className="space-y-4">
              {/* Status Header Banner */}
              <div className="p-3.5 rounded bg-void/80 border border-white/10 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
                <div className="space-y-1">
                  <div className="flex items-center gap-2 font-mono">
                    <span className="text-pebble text-[11px]">CHANNEL STATUS:</span>
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        isSubscribed
                          ? "bg-emerald-950/60 text-emerald-400 border border-emerald-500/40"
                          : vapidStatus === "READY"
                          ? "bg-amber-950/60 text-amber-400 border border-amber-500/40"
                          : "bg-red-950/60 text-red-400 border border-arterial/40"
                      }`}
                    >
                      {isSubscribed
                        ? "CONNECTED"
                        : vapidStatus === "READY"
                        ? "PENDING SUBSCRIPTION"
                        : "NOT CONFIGURED"}
                    </span>
                  </div>
                  <p className="text-ash text-[11px]">
                    {isSubscribed
                      ? `Active push subscription bound to endpoint: ${subscriptionEndpoint ? subscriptionEndpoint.slice(0, 35) + "..." : "Registered"}`
                      : vapidStatus === "READY"
                      ? "VAPID cryptographic keys loaded. Ready to authorize device notifications."
                      : "VAPID_PUBLIC_KEY and VAPID_PRIVATE_KEY missing in environment."}
                  </p>
                </div>

                <button
                  onClick={checkWebPushStatus}
                  className="px-2.5 py-1 rounded bg-smoke hover:bg-white/10 border border-white/10 text-pebble hover:text-bone text-[11px] font-mono flex items-center gap-1.5 transition-colors self-stretch sm:self-auto justify-center"
                >
                  <RefreshCw className="w-3 h-3" />
                  <span>Refresh</span>
                </button>
              </div>

              {/* iOS Notice Alert */}
              <div className="p-3 rounded bg-sky-950/20 border border-sky-500/30 text-sky-200 text-[11px] space-y-1">
                <div className="flex items-center gap-1.5 font-bold font-mono">
                  <HelpCircle className="w-3.5 h-3.5 text-sky-400 shrink-0" />
                  <span>Apple iOS Notification Protocol:</span>
                </div>
                <p className="text-sky-300/80 leading-relaxed">
                  On iPhones and iPads (iOS 16.4+), Web Push requires adding ASTRA-GUARD to your Home Screen: tap the Share button in Safari, then tap <strong>&quot;Add to Home Screen&quot;</strong>. Launch from the Home Screen to enable instant push delivery.
                </p>
              </div>

              {/* Main Subscription Controls */}
              {!browserSupported ? (
                <div className="p-4 rounded bg-red-950/30 border border-red-500/30 text-red-300 text-xs font-mono">
                  Push notifications are not supported in this browser environment. Please use Chrome, Firefox, Edge, or Safari 16.4+.
                </div>
              ) : vapidStatus === "READY" ? (
                <div className="p-4 rounded bg-smoke/40 border border-white/10 space-y-4">
                  <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
                    <div className="space-y-0.5">
                      <h4 className="font-mono font-bold text-bone text-xs">
                        {isSubscribed ? "Browser Device Subscribed" : "Authorize This Device"}
                      </h4>
                      <p className="text-ash text-[11px]">
                        Browser Permission:{" "}
                        <span
                          className={`font-mono font-bold uppercase ${
                            permission === "granted"
                              ? "text-emerald-400"
                              : permission === "denied"
                              ? "text-arterial"
                              : "text-amber-400"
                          }`}
                        >
                          {permission}
                        </span>
                      </p>
                    </div>

                    <div className="flex flex-wrap items-center gap-2 w-full sm:w-auto">
                      {isSubscribed ? (
                        <>
                          <button
                            onClick={handleSendTestPush}
                            disabled={loading}
                            className="flex-1 sm:flex-none px-3.5 py-1.5 rounded-nav bg-emerald-600 hover:bg-emerald-500 text-white font-mono font-bold text-xs flex items-center justify-center gap-1.5 transition-colors disabled:opacity-50"
                          >
                            <Send className="w-3.5 h-3.5" />
                            <span>Send Real Test Push</span>
                          </button>
                          <button
                            onClick={handleUnsubscribeWebPush}
                            disabled={loading}
                            className="flex-1 sm:flex-none px-3 py-1.5 rounded-nav bg-charcoal hover:bg-white/10 border border-white/20 text-pebble hover:text-white font-mono text-xs transition-colors disabled:opacity-50"
                          >
                            Unsubscribe
                          </button>
                        </>
                      ) : (
                        <button
                          onClick={handleSubscribeWebPush}
                          disabled={loading}
                          className="w-full sm:w-auto px-4 py-2 rounded-nav bg-arterial hover:bg-red-600 text-white font-mono font-bold text-xs flex items-center justify-center gap-2 transition-colors disabled:opacity-50 shadow-lg shadow-arterial/20"
                        >
                          <Bell className="w-4 h-4" />
                          <span>{loading ? "Authorizing..." : "Enable Phone Alerts"}</span>
                        </button>
                      )}
                    </div>
                  </div>

                  {testResult && (
                    <div className="p-3 rounded bg-void border border-white/10 font-mono text-xs text-bone flex items-start gap-2">
                      <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                      <span>{testResult}</span>
                    </div>
                  )}
                </div>
              ) : (
                /* VAPID Missing Setup Guide */
                <div className="p-4 rounded bg-smoke/40 border border-white/10 space-y-3">
                  <div className="flex items-center gap-2 text-amber-300 font-mono font-bold text-xs">
                    <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
                    <span>Honest Provider Warning: VAPID Keys Missing</span>
                  </div>
                  <p className="text-ash text-[11px] leading-relaxed">
                    To send Web Push without third-party accounts, generate a cryptographic P-256 VAPID keypair and append them to your backend <code>.env</code> file:
                  </p>

                  <button
                    onClick={handleGenerateKeys}
                    className="px-3.5 py-1.5 rounded bg-smoke hover:bg-white/10 border border-white/20 font-mono text-xs text-bone flex items-center gap-1.5 transition-colors"
                  >
                    <span>Generate VAPID Keypair</span>
                  </button>

                  {generatedKeys && (
                    <div className="p-3 rounded bg-void border border-white/10 space-y-2 font-mono text-[11px]">
                      <div className="flex items-center justify-between text-pebble">
                        <span>Copy into apps/api/.env:</span>
                        <button
                          onClick={() => {
                            navigator.clipboard.writeText(
                              `VAPID_PUBLIC_KEY=${generatedKeys.pub}\nVAPID_PRIVATE_KEY="${generatedKeys.priv.replace(/\n/g, "\\n")}"`
                            );
                            setCopiedKey(true);
                            setTimeout(() => setCopiedKey(false), 2000);
                          }}
                          className="text-cyan-400 hover:text-cyan-300 flex items-center gap-1"
                        >
                          {copiedKey ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
                          <span>{copiedKey ? "Copied" : "Copy Env"}</span>
                        </button>
                      </div>
                      <pre className="text-ash bg-black/60 p-2 rounded overflow-x-auto text-[10px]">
                        VAPID_PUBLIC_KEY={generatedKeys.pub}
                        <br />
                        VAPID_PRIVATE_KEY=...
                      </pre>
                    </div>
                  )}
                </div>
              )}

              {/* Service Worker Architecture Note */}
              <div className="p-3 rounded bg-void/50 border border-white/5 space-y-1.5 text-pebble text-[11px]">
                <div className="flex items-center gap-1.5 text-ash font-mono font-semibold">
                  <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                  <span>Cryptographic Single-Use Action Architecture:</span>
                </div>
                <p className="leading-relaxed">
                  Web Push notifications bundle signed HMAC action tokens. Tapping <strong>Approve</strong> or <strong>Snooze 30m</strong> triggers a background fetch directly to <code>/api/v1/alerts/{`{id}`}/action-token/{`{token}`}</code>. Single-use tokens expire in 24h and instantly halt escalation.
                </p>
              </div>
            </div>
          ) : (
            /* ntfy Tab Content */
            <div className="space-y-4">
              {/* Status Header Banner */}
              <div className="p-3.5 rounded bg-void/80 border border-white/10 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
                <div className="space-y-1">
                  <div className="flex items-center gap-2 font-mono">
                    <span className="text-pebble text-[11px]">NTFY PROVIDER STATUS:</span>
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        ntfyHealth === "CONNECTED"
                          ? "bg-emerald-950/60 text-emerald-400 border border-emerald-500/40"
                          : "bg-cyan-950/60 text-cyan-400 border border-cyan-500/40"
                      }`}
                    >
                      {ntfyHealth}
                    </span>
                  </div>
                  <p className="text-ash text-[11px]">
                    Zero-config instant push channel via open-source ntfy.sh network. Native Android & iOS app.
                  </p>
                </div>

                <a
                  href={`${ntfyServer}/${ntfyTopic}`}
                  target="_blank"
                  rel="noreferrer"
                  className="px-3 py-1.5 rounded bg-smoke hover:bg-white/10 border border-cyan-500/30 text-cyan-300 font-mono text-xs flex items-center gap-1.5 transition-colors self-stretch sm:self-auto justify-center"
                >
                  <ExternalLink className="w-3.5 h-3.5" />
                  <span>Open Topic Web View</span>
                </a>
              </div>

              {/* 3 Step Setup Guide */}
              <div className="p-4 rounded bg-smoke/40 border border-white/10 space-y-3">
                <h4 className="font-mono font-bold text-bone text-xs">
                  How to Receive Lock-Screen Alerts on Any Phone:
                </h4>
                <ol className="list-decimal list-inside space-y-2 text-ash text-[11px] leading-relaxed">
                  <li>
                    Install the free <strong>ntfy app</strong> on your phone (
                    <a
                      href="https://play.google.com/store/apps/details?id=io.heckel.ntfy"
                      target="_blank"
                      rel="noreferrer"
                      className="text-cyan-400 underline ml-1"
                    >
                      Google Play
                    </a>{" "}
                    or{" "}
                    <a
                      href="https://apps.apple.com/us/app/ntfy/id1625396347"
                      target="_blank"
                      rel="noreferrer"
                      className="text-cyan-400 underline ml-1"
                    >
                      Apple App Store
                    </a>
                    ).
                  </li>
                  <li>
                    Tap <strong>+ Subscribe to topic</strong> and enter:
                    <div className="mt-1 flex items-center gap-2">
                      <input
                        type="text"
                        value={ntfyTopic}
                        onChange={(e) => setNtfyTopic(e.target.value)}
                        className="px-2.5 py-1 rounded bg-black/60 border border-white/20 text-bone font-mono text-xs focus:outline-none focus:border-cyan-500"
                        placeholder="astraguard_alerts"
                      />
                      <span className="text-pebble text-[10px]">
                        URL: <code>{ntfyServer}/{ntfyTopic}</code>
                      </span>
                    </div>
                  </li>
                  <li>
                    When critical space hazards trigger, your phone will ring and show interactive <strong>[Approve]</strong> and <strong>[Snooze 30m]</strong> buttons right on your lock screen!
                  </li>
                </ol>

                <div className="pt-2 flex flex-col sm:flex-row items-stretch sm:items-center gap-2">
                  <button
                    onClick={handleSendTestNtfy}
                    disabled={ntfySending}
                    className="px-4 py-2 rounded-nav bg-cyan-600 hover:bg-cyan-500 text-white font-mono font-bold text-xs flex items-center justify-center gap-2 transition-colors disabled:opacity-50"
                  >
                    <Send className="w-3.5 h-3.5" />
                    <span>{ntfySending ? "Publishing..." : "Send Real Test Alert to ntfy"}</span>
                  </button>
                  <a
                    href={`${ntfyServer}/${ntfyTopic}`}
                    target="_blank"
                    rel="noreferrer"
                    className="px-3 py-2 rounded-nav bg-charcoal hover:bg-white/10 border border-white/20 font-mono text-xs text-pebble hover:text-white flex items-center justify-center gap-1.5 transition-colors"
                  >
                    <span>Inspect Live Topic Stream</span>
                    <ExternalLink className="w-3 h-3" />
                  </a>
                </div>

                {ntfyResult && (
                  <div
                    className={`p-3 rounded border font-mono text-xs ${
                      ntfyResult.error
                        ? "bg-red-950/40 border-red-500/40 text-red-300"
                        : "bg-emerald-950/40 border-emerald-500/40 text-emerald-300"
                    }`}
                  >
                    {ntfyResult.error ? (
                      <div>Error: {ntfyResult.error}</div>
                    ) : (
                      <div className="space-y-1">
                        <div className="flex items-center gap-1.5 font-bold">
                          <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                          <span>ntfy Alert Delivered Successfully!</span>
                        </div>
                        <div className="text-[11px] text-ash">
                          Topic: <strong>{ntfyResult.topic}</strong> &bull; Message ID:{" "}
                          <code>{ntfyResult.provider_message_id}</code>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="p-4 border-t border-white/10 bg-void/50 flex items-center justify-between">
          <span className="text-[11px] text-pebble font-mono">
            Human-in-the-Loop Advisory Protocol &bull; Operational Safety
          </span>
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-nav bg-smoke hover:bg-white/10 border border-white/20 font-mono text-xs text-bone transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
