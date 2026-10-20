"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Shield, Radio, Activity, Orbit, AlertTriangle, Layers, PlayCircle } from "lucide-react";

export function Navbar() {
  const pathname = usePathname();

  const navLinks = [
    { href: "/", label: "Overview", icon: Shield },
    { href: "/health", label: "Health AI", icon: Activity },
    { href: "/debris", label: "Debris Risk", icon: Orbit },
    { href: "/disaster", label: "Disaster EO", icon: Layers },
    { href: "/alerts", label: "Alerts & HITL", icon: AlertTriangle },
    { href: "/models", label: "Model Registry", icon: Radio },
    { href: "/demo", label: "Demo Player", icon: PlayCircle },
  ];

  return (
    <header className="sticky top-0 z-50 bg-void/90 backdrop-blur-md border-b border-white/10 transition-colors">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo & Platform Name */}
          <div className="flex items-center gap-3">
            <Link href="/" className="flex items-center gap-2 group">
              <div className="w-8 h-8 rounded-nav bg-charcoal border border-white/20 flex items-center justify-center group-hover:border-arterial transition-colors">
                <Shield className="w-4 h-4 text-arterial" />
              </div>
              <div>
                <span className="font-bold tracking-tight text-bone text-base sm:text-lg flex items-center gap-1.5">
                  ASTRA-GUARD
                  <span className="w-1.5 h-1.5 rounded-full bg-arterial inline-block" />
                </span>
                <span className="block text-[9px] uppercase tracking-widest text-ash font-mono -mt-0.5">
                  Space Safety Platform
                </span>
              </div>
            </Link>

            {/* Satellite Asset Tag */}
            <div className="hidden lg:flex items-center gap-2 px-2.5 py-1 rounded-nav bg-smoke/80 border border-white/10 text-[11px] font-mono">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              <span className="text-bone font-semibold">SENTINEL-2A</span>
              <span className="text-iron">|</span>
              <span className="text-ash">NORAD 40697</span>
              <span className="text-iron">|</span>
              <span className="text-ash">SSO 786 KM</span>
            </div>
          </div>

          {/* Nav Links */}
          <nav className="hidden md:flex items-center space-x-1">
            {navLinks.map((link) => {
              const Icon = link.icon;
              const isActive = pathname === link.href;
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-nav text-xs font-medium tracking-nav transition-all ${
                    isActive
                      ? "bg-smoke text-bone border border-white/20 shadow-glass"
                      : "text-ash hover:text-bone hover:bg-white/5"
                  }`}
                >
                  <Icon className={`w-3.5 h-3.5 ${isActive ? "text-arterial" : "text-pebble"}`} />
                  {link.label}
                </Link>
              );
            })}
          </nav>

          {/* Real-time Status Badge */}
          <div className="flex items-center gap-2">
            <div className="flex items-center gap-2 px-2.5 py-1 rounded-nav bg-smoke border border-emerald-500/30 text-[11px] font-mono text-emerald-400">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <span className="hidden sm:inline">STREAM:</span> LIVE
            </div>
          </div>
        </div>
      </div>

      {/* Mobile nav bar */}
      <div className="md:hidden border-t border-white/5 bg-charcoal px-3 py-2 flex overflow-x-auto space-x-2 scrollbar-none">
        {navLinks.map((link) => {
          const Icon = link.icon;
          const isActive = pathname === link.href;
          return (
            <Link
              key={link.href}
              href={link.href}
              className={`flex items-center gap-1.5 px-2.5 py-1 rounded-nav text-[11px] whitespace-nowrap ${
                isActive ? "bg-smoke text-bone border border-white/20" : "text-ash"
              }`}
            >
              <Icon className="w-3 h-3 text-arterial" />
              {link.label}
            </Link>
          );
        })}
      </div>
    </header>
  );
}
