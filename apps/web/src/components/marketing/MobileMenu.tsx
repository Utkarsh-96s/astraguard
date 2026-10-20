"use client";

import React, { useEffect } from "react";
import Link from "next/link";
import { Button } from "./Button";
import { ScenarioSelector } from "./ScenarioSelector";

export interface MobileMenuProps {
  isOpen: boolean;
  onClose: () => void;
  links: Array<{ label: string; href: string }>;
}

export function MobileMenu({ isOpen, onClose, links }: MobileMenuProps) {
  // Lock body scroll and listen for Escape key
  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };

    document.body.style.overflow = "hidden";
    window.addEventListener("keydown", handleKeyDown);

    return () => {
      document.body.style.overflow = "";
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label="Navigation Menu"
      className="fixed inset-0 z-50 bg-[#000000] flex flex-col justify-between p-6 sm:p-10 select-none overflow-y-auto"
      style={{ fontFamily: "var(--font-d-din, var(--font-barlow, sans-serif))" }}
    >
      {/* Top Header */}
      <div className="flex items-center justify-between border-b border-[#404040] pb-6">
        <span className="text-[#f0f0fa] text-[14px] font-bold tracking-[0.10em] uppercase">
          ASTRA-GUARD
        </span>
        <button
          type="button"
          onClick={onClose}
          aria-label="Close Navigation Menu"
          className="border border-[#f0f0fa] text-[#f0f0fa] px-3 py-1.5 rounded text-[11px] font-bold uppercase tracking-[0.10em] hover:bg-[rgba(240,240,250,0.08)]"
        >
          CLOSE [ESC]
        </button>
      </div>

      {/* Nav Links */}
      <nav className="flex flex-col gap-6 py-12" aria-label="Mobile Navigation Links">
        {links.map((link) => (
          <a
            key={link.label}
            href={link.href}
            onClick={onClose}
            className="text-[#f0f0fa] text-[24px] sm:text-[32px] font-bold uppercase tracking-[0.04em] transition-colors hover:text-[#545457]"
            style={{ fontFamily: "var(--font-d-din-bold, var(--font-barlow, sans-serif))" }}
          >
            {link.label}
          </a>
        ))}
      </nav>

      {/* Footer Controls */}
      <div className="border-t border-[#404040] pt-6 flex flex-col gap-4">
        <div className="flex items-center justify-between">
          <span className="text-[#545457] text-[11px] font-bold uppercase tracking-[0.10em]">
            SCENARIO
          </span>
          <ScenarioSelector />
        </div>
        <Button variant="ghost" href="/dashboard" onClick={onClose} className="w-full">
          LAUNCH DASHBOARD
        </Button>
      </div>
    </div>
  );
}
