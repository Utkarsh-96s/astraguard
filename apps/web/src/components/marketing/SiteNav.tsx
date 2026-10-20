"use client";

import React, { useState } from "react";
import Link from "next/link";
import { Button } from "./Button";
import { ScenarioSelector } from "./ScenarioSelector";
import { MobileMenu } from "./MobileMenu";

const NAV_LINKS = [
  { label: "MISSION", href: "#mission" },
  { label: "HEALTH", href: "#health" },
  { label: "DEBRIS", href: "#debris" },
  { label: "EARTH", href: "#earth" },
  { label: "ENGINE", href: "#engine" },
  { label: "DEMO", href: "#demo" },
  { label: "TEAM", href: "#team" },
];

export function SiteNav() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <>
      {/* Skip to Content for a11y */}
      <a
        href="#mission"
        className="sr-only focus:not-sr-only focus:fixed focus:top-4 focus:left-4 z-50 bg-[#000000] border border-[#f0f0fa] text-[#f0f0fa] px-4 py-2 rounded text-[11px] font-bold uppercase tracking-[0.10em] outline-none"
      >
        SKIP TO CONTENT
      </a>

      {/* Transparent Fixed Header */}
      <header
        role="banner"
        className="fixed top-0 left-0 right-0 z-40 w-full bg-transparent border-b border-transparent transition-none select-none pointer-events-none"
        style={{ fontFamily: "var(--font-d-din, var(--font-barlow, sans-serif))" }}
      >
        <div className="max-w-7xl mx-auto px-6 sm:px-10 lg:px-16 h-20 flex items-center justify-between pointer-events-auto">
          {/* Left: Wordmark */}
          <Link
            href="/"
            className="text-[#f0f0fa] text-[13px] sm:text-[14px] font-bold tracking-[0.10em] uppercase transition-colors hover:text-[#545457]"
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
              <a
                key={link.label}
                href={link.href}
                className="text-[#f0f0fa] text-[11px] font-bold tracking-[0.10em] uppercase transition-colors hover:text-[#545457] focus-visible:outline focus-visible:outline-1 focus-visible:outline-[#f0f0fa] focus-visible:outline-offset-[3px]"
              >
                {link.label}
              </a>
            ))}
          </nav>

          {/* Right: Scenario Selector + Launch Dashboard CTA */}
          <div className="hidden sm:flex items-center gap-4">
            <ScenarioSelector />
            <Button variant="ghost" href="/dashboard">
              LAUNCH DASHBOARD
            </Button>
          </div>

          {/* Mobile Menu Button */}
          <div className="flex sm:hidden items-center gap-3">
            <button
              type="button"
              onClick={() => setMobileMenuOpen(true)}
              aria-label="Open Navigation Menu"
              aria-expanded={mobileMenuOpen}
              className="border border-[#f0f0fa] bg-transparent text-[#f0f0fa] rounded px-3 py-1.5 text-[11px] font-bold uppercase tracking-[0.10em] hover:bg-[rgba(240,240,250,0.08)]"
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
