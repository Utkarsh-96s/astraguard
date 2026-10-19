"use client";

import { useEffect, useState } from "react";
import { Activity, AlertTriangle, ArrowUpRight, CheckCircle2, Database, Orbit, Radio, Shield, Waves } from "lucide-react";

interface HealthData {
  status: string;
  version: string;
  timestamp: string;
  environment: string;
  database_connected: boolean;
  message?: string;
}

export default function Home() {
  const [health, setHealth] = useState<HealthData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchHealth = async () => {
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
        const res = await fetch(`${apiUrl}/healthz`, { cache: "no-store" });
        if (!res.ok) {
          throw new Error(`API responded with status: ${res.status}`);
        }
        const data = await res.json();
        setHealth(data);
        setError(null);
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : "Failed to connect to API backend";
        setError(msg);
      } finally {
        setLoading(false);
      }
    };

    fetchHealth();
    const interval = setInterval(fetchHealth, 8000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen bg-void text-bone selection:bg-arterial selection:text-bone">
      {/* Top Floating Navigation per design.md */}
      <header className="w-full border-b border-iron/30 px-6 py-4 flex items-center justify-between backdrop-blur-md sticky top-0 z-50 bg-void/80">
        <div className="flex items-center gap-3">
          <div className="w-2.5 h-2.5 rounded-full bg-arterial animate-pulse" />
          <span className="font-bold text-xl tracking-tight uppercase text-bone">
            ASTRA<span className="text-arterial font-normal">·</span>GUARD
          </span>
          <span className="badge-simulated ml-2">SIMULATED</span>
        </div>

        <nav className="hidden md:flex items-center gap-8 text-xs uppercase tracking-nav text-ash">
          <a href="#overview" className="hover:text-bone transition-colors text-bone font-medium">OVERVIEW</a>
          <a href="#health" className="hover:text-bone transition-colors">HEALTH AI</a>
          <a href="#debris" className="hover:text-bone transition-colors">DEBRIS RISK</a>
          <a href="#disaster" className="hover:text-bone transition-colors">DISASTER AI</a>
          <a href="#fusion" className="hover:text-bone transition-colors">RISK ENGINE</a>
          <a href="#models" className="hover:text-bone transition-colors">MODELS</a>
        </nav>

        <div className="flex items-center gap-4">
          <div className="hidden sm:flex items-center gap-2 text-xs border border-ash/20 px-3 py-1.5 rounded-card">
            <span className="text-pebble">CORE:</span>
            {loading ? (
              <span className="text-ash animate-pulse">CONNECTING...</span>
            ) : health?.status === "ok" ? (
              <span className="text-emerald-400 font-medium flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                ONLINE (v{health.version})
              </span>
            ) : (
              <span className="text-arterial font-medium flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-arterial" />
                OFFLINE
              </span>
            )}
          </div>

          <a
            href="#demo"
            className="flex items-center gap-1 text-xs uppercase tracking-nav px-4 py-2 rounded-card border border-ash/40 hover:border-bone text-bone hover:bg-smoke/30 transition-all"
          >
            DEMO MODE <ArrowUpRight className="w-3.5 h-3.5 text-ash" />
          </a>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="max-w-7xl mx-auto px-6 py-12 space-y-16">
        {/* Hero Section per design.md */}
        <section id="overview" className="pt-8 pb-4 relative">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-card border border-iron/50 text-xs text-ash mb-6">
            <Shield className="w-3.5 h-3.5 text-arterial" />
            <span>AITHON 2.0 · Team OMEN · Track 11: Aerospace, Telemetry & SpaceTech</span>
          </div>

          <div className="space-y-4">
            <h1 className="text-5xl md:text-7xl font-bold tracking-tight text-bone font-display max-w-4xl">
              MISSION <span className="font-serif italic font-light text-ash">safety</span>
              <br />
              INTELLIGENCE
            </h1>
            <p className="text-ash text-base md:text-lg max-w-2xl font-light leading-relaxed pt-2">
              Autonomous telemetry anomaly detection, debris collision risk screening, and Earth disaster
              observation fused into an explainable Mission Risk Score with human-in-the-loop recommendations.
            </p>
          </div>

          <div className="mt-8 flex flex-wrap gap-4">
            <div className="border border-arterial bg-smoke/20 px-5 py-3 rounded-card flex items-center gap-3">
              <div className="w-3 h-3 rounded-full bg-arterial" />
              <div>
                <div className="text-xs uppercase tracking-nav text-pebble">ADVISORY SYSTEM</div>
                <div className="text-sm font-semibold text-bone">Human-in-the-Loop Approval Required</div>
              </div>
            </div>

            <div className="border border-iron/40 bg-smoke/10 px-5 py-3 rounded-card flex items-center gap-3">
              <Radio className="w-4 h-4 text-ash" />
              <div>
                <div className="text-xs uppercase tracking-nav text-pebble">INGESTION PIPELINE</div>
                <div className="text-sm font-semibold text-bone">FastAPI · SGP4 · Time-Series Hypertables</div>
              </div>
            </div>
          </div>
        </section>

        {/* Live System Diagnostics Card */}
        <section className="border border-iron/40 bg-charcoal/60 rounded-panel p-6 shadow-glass relative overflow-hidden">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-iron/30 pb-4 mb-6">
            <div className="flex items-center gap-3">
              <Database className="w-5 h-5 text-ash" />
              <div>
                <h3 className="text-sm font-bold uppercase tracking-nav text-bone">Backend Foundation & Healthz</h3>
                <p className="text-xs text-pebble">FastAPI + SQLAlchemy + TimescaleDB baseline connectivity</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-ash">Target:</span>
              <code className="text-xs bg-smoke/80 px-2 py-1 rounded text-bone border border-iron/40">
                /healthz
              </code>
            </div>
          </div>

          {loading ? (
            <div className="py-8 text-center text-ash text-sm animate-pulse">
              Querying API backend at {process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}...
            </div>
          ) : error ? (
            <div className="bg-arterial/10 border border-arterial/30 rounded-card p-4 flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-arterial shrink-0 mt-0.5" />
              <div>
                <div className="text-sm font-semibold text-bone">API Backend Offline or Initializing</div>
                <div className="text-xs text-ash mt-1">{error}</div>
                <div className="text-xs text-pebble mt-2">
                  Verify backend container or local uvicorn instance: <code className="text-bone">make dev-api</code>
                </div>
              </div>
            </div>
          ) : (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-smoke/30 p-4 rounded-card border border-iron/30">
                <div className="text-xs uppercase tracking-nav text-pebble">SERVICE STATUS</div>
                <div className="text-base font-bold text-emerald-400 mt-1 flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4" />
                  {health?.status.toUpperCase()}
                </div>
              </div>
              <div className="bg-smoke/30 p-4 rounded-card border border-iron/30">
                <div className="text-xs uppercase tracking-nav text-pebble">API VERSION</div>
                <div className="text-base font-bold text-bone mt-1">v{health?.version}</div>
              </div>
              <div className="bg-smoke/30 p-4 rounded-card border border-iron/30">
                <div className="text-xs uppercase tracking-nav text-pebble">DATABASE</div>
                <div className="text-base font-bold mt-1">
                  {health?.database_connected ? (
                    <span className="text-emerald-400 flex items-center gap-1.5">
                      <span className="w-2 h-2 rounded-full bg-emerald-400" /> CONNECTED
                    </span>
                  ) : (
                    <span className="text-amber-400 flex items-center gap-1.5">
                      <span className="w-2 h-2 rounded-full bg-amber-400" /> PENDING
                    </span>
                  )}
                </div>
              </div>
              <div className="bg-smoke/30 p-4 rounded-card border border-iron/30">
                <div className="text-xs uppercase tracking-nav text-pebble">ENVIRONMENT</div>
                <div className="text-base font-bold text-bone mt-1 uppercase">{health?.environment}</div>
              </div>
            </div>
          )}
        </section>

        {/* AI Domains Architecture Grid */}
        <section className="space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-2xl font-bold tracking-tight text-bone font-display uppercase">
              Core Intelligence Modules
            </h2>
            <span className="text-xs text-pebble tracking-nav uppercase">Architecture §5</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Domain 1: Health AI */}
            <div className="bg-smoke/20 border border-iron/40 rounded-panel p-6 space-y-4 hover:border-ash/50 transition-colors">
              <div className="flex items-center justify-between">
                <div className="w-8 h-8 rounded-card bg-charcoal flex items-center justify-center border border-iron/40">
                  <Activity className="w-4 h-4 text-ash" />
                </div>
                <span className="text-xs uppercase tracking-nav text-pebble">Module 01</span>
              </div>
              <div>
                <h3 className="text-lg font-bold text-bone">Spacecraft Health AI</h3>
                <p className="text-xs text-ash mt-1">
                  Isolation Forest baseline + LSTM autoencoder detecting telemetry faults with channel-level SHAP attribution.
                </p>
              </div>
              <div className="pt-2 border-t border-iron/20 flex items-center justify-between text-xs text-pebble">
                <span>Model: LSTM-AE + IsoForest</span>
                <span className="text-bone">Phase 2</span>
              </div>
            </div>

            {/* Domain 2: Debris Risk */}
            <div className="bg-smoke/20 border border-iron/40 rounded-panel p-6 space-y-4 hover:border-ash/50 transition-colors">
              <div className="flex items-center justify-between">
                <div className="w-8 h-8 rounded-card bg-charcoal flex items-center justify-center border border-iron/40">
                  <Orbit className="w-4 h-4 text-ash" />
                </div>
                <span className="text-xs uppercase tracking-nav text-pebble">Module 02</span>
              </div>
              <div>
                <h3 className="text-lg font-bold text-bone">Debris Collision Risk AI</h3>
                <p className="text-xs text-ash mt-1">
                  SGP4 72-hour orbit propagation, screening-grade Foster Pc estimation, and XGBoost CDM trend classification.
                </p>
              </div>
              <div className="pt-2 border-t border-iron/20 flex items-center justify-between text-xs text-pebble">
                <span>Model: SGP4 + XGBoost</span>
                <span className="text-bone">Phase 3</span>
              </div>
            </div>

            {/* Domain 3: Disaster AI */}
            <div className="bg-smoke/20 border border-iron/40 rounded-panel p-6 space-y-4 hover:border-ash/50 transition-colors">
              <div className="flex items-center justify-between">
                <div className="w-8 h-8 rounded-card bg-charcoal flex items-center justify-center border border-iron/40">
                  <Waves className="w-4 h-4 text-ash" />
                </div>
                <span className="text-xs uppercase tracking-nav text-pebble">Module 03</span>
              </div>
              <div>
                <h3 className="text-lg font-bold text-bone">Disaster Intelligence AI</h3>
                <p className="text-xs text-ash mt-1">
                  Ground-segment flood/fire segmentation via U-Net and dynamic observation prioritization scoring.
                </p>
              </div>
              <div className="pt-2 border-t border-iron/20 flex items-center justify-between text-xs text-pebble">
                <span>Model: U-Net (Sen1Floods11)</span>
                <span className="text-bone">Phase 4</span>
              </div>
            </div>
          </div>
        </section>

        {/* Risk Fusion Engine Preview */}
        <section id="fusion" className="border border-arterial/60 bg-charcoal/40 rounded-panel p-8 space-y-6 relative">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-2 text-xs uppercase tracking-nav text-arterial font-bold">
                <span className="w-2 h-2 rounded-full bg-arterial" />
                Fusion Engine · Architecture §5.4
              </div>
              <h3 className="text-2xl font-bold text-bone mt-1">Unified Mission Risk Score</h3>
              <p className="text-xs text-ash mt-1 max-w-xl">
                Noisy-OR probabilistic hazard fusion: <code className="text-bone">R_safety = 1 − (1 − r_h)(1 − r_d)</code>,
                weighted with Earth Observation mission priorities and hard safety overrides.
              </p>
            </div>
            <div className="border border-iron/40 bg-smoke/40 px-6 py-4 rounded-card text-center">
              <div className="text-xs uppercase tracking-nav text-pebble">BASELINE RISK LEVEL</div>
              <div className="text-2xl font-bold text-emerald-400 mt-1">NOMINAL (12/100)</div>
              <div className="text-[11px] text-pebble mt-0.5">Demo Mode Ready</div>
            </div>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-4 border-t border-iron/20 text-xs">
            <div>
              <span className="text-pebble block">NOMINAL</span>
              <span className="font-semibold text-emerald-400">0 – 25</span>
            </div>
            <div>
              <span className="text-pebble block">WATCH</span>
              <span className="font-semibold text-blue-400">25 – 50</span>
            </div>
            <div>
              <span className="text-pebble block">WARNING</span>
              <span className="font-semibold text-amber-400">50 – 75</span>
            </div>
            <div>
              <span className="text-pebble block">CRITICAL</span>
              <span className="font-semibold text-arterial">75 – 100 (Pc ≥ 1e-4)</span>
            </div>
          </div>
        </section>
      </main>

      {/* Footer per design.md */}
      <footer className="mt-auto border-t border-iron/30 bg-charcoal py-10 px-6">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-6 text-xs text-ash">
          <div className="flex items-center gap-3">
            <span className="font-bold text-bone uppercase">ASTRA-GUARD</span>
            <span>·</span>
            <span>AI Space Mission Safety & Intelligence</span>
          </div>
          <div>
            Team OMEN · AITHON 2.0 (AIESA) · Track 11: Aerospace, Telemetry & SpaceTech
          </div>
          <div className="text-pebble">
            Rules binding · Advisory only · No automated command execution
          </div>
        </div>
      </footer>
    </div>
  );
}
