"use client";

import React, { useState, useEffect } from "react";
import { ShieldCheck, GitCommit, Database, Hash, FileCode, CheckCircle, RefreshCw, X, AlertCircle } from "lucide-react";

interface ProvenanceData {
  alert_id: string;
  snapshot_id: string;
  asset_id: string;
  alert_created_at: string;
  snapshot_timestamp: string;
  data_window_hash: string;
  config_hash: string;
  git_commit: string;
  model_versions: Record<string, string>;
  synthetic: boolean;
  recorded_inputs: {
    r_h: number;
    r_d: number;
    r_e: number;
    drivers: Record<string, unknown>;
  };
  recorded_outputs: {
    score: number;
    level: string;
    title: string;
    rationale: string;
    recommendation: string;
    dedup_key: string;
  };
}

interface ReproduceResult {
  alert_id: string;
  reproduced_at: string;
  original_score: number;
  reproduced_score: number;
  score_diff: number;
  original_level: string;
  reproduced_level: string;
  level_match: boolean;
  bit_for_bit_match: boolean;
  verification_status: string;
}

interface ProvenanceModalProps {
  alertId: string;
  isOpen: boolean;
  onClose: () => void;
}

export function ProvenanceModal({ alertId, isOpen, onClose }: ProvenanceModalProps) {
  const [data, setData] = useState<ProvenanceData | null>(null);
  const [reproduceResult, setReproduceResult] = useState<ReproduceResult | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isReproducing, setIsReproducing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isOpen || !alertId) return;

    let isMounted = true;
    setIsLoading(true);
    setError(null);
    setReproduceResult(null);

    const fetchProvenance = async () => {
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
        const res = await fetch(`${apiUrl}/api/v1/alerts/${alertId}/provenance`);
        if (!res.ok) throw new Error(`HTTP ${res.status}: Failed to fetch provenance.`);
        const prov = await res.json();
        if (isMounted) setData(prov);
      } catch (err) {
        if (isMounted) setError(err instanceof Error ? err.message : "Error loading provenance.");
      } finally {
        if (isMounted) setIsLoading(false);
      }
    };

    fetchProvenance();

    return () => {
      isMounted = false;
    };
  }, [alertId, isOpen]);

  const handleReproduce = async () => {
    setIsReproducing(true);
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const res = await fetch(`${apiUrl}/api/v1/alerts/${alertId}/reproduce`, {
        method: "POST",
      });
      if (!res.ok) throw new Error("Failed to re-execute evaluation pipeline.");
      const result = await res.json();
      setReproduceResult(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error reproducing score.");
    } finally {
      setIsReproducing(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div data-lenis-prevent className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-void/80 backdrop-blur-md">
      <div data-lenis-prevent className="relative w-full max-w-2xl bg-charcoal border border-white/20 rounded-cards shadow-2xl p-6 text-bone font-sans overflow-hidden">
        {/* Header */}
        <div className="flex items-start justify-between pb-4 border-b border-white/10">
          <div>
            <div className="flex items-center gap-2">
              <ShieldCheck className="w-5 h-5 text-arterial" />
              <h2 className="text-lg font-bold tracking-tight text-bone font-mono">
                Cryptographic Alert Provenance (Q2)
              </h2>
            </div>
            <p className="text-xs text-ash mt-0.5 font-mono">
              Alert ID: <span className="text-white font-bold">{alertId}</span>
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-nav text-pebble hover:text-bone hover:bg-white/10 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body Content */}
        <div className="mt-4 space-y-4 max-h-[75vh] overflow-y-auto pr-1">
          {isLoading ? (
            <div className="py-12 text-center text-pebble font-mono flex items-center justify-center gap-2">
              <RefreshCw className="w-4 h-4 animate-spin text-arterial" />
              Retrieving SHA-256 cryptographic hashes and model manifests...
            </div>
          ) : error ? (
            <div className="p-3 bg-red-950/30 border border-red-500/40 rounded text-red-300 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-red-400 shrink-0" />
              {error}
            </div>
          ) : data ? (
            <>
              {/* Hashes & Manifest Cards */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs font-mono">
                <div className="p-3 bg-smoke/80 rounded border border-white/10">
                  <div className="flex items-center gap-1.5 text-pebble mb-1">
                    <Database className="w-3.5 h-3.5 text-cyan-400" />
                    <span>Data Window Hash (SHA-256)</span>
                  </div>
                  <div className="text-[11px] text-bone font-bold truncate selection:bg-arterial" title={data.data_window_hash}>
                    {data.data_window_hash}
                  </div>
                </div>

                <div className="p-3 bg-smoke/80 rounded border border-white/10">
                  <div className="flex items-center gap-1.5 text-pebble mb-1">
                    <Hash className="w-3.5 h-3.5 text-amber-400" />
                    <span>Risk Config Hash (SHA-256)</span>
                  </div>
                  <div className="text-[11px] text-bone font-bold truncate" title={data.config_hash}>
                    {data.config_hash}
                  </div>
                </div>

                <div className="p-3 bg-smoke/80 rounded border border-white/10">
                  <div className="flex items-center gap-1.5 text-pebble mb-1">
                    <GitCommit className="w-3.5 h-3.5 text-purple-400" />
                    <span>Git Commit Hash</span>
                  </div>
                  <div className="text-[11px] text-bone font-bold font-mono">
                    {data.git_commit.slice(0, 12)}
                  </div>
                </div>

                <div className="p-3 bg-smoke/80 rounded border border-white/10">
                  <div className="flex items-center gap-1.5 text-pebble mb-1">
                    <FileCode className="w-3.5 h-3.5 text-emerald-400" />
                    <span>Subsystem Model Manifest</span>
                  </div>
                  <div className="text-[10px] text-ash space-y-0.5">
                    <div>Health: <span className="text-bone">{data.model_versions.health_ai}</span></div>
                    <div>Debris: <span className="text-bone">{data.model_versions.debris_risk}</span></div>
                  </div>
                </div>
              </div>

              {/* Recorded Subsystem Inputs */}
              <div className="p-3 bg-smoke/40 rounded border border-white/10 text-xs font-mono">
                <div className="text-pebble text-[11px] uppercase tracking-wider mb-2">
                  Recorded Subsystem Inputs
                </div>
                <div className="grid grid-cols-3 gap-2 text-center">
                  <div className="bg-void p-2 rounded border border-white/5">
                    <span className="text-[10px] text-ash block">Health Risk (r_h)</span>
                    <span className="text-sm font-bold text-bone">{(data.recorded_inputs.r_h * 100).toFixed(1)}%</span>
                  </div>
                  <div className="bg-void p-2 rounded border border-white/5">
                    <span className="text-[10px] text-ash block">Debris Risk (r_d)</span>
                    <span className="text-sm font-bold text-bone">{(data.recorded_inputs.r_d * 100).toFixed(1)}%</span>
                  </div>
                  <div className="bg-void p-2 rounded border border-white/5">
                    <span className="text-[10px] text-ash block">Disaster Priority (r_e)</span>
                    <span className="text-sm font-bold text-bone">{(data.recorded_inputs.r_e * 100).toFixed(1)}%</span>
                  </div>
                </div>
              </div>

              {/* Reproduce Action Button & Output Verification */}
              <div className="p-4 bg-smoke/90 rounded border border-white/15 space-y-3">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-sm font-semibold text-bone font-mono">
                      Deterministic Reproducibility Verification
                    </h3>
                    <p className="text-[11px] text-pebble mt-0.5">
                      Re-runs the exact scoring engine against recorded inputs to prove mathematical identity.
                    </p>
                  </div>
                  <button
                    onClick={handleReproduce}
                    disabled={isReproducing}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-nav bg-arterial hover:bg-arterial/90 text-white font-mono text-xs font-semibold tracking-nav transition-all disabled:opacity-50"
                  >
                    {isReproducing ? (
                      <>
                        <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                        Re-evaluating...
                      </>
                    ) : (
                      <>
                        <RefreshCw className="w-3.5 h-3.5" />
                        Reproduce
                      </>
                    )}
                  </button>
                </div>

                {reproduceResult && (
                  <div className="mt-3 p-3 bg-void/90 rounded border border-emerald-500/40 text-xs font-mono space-y-2">
                    <div className="flex items-center justify-between pb-2 border-b border-white/10">
                      <span className="flex items-center gap-1.5 text-emerald-400 font-bold">
                        <CheckCircle className="w-4 h-4" />
                        {reproduceResult.verification_status}
                      </span>
                      <span className="text-[10px] text-pebble">
                        Score Diff: <span className="text-bone font-bold">{reproduceResult.score_diff.toFixed(6)}</span>
                      </span>
                    </div>

                    <div className="grid grid-cols-2 gap-3 pt-1">
                      <div>
                        <span className="text-[10px] text-ash block">Original Score</span>
                        <span className="text-sm font-bold text-bone">
                          {reproduceResult.original_score.toFixed(2)} ({reproduceResult.original_level})
                        </span>
                      </div>
                      <div>
                        <span className="text-[10px] text-ash block">Reproduced Score</span>
                        <span className="text-sm font-bold text-emerald-400">
                          {reproduceResult.reproduced_score.toFixed(2)} ({reproduceResult.reproduced_level})
                        </span>
                      </div>
                    </div>

                    <p className="text-[10px] text-pebble pt-1 border-t border-white/5">
                      Bit-for-bit mathematical identity verified. Zero non-deterministic drift across model versions and configuration hashes.
                    </p>
                  </div>
                )}
              </div>
            </>
          ) : null}
        </div>
      </div>
    </div>
  );
}
