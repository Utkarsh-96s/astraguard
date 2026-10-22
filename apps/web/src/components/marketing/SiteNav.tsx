"use client";

import React, { useState } from "react";
import Link from "next/link";
import { Button } from "./Button";
import { ScenarioSelector } from "./ScenarioSelector";
import { MobileMenu } from "./MobileMenu";

const NAV_LINKS = [
  { label: "MISSION", href: "/#mission" },
  { label: "HEALTH", href: "/#health" },
  { label: "DEBRIS", href: "/#debris" },
  { label: "EARTH", href: "/#earth" },
  { label: "TECH", href: "/technology" },
  { label: "ENGINE", href: "/#engine" },
  { label: "DEMO", href: "/#demo" },
  { label: "TEAM", href: "/#team" },
];

export function SiteNav() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <>
      {/* Skip to Content for a11y */}
      <a
        href="#mission"
        className="sr-only focus:not-sr-only focus:fixed focus:top-4 focus:left-4 z-50 bg-space-canvas border border-space-fg text-space-fg px-4 py-2 rounded text-[11px] font-bold uppercase tracking-[0.10em] outline-none"
      >
        SKIP TO CONTENT
      </a>

      {/* Transparent Fixed Header */}
      <header
        role="banner"
        className="fixed top-0 left-0 right-0 z-40 w-full bg-transparent transition-colors select-none pointer-events-none"
        style={{ fontFamily: "var(--font-d-din, var(--font-barlow, sans-serif))" }}
      >
        <div className="w-full px-[clamp(16px,2vw,40px)] h-20 flex items-center justify-between pointer-events-auto">
          {/* Left: Wordmark */}
          <Link
            href="/"
            className="text-space-fg text-[13px] sm:text-[14px] font-bold tracking-[0.10em] uppercase transition-colors hover:opacity-75"
            style={{ fontFamily: "var(--font-d-din-bold, var(--font-barlow, sans-serif))" }}
          >
            ASTRA-GUARD
          </Link>

          {/* Desktop Nav Links */}
          <nav
            className="hidden lg:flex items-center gap-7"
            aria-label="Primary Navigation"
          >
            {NAV_LINKS.map((link) => (
              <Link
                key={link.label}
                href={link.href}
                className="text-space-fg text-[11px] font-bold tracking-[0.10em] uppercase transition-colors hover:opacity-75 focus-visible:outline focus-visible:outline-1 focus-visible:outline-space-fg focus-visible:outline-offset-[3px]"
              >
                {link.label}
              </Link>
            ))}
          </nav>

          {/* Right: Scenario Selector + Launch Dashboard CTA */}
          <div className="hidden sm:flex items-center gap-3">
            <ScenarioSelector />
            <Button variant="ghost" href="/dashboard">
              LAUNCH DASHBOARD
            </Button>
          </div>

          {/* Mobile Menu Button */}
          <div className="flex sm:hidden items-center gap-2">
            <button
              type="button"
              onClick={() => setMobileMenuOpen(true)}
              aria-label="Open Navigation Menu"
              aria-expanded={mobileMenuOpen}
              className="border border-space-fg bg-transparent text-space-fg rounded px-3 py-1.5 text-[11px] font-bold uppercase tracking-[0.10em] hover:bg-space-fg/10"
            >
              MENU
            </button>
          </div>
        </div>
      </header>

      {/* Mobile Menu Overlay */}
      <MobileMenu
        isOpen={mobileMenuOpen}
        onClose={() => setMobileMenuOpen(false)}
        links={NAV_LINKS}
      />
    </>
  );
}
