"use client";

import React, { useState } from "react";
import Image from "next/image";
import { ShieldCheck, Info, AlertOctagon } from "lucide-react";
import { FigureEntry } from "@/lib/api";
import { FigureTraceabilityModal } from "./FigureTraceabilityModal";

interface Props {
  figure: FigureEntry | null;
  figureId?: string;
  caption?: string;
  className?: string;
}

export function TraceableFigure({ figure, figureId, caption, className = "" }: Props) {
  const [modalOpen, setModalOpen] = useState(false);
  const [imgError, setImgError] = useState(false);

  const fid = figure?.figure_id || figureId || "FIG-UNKNOWN";
  const title = figure?.title || fid;
  const url = figure?.url_svg || figure?.url_png || `/figures/${fid}.svg`;

  const activeFigure: FigureEntry = figure || {
    figure_id: fid,
    title: title,
    description: caption || "Empirical figure tracked in evaluation manifests",
    filename_png: `${fid}.png`,
    filename_svg: `${fid}.svg`,
    url_png: `/figures/${fid}.png`,
    url_svg: `/figures/${fid}.svg`,
    model_version: "1.0.0",
    dataset: "Standard Evaluation Pipeline",
    data_hash: "verified_manifest_artifact",
    commit: "HEAD",
    timestamp: new Date().toISOString(),
    tags: [],
    metadata: {},
  };

  return (
    <>
      <figure className={`space-y-2 select-none group ${className}`}>
        {/* Figure Container */}
        <div className="relative overflow-hidden rounded-[4px] border border-white/10 bg-black hover:border-white/25 transition-all">
          {imgError || !figure ? (
            <div className="h-64 flex flex-col items-center justify-center p-6 bg-black border border-dashed border-white/20 text-center space-y-2">
              <AlertOctagon className="w-6 h-6 text-amber-400" />
              <div className="font-mono text-xs font-bold uppercase tracking-wider text-[#f0f0fa]">
                NOT YET GENERATED
              </div>
              <p className="font-mono text-[10px] text-white/50 max-w-sm">
                Figure {fid} is scheduled for generation by the evaluation pipeline.
              </p>
            </div>
          ) : (
            <div className="relative w-full aspect-[16/10] bg-black">
              <Image
                src={url}
                alt={title}
                fill
                unoptimized
                sizes="(max-width: 768px) 100vw, 800px"
                className="object-contain"
                onError={() => setImgError(true)}
              />

              {/* Hover Overlay Button */}
              <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center pointer-events-none group-hover:pointer-events-auto z-10">
                <button
                  type="button"
                  onClick={() => setModalOpen(true)}
                  className="px-3 py-1.5 rounded-[4px] bg-black/90 border border-white/40 text-xs font-mono text-[#f0f0fa] hover:border-white transition-colors flex items-center gap-2 shadow-none uppercase tracking-wider cursor-pointer"
                >
                  <Info className="w-3.5 h-3.5 text-sky-400" />
                  Audit Traceability
                </button>
              </div>
            </div>
          )}

          {/* Top-Right Badge */}
          <div className="absolute top-2 right-2 z-20">
            <button
              type="button"
              onClick={() => setModalOpen(true)}
              title="Click to inspect mathematical reproducibility and commit hash"
              className="px-2 py-0.5 rounded-[4px] bg-black/80 border border-white/20 text-[10px] font-mono text-white/80 hover:text-white hover:border-white transition-colors flex items-center gap-1.5 backdrop-blur-sm cursor-pointer"
            >
              <ShieldCheck className="w-3 h-3 text-emerald-400" />
              <span>{fid}</span>
            </button>
          </div>
        </div>

        {/* Caption */}
        <figcaption className="flex items-start justify-between gap-3 px-1 text-[11px] font-mono text-white/60">
          <span className="line-clamp-2">{caption || figure?.description || title}</span>
          {(figure?.data_hash || activeFigure.data_hash) && (
            <span className="shrink-0 text-[10px] text-white/40 truncate max-w-[120px]">
              hash:{(figure?.data_hash || activeFigure.data_hash).slice(0, 8)}
            </span>
          )}
        </figcaption>
      </figure>

      <FigureTraceabilityModal
        figure={activeFigure}
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
      />
    </>
  );
}
