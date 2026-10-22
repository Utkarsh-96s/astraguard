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
      className="w-full bg-space-canvas py-16 select-none transition-colors duration-300"
      style={{ fontFamily: "var(--font-d-din, var(--font-barlow, sans-serif))" }}
    >
      <div className="w-full px-[clamp(16px,2vw,40px)] flex flex-col gap-10">
        {/* Top: Team / Track / Links */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="flex flex-col gap-1.5">
            <span className="text-space-fg text-[12px] font-bold uppercase tracking-[0.10em]">
              TEAM OMEN / AITHON 2.0 / TRACK 11 AEROSPACE, TELEMETRY AND SPACETECH
            </span>
            <span className="text-space-secondary text-[11px] font-medium uppercase tracking-[0.09em]">
              ADVISORY SYSTEM. DEMO MODE USES SIMULATED DATA.
            </span>
          </div>

          <div className="flex items-center gap-6 text-[11px] font-bold uppercase tracking-[0.10em]">
            <Link
              href="/dashboard"
              className="text-space-fg hover:opacity-75 transition-opacity"
            >
              DASHBOARD
            </Link>
            <Link
              href="/demo"
              className="text-space-fg hover:opacity-75 transition-opacity"
            >
              DEMO REPLAY
            </Link>
            <a
              href="https://github.com"
              target="_blank"
              rel="noopener noreferrer"
              className="text-space-fg hover:opacity-75 transition-opacity"
            >
              GITHUB
            </a>
            <a
              href="/docs"
              target="_blank"
              rel="noopener noreferrer"
              className="text-space-fg hover:opacity-75 transition-opacity"
            >
              DOCS
            </a>
          </div>
        </div>

        {/* Middle: Data Sources & Attribution */}
        <div className="pt-8 flex flex-col gap-3">
          <span className="text-space-fg text-[11px] font-bold uppercase tracking-[0.10em]">
            DATA SOURCES & TELEMETRY PROTOCOLS
          </span>
          <p className="text-space-secondary text-[11.5px] tracking-[0.08em] uppercase leading-relaxed m-0 font-medium">
            ORBITAL PROPAGATION & CONJUNCTION DATA: CELESTRAK · ESA KELVINS SPACE DEBRIS REPOSITORY. SPACECRAFT TELEMETRY: ESA-ADB ANOMALY DATA BENCHMARK STRUCTURE. EARTH OBSERVATION: COPERNICUS SENTINEL-1/2 OPEN ACCESS HUB · NASA EARTHDATA.
          </p>
        </div>

        {/* Bottom: Image Credits from CREDITS.md */}
        <div className="pt-6 flex flex-col gap-2">
          <span className="text-space-fg text-[10px] font-bold uppercase tracking-[0.10em]">
            IMAGE ASSET ATTRIBUTION (PUBLIC DOMAIN & OPEN LICENCE VIA CREDITS.MD)
          </span>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2 text-[10px] text-space-secondary tracking-[0.08em] uppercase font-medium">
            {IMAGE_CREDITS.map((credit, i) => (
              <div key={i} className="truncate">
                <span className="text-space-fg font-bold">{credit.img}: </span>
                <span>{credit.text}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Copyright notice */}
        <div className="pt-6 flex items-center justify-between text-[10px] text-space-secondary uppercase tracking-[0.10em] font-medium">
          <span>© 2026 ASTRA-GUARD MISSION SAFETY</span>
          <span>AEROSPACE HYPERSCALE SPEC</span>
        </div>
      </div>
    </footer>
  );
}
