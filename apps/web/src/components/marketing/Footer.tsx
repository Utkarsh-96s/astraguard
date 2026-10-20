import React from "react";
import Link from "next/link";

const IMAGE_CREDITS = [
  { img: "hero-earth.webp", text: "Earth limb against space void — NASA Earth Observatory / Visible Earth" },
  { img: "problem-orbit.webp", text: "Intersecting orbital planes — ESA / Science Office" },
  { img: "health-satellite.webp", text: "Earth observation satellite — Copernicus Sentinel / ESA" },
  { img: "debris-orbit.webp", text: "Debris tracking density — NASA ODPO / ESA Space Debris Office" },
  { img: "earth-disaster.webp", text: "Satellite multispectral disaster mapping — Landsat / Copernicus" },
  { img: "engine-space.webp", text: "Spacecraft vacuum propulsion — NASA Marshall / Artemis" },
  { img: "demo-space.webp", text: "Constellation over night Earth — NASA Johnson Space Center" },
];

export function Footer() {
  return (
    <footer
      id="team"
      role="contentinfo"
      className="w-full bg-[#000000] border-t border-[#404040] py-16 px-6 sm:px-10 lg:px-16 select-none"
      style={{ fontFamily: "var(--font-d-din, var(--font-barlow, sans-serif))" }}
    >
      <div className="max-w-7xl mx-auto flex flex-col gap-10">
        {/* Top: Team / Track / Links */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="flex flex-col gap-1.5">
            <span className="text-[#f0f0fa] text-[12px] font-bold uppercase tracking-[0.10em]">
              TEAM OMEN / AITHON 2.0 / TRACK 11 AEROSPACE, TELEMETRY AND SPACETECH
            </span>
            <span className="text-[#545457] text-[11px] font-normal uppercase tracking-[0.09em]">
              ADVISORY SYSTEM. DEMO MODE USES SIMULATED DATA.
            </span>
          </div>

          <div className="flex items-center gap-6 text-[11px] font-bold uppercase tracking-[0.10em]">
            <Link
              href="/dashboard"
              className="text-[#f0f0fa] hover:text-[#545457] transition-colors"
            >
              DASHBOARD
            </Link>
            <Link
              href="/demo"
              className="text-[#f0f0fa] hover:text-[#545457] transition-colors"
            >
              DEMO REPLAY
            </Link>
            <a
              href="https://github.com"
              target="_blank"
              rel="noopener noreferrer"
              className="text-[#f0f0fa] hover:text-[#545457] transition-colors"
            >
              GITHUB
            </a>
            <a
              href="/docs"
              target="_blank"
              rel="noopener noreferrer"
              className="text-[#f0f0fa] hover:text-[#545457] transition-colors"
            >
              DOCS
            </a>
          </div>
        </div>

        {/* Middle: Data Sources & Attribution */}
        <div className="border-t border-[#404040] pt-8 flex flex-col gap-3">
          <span className="text-[#545457] text-[11px] font-bold uppercase tracking-[0.10em]">
            DATA SOURCES & TELEMETRY PROTOCOLS
          </span>
          <p className="text-[#545457] text-[11px] tracking-[0.08em] uppercase leading-relaxed m-0">
            ORBITAL PROPAGATION & CONJUNCTION DATA: CELESTRAK · ESA KELVINS SPACE DEBRIS REPOSITORY. SPACECRAFT TELEMETRY: ESA-ADB ANOMALY DATA BENCHMARK STRUCTURE. EARTH OBSERVATION: COPERNICUS SENTINEL-1/2 OPEN ACCESS HUB · NASA EARTHDATA.
          </p>
        </div>

        {/* Bottom: Image Credits from CREDITS.md */}
        <div className="border-t border-[#404040] pt-6 flex flex-col gap-2">
          <span className="text-[#545457] text-[10px] font-bold uppercase tracking-[0.10em]">
            IMAGE ASSET ATTRIBUTION (PUBLIC DOMAIN & OPEN LICENCE VIA CREDITS.MD)
          </span>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2 text-[10px] text-[#545457] tracking-[0.08em] uppercase">
            {IMAGE_CREDITS.map((credit, i) => (
              <div key={i} className="truncate">
                <span className="text-[#f0f0fa]">{credit.img}: </span>
                <span>{credit.text}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Copyright notice */}
        <div className="border-t border-[#404040] pt-6 flex items-center justify-between text-[10px] text-[#545457] uppercase tracking-[0.10em]">
          <span>© 2026 ASTRA-GUARD MISSION SAFETY</span>
          <span>STRICTLY MONOCHROME AEROSPACE SPEC</span>
        </div>
      </div>
    </footer>
  );
}
