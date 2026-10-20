"use client";

import React, { useState, useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";
import { Compass, CheckCircle2, ChevronRight, ChevronLeft, X, Sparkles } from "lucide-react";
import tourSteps from "../lib/judge_tour.json";
import { useFeature } from "../lib/features";

interface JudgeTourOverlayProps {
  isOpen: boolean;
  onClose: () => void;
  initialStep?: number;
}

export function JudgeTourOverlay({ isOpen, onClose, initialStep = 1 }: JudgeTourOverlayProps) {
  const isEnabled = useFeature("guided_judge_tour");
  const router = useRouter();
  const pathname = usePathname();
  const [currentStepIndex, setCurrentStepIndex] = useState(initialStep - 1);

  useEffect(() => {
    if (initialStep >= 1 && initialStep <= tourSteps.length) {
      setCurrentStepIndex(initialStep - 1);
    }
  }, [initialStep]);

  if (!isEnabled || !isOpen) return null;

  const currentStep = tourSteps[currentStepIndex];
  const totalSteps = tourSteps.length;
  const isLast = currentStepIndex === totalSteps - 1;
  const isFirst = currentStepIndex === 0;

  const handleNext = () => {
    if (!isLast) {
      const nextIndex = currentStepIndex + 1;
      setCurrentStepIndex(nextIndex);
      const nextRoute = tourSteps[nextIndex].route;
      if (pathname !== nextRoute) {
        router.push(nextRoute);
      }
    } else {
      onClose();
    }
  };

  const handlePrev = () => {
    if (!isFirst) {
      const prevIndex = currentStepIndex - 1;
      setCurrentStepIndex(prevIndex);
      const prevRoute = tourSteps[prevIndex].route;
      if (pathname !== prevRoute) {
        router.push(prevRoute);
      }
    }
  };

  const handleJumpToStep = (index: number) => {
    setCurrentStepIndex(index);
    const targetRoute = tourSteps[index].route;
    if (pathname !== targetRoute) {
      router.push(targetRoute);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center p-4 bg-void/60 backdrop-blur-sm pointer-events-auto">
      <div className="relative w-full max-w-xl bg-charcoal border-2 border-arterial/60 rounded-cards shadow-2xl p-6 text-bone font-sans animate-in fade-in zoom-in-95 duration-200">
        {/* Step Header */}
        <div className="flex items-start justify-between pb-3 border-b border-white/10">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-nav bg-arterial/20 border border-arterial/50 flex items-center justify-center text-arterial">
              <Compass className="w-4 h-4 animate-spin-slow" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-[10px] font-mono uppercase tracking-widest text-pebble font-bold">
                  Guided Judge Tour (Q1)
                </span>
                <span className="px-2 py-0.5 rounded-full bg-arterial/20 border border-arterial/40 text-[9px] font-mono text-arterial font-bold">
                  {currentStep.badge}
                </span>
              </div>
              <h3 className="text-base font-bold text-bone font-mono mt-0.5">
                {currentStep.title}
              </h3>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-nav text-pebble hover:text-bone hover:bg-white/10 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Narrative Description */}
        <p className="mt-3 text-xs text-ash leading-relaxed">
          {currentStep.description}
        </p>

        {/* Key Innovations */}
        <div className="mt-3.5 bg-smoke/70 p-3 rounded border border-white/5 space-y-1.5 text-xs font-mono">
          <span className="text-[10px] text-pebble uppercase tracking-wider block font-bold mb-1">
            Core Technical Innovations:
          </span>
          {currentStep.key_innovations.map((item, idx) => (
            <div key={idx} className="flex items-start gap-2 text-[11px] text-bone">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0 mt-0.5" />
              <span>{item}</span>
            </div>
          ))}
        </div>

        {/* Step Indicator Dots & Navigation */}
        <div className="mt-5 pt-3 border-t border-white/10 flex items-center justify-between">
          <div className="flex items-center gap-1.5">
            {tourSteps.map((_, idx) => (
              <button
                key={idx}
                onClick={() => handleJumpToStep(idx)}
                className={`w-2.5 h-2.5 rounded-full transition-all ${
                  idx === currentStepIndex
                    ? "w-6 bg-arterial"
                    : "bg-iron hover:bg-pebble"
                }`}
                title={`Jump to step ${idx + 1}`}
              />
            ))}
            <span className="text-[10px] font-mono text-pebble ml-2">
              Step {currentStepIndex + 1} of {totalSteps}
            </span>
          </div>

          <div className="flex items-center gap-2">
            {!isFirst && (
              <button
                onClick={handlePrev}
                className="flex items-center gap-1 px-3 py-1.5 rounded-nav bg-smoke hover:bg-white/10 border border-white/10 text-xs font-mono text-ash hover:text-bone transition-all"
              >
                <ChevronLeft className="w-3.5 h-3.5" /> Prev
              </button>
            )}

            <button
              onClick={handleNext}
              className="flex items-center gap-1 px-4 py-1.5 rounded-nav bg-arterial hover:bg-arterial/90 text-white font-mono text-xs font-bold tracking-nav transition-all shadow-lg shadow-arterial/20"
            >
              {isLast ? "Complete Tour" : "Next Module"}
              {!isLast && <ChevronRight className="w-3.5 h-3.5" />}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export function JudgeTourTriggerButton({ onStartTour }: { onStartTour: () => void }) {
  const isEnabled = useFeature("guided_judge_tour");
  if (!isEnabled) return null;

  return (
    <button
      onClick={onStartTour}
      className="flex items-center gap-1.5 px-2.5 py-1 rounded-nav bg-arterial/10 hover:bg-arterial/20 border border-arterial/40 text-[11px] font-mono text-arterial font-semibold tracking-nav transition-all group shadow-sm hover:shadow-arterial/20"
      title="Launch Guided 6-Step Judge Tour (Q1)"
    >
      <Sparkles className="w-3.5 h-3.5 text-arterial group-hover:scale-110 transition-transform" />
      <span className="hidden sm:inline">JUDGE TOUR</span>
    </button>
  );
}
