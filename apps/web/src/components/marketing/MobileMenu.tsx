"use client";

import React, { useEffect } from "react";
import Link from "next/link";
import { Button } from "./Button";
import { ScenarioSelector } from "./ScenarioSelector";

import { Sun, Moon } from "lucide-react";
import { useTheme } from "../../lib/themeContext";

export interface MobileMenuProps {
  isOpen: boolean;
  onClose: () => void;
  links: Array<{ label: string; href: string }>;
}

export function MobileMenu({ isOpen, onClose, links }: MobileMenuProps) {
  const { theme, isNight, toggleTheme } = useTheme();

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
      className="fixed inset-0 z-50 bg-space-canvas text-space-fg flex flex-col justify-between p-6 sm:p-10 select-none overflow-y-auto transition-colors duration-300"
      style={{ fontFamily: "var(--font-d-din, var(--font-barlow, sans-serif))" }}
    >
      {/* Top Header */}
      <div className="flex items-center justify-between border-b border-space-separator pb-6">
        <span className="text-space-fg text-[14px] font-bold tracking-[0.10em] uppercase">
          ASTRA-GUARD
        </span>
        <button
          type="button"
          onClick={onClose}
          aria-label="Close Navigation Menu"
          className="border border-space-fg text-space-fg px-3 py-1.5 rounded text-[11px] font-bold uppercase tracking-[0.10em] hover:bg-space-fg/10"
        >
          CLOSE [ESC]
        </button>
      </div>

      {/* Nav Links */}
      <nav className="flex flex-col gap-6 py-12" aria-label="Mobile Navigation Links">
        {links.map((link) => (
          <Link
            key={link.label}
            href={link.href}
            onClick={onClose}
            className="text-space-fg text-[24px] sm:text-[32px] font-bold uppercase tracking-[0.04em] transition-colors hover:opacity-75"
            style={{ fontFamily: "var(--font-d-din-bold, var(--font-barlow, sans-serif))" }}
          >
            {link.label}
          </Link>
        ))}
      </nav>

      {/* Footer Controls */}
      <div className="border-t border-space-separator pt-6 flex flex-col gap-4">
        {/* Appearance Row */}
        <div className="flex items-center justify-between">
          <span className="text-space-secondary text-[11px] font-bold uppercase tracking-[0.10em]">
            APPEARANCE
          </span>
          <button
            type="button"
            onClick={toggleTheme}
            className="inline-flex items-center gap-1.5 border border-space-fg bg-transparent text-space-fg rounded-full px-3.5 py-1.5 text-[11px] font-bold uppercase tracking-[0.10em] hover:bg-space-fg/10 cursor-pointer"
          >
            {isNight ? (
              <>
                <Sun className="w-3.5 h-3.5 shrink-0" />
                <span>DAY MODE</span>
              </>
            ) : (
              <>
                <Moon className="w-3.5 h-3.5 shrink-0" />
                <span>NIGHT MODE</span>
              </>
            )}
          </button>
        </div>

        <div className="flex items-center justify-between">
          <span className="text-space-secondary text-[11px] font-bold uppercase tracking-[0.10em]">
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
