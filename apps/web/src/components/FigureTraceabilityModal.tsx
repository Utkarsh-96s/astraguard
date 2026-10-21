"use client";

import React from "react";
import { X, ShieldCheck, ExternalLink, Hash, Clock, GitCommit, Database, Tag } from "lucide-react";
import { FigureEntry } from "@/lib/api";

interface Props {
  figure: FigureEntry | null;
  isOpen: boolean;
  onClose: () => void;
}

export function FigureTraceabilityModal({ figure, isOpen, onClose }: Props) {
  if (!isOpen || !figure) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/85 backdrop-blur-sm select-none"
    >
      <div className="relative w-full max-w-2xl bg-[#050508] border border-white/20 rounded-[4px] p-6 text-[#f0f0fa] space-y-6 max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-start justify-between border-b border-white/10 pb-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="px-2 py-0.5 rounded-[4px] bg-white/10 border border-white/20 font-mono text-[11px] font-bold tracking-wider text-emerald-400 flex items-center gap-1.5">
                <ShieldCheck className="w-3.5 h-3.5" />
                VERIFIED EMPIRICAL ARTIFACT
              </span>
              <span className="font-mono text-xs text-white/50">{figure.figure_id}</span>
            </div>
            <h2 className="text-lg font-bold font-mono tracking-tight text-[#f0f0fa]">
              {figure.title}
            </h2>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-[4px] border border-white/20 text-white/70 hover:text-white hover:border-white transition-colors"
            aria-label="Close dialog"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Description */}
        <p className="text-xs text-white/70 font-sans leading-relaxed">
          {figure.description}
        </p>

        {/* Traceability Metadata Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs font-mono">
          <div className="p-3 bg-white/[0.03] border border-white/10 rounded-[4px] space-y-1">
            <div className="flex items-center gap-1.5 text-white/50 text-[10px] uppercase tracking-wider">
              <Database className="w-3 h-3" />
              Dataset Source
            </div>
            <div className="text-[#f0f0fa] font-bold truncate">{figure.dataset || "Synthetic & Benchmark"}</div>
          </div>

          <div className="p-3 bg-white/[0.03] border border-white/10 rounded-[4px] space-y-1">
            <div className="flex items-center gap-1.5 text-white/50 text-[10px] uppercase tracking-wider">
              <Hash className="w-3 h-3" />
              Data Fingerprint (SHA-256)
            </div>
            <div className="text-emerald-400 font-mono text-[11px] truncate">
              {figure.data_hash || "Deterministic Physics Seed"}
            </div>
          </div>

          <div className="p-3 bg-white/[0.03] border border-white/10 rounded-[4px] space-y-1">
            <div className="flex items-center gap-1.5 text-white/50 text-[10px] uppercase tracking-wider">
              <GitCommit className="w-3 h-3" />
              Commit Hash & Version
            </div>
            <div className="text-[#f0f0fa] font-bold">
              {figure.commit ? `commit ${figure.commit.slice(0, 7)}` : "HEAD"} · v{figure.model_version}
            </div>
          </div>

          <div className="p-3 bg-white/[0.03] border border-white/10 rounded-[4px] space-y-1">
            <div className="flex items-center gap-1.5 text-white/50 text-[10px] uppercase tracking-wider">
              <Clock className="w-3 h-3" />
              Evaluated Timestamp
            </div>
            <div className="text-[#f0f0fa] truncate">{figure.timestamp}</div>
          </div>
        </div>

        {/* Tags */}
        {figure.tags && figure.tags.length > 0 && (
          <div className="space-y-1.5">
            <div className="text-[10px] font-mono uppercase tracking-wider text-white/50 flex items-center gap-1">
              <Tag className="w-3 h-3" /> Tags
            </div>
            <div className="flex flex-wrap gap-1.5">
              {figure.tags.map((t) => (
                <span
                  key={t}
                  className="px-2 py-0.5 rounded-[4px] bg-white/[0.05] border border-white/10 text-[10px] font-mono text-white/70"
                >
                  #{t}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Full Provenance JSON */}
        <div className="space-y-1.5">
          <div className="text-[10px] font-mono uppercase tracking-wider text-white/50">
            Cryptographic Manifest Entry
          </div>
          <pre className="p-3 bg-black border border-white/10 rounded-[4px] text-[10px] font-mono text-emerald-400 overflow-x-auto max-h-36">
            {JSON.stringify(
              {
                figure_id: figure.figure_id,
                title: figure.title,
                dataset: figure.dataset,
                data_hash: figure.data_hash,
                commit: figure.commit,
                timestamp: figure.timestamp,
                url_svg: figure.url_svg,
                url_png: figure.url_png,
              },
              null,
              2
            )}
          </pre>
        </div>

        {/* Footer Actions */}
        <div className="flex items-center justify-between border-t border-white/10 pt-4">
          <div className="flex items-center gap-3">
            <a
              href={figure.url_svg}
              target="_blank"
              rel="noopener noreferrer"
              className="px-3 py-1.5 rounded-[4px] border border-white/20 text-xs font-mono text-white/80 hover:text-white hover:border-white transition-colors flex items-center gap-1.5"
            >
              <ExternalLink className="w-3.5 h-3.5" />
              View Raw SVG
            </a>
            <a
              href={figure.url_png}
              target="_blank"
              rel="noopener noreferrer"
              className="px-3 py-1.5 rounded-[4px] border border-white/20 text-xs font-mono text-white/80 hover:text-white hover:border-white transition-colors flex items-center gap-1.5"
            >
              <ExternalLink className="w-3.5 h-3.5" />
              View 2x PNG
            </a>
          </div>

          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-[4px] bg-white/10 border border-white/30 text-xs font-mono text-white hover:bg-white/20 transition-colors uppercase tracking-wider"
          >
            Close Audit
          </button>
        </div>
      </div>
    </div>
  );
}
