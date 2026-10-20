"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import {
  Globe,
  Compass,
  Play,
  Pause,
  RotateCcw,
  Maximize2,
  Minimize2,
  Navigation,
  Eye,
  Radio,
  Layers,
} from "lucide-react";
import { OrbitTracksResponse, OrbitPoint } from "../lib/types";
import { fetchOrbitTracks } from "../lib/api";
import { SimulatedBadge } from "./SimulatedBadge";
import { playAudioCue } from "../lib/audio";

interface OrbitTwin3DProps {
  assetId?: string;
  selectedConjunctionName?: string;
  onSelectWaypoint?: (wp: OrbitPoint) => void;
}

export function OrbitTwin3D({
  assetId = "SENTINEL-2A",
  selectedConjunctionName = "FENGYUN-1C-DEB-29834",
  onSelectWaypoint,
}: OrbitTwin3DProps) {
  const [tracks, setTracks] = useState<OrbitTracksResponse | null>(null);
  const [pitch, setPitch] = useState<number>(25.0); // deg
  const [yaw, setYaw] = useState<number>(-45.0); // deg
  const [zoom, setZoom] = useState<number>(1.0);
  const [autoRotate, setAutoRotate] = useState<boolean>(true);
  const [timeStepIndex, setTimeStepIndex] = useState<number>(12); // current position along orbit
  const [dragging, setDragging] = useState<boolean>(false);
  const [dragStart, setDragStart] = useState<{ x: number; y: number }>({ x: 0, y: 0 });

  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  // Fetch orbit tracks
  useEffect(() => {
    let mounted = true;
    fetchOrbitTracks(assetId).then((data) => {
      if (mounted) setTracks(data);
    });
    return () => {
      mounted = false;
    };
  }, [assetId]);

  // Auto-rotation timer
  useEffect(() => {
    if (!autoRotate || dragging) return;
    const interval = setInterval(() => {
      setYaw((prev) => (prev + 0.35) % 360);
      setTimeStepIndex((prev) => (prev + 1) % 48);
    }, 60);
    return () => clearInterval(interval);
  }, [autoRotate, dragging]);

  // 3D Orthographic Projection Math
  // Projects a 3D point (x, y, z) in Earth-Centered Inertial (ECI) km onto a 2D screen (sx, sy)
  const project3D = useCallback(
    (
      x: number,
      y: number,
      z: number,
      width: number,
      height: number,
      currentYaw: number,
      currentPitch: number,
      scaleMultiplier: number
    ) => {
      const yawRad = (currentYaw * Math.PI) / 180;
      const pitchRad = (currentPitch * Math.PI) / 180;

      // Rotate around Z axis (yaw)
      const x1 = x * Math.cos(yawRad) - y * Math.sin(yawRad);
      const y1 = x * Math.sin(yawRad) + y * Math.cos(yawRad);
      const z1 = z;

      // Rotate around X axis (pitch)
      const x2 = x1;
      const y2 = y1 * Math.cos(pitchRad) - z1 * Math.sin(pitchRad);
      const z2 = y1 * Math.sin(pitchRad) + z1 * Math.cos(pitchRad);

      // Earth radius ~6378 km, normalize to screen scale
      const earthRadiusKm = 6378.0;
      const screenRadius = (Math.min(width, height) / 2) * 0.48 * scaleMultiplier;
      const scale = screenRadius / earthRadiusKm;

      const sx = width / 2 + x2 * scale;
      const sy = height / 2 - z2 * scale; // inverted Y for screen space

      return { sx, sy, depth: y2, scale };
    },
    []
  );

  // Canvas Rendering Loop
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const width = canvas.width;
    const height = canvas.height;

    // Clear background
    ctx.fillStyle = "#0c0a0c";
    ctx.fillRect(0, 0, width, height);

    // Starfield points
    ctx.fillStyle = "rgba(255, 255, 255, 0.4)";
    for (let i = 0; i < 40; i++) {
      const sx = (Math.sin(i * 123.4) * 0.5 + 0.5) * width;
      const sy = (Math.cos(i * 567.8) * 0.5 + 0.5) * height;
      ctx.fillRect(sx, sy, 1.2, 1.2);
    }

    const earthRadiusKm = 6378.0;
    const screenRadius = (Math.min(width, height) / 2) * 0.48 * zoom;

    // Atmosphere Outer Glow
    const glowGrad = ctx.createRadialGradient(
      width / 2,
      height / 2,
      screenRadius * 0.9,
      width / 2,
      height / 2,
      screenRadius * 1.2
    );
    glowGrad.addColorStop(0, "rgba(56, 189, 248, 0.25)");
    glowGrad.addColorStop(0.5, "rgba(56, 189, 248, 0.08)");
    glowGrad.addColorStop(1, "rgba(56, 189, 248, 0)");
    ctx.fillStyle = glowGrad;
    ctx.beginPath();
    ctx.arc(width / 2, height / 2, screenRadius * 1.2, 0, Math.PI * 2);
    ctx.fill();

    // Earth Sphere Surface
    const earthGrad = ctx.createRadialGradient(
      width / 2 - screenRadius * 0.3,
      height / 2 - screenRadius * 0.3,
      screenRadius * 0.1,
      width / 2,
      height / 2,
      screenRadius
    );
    earthGrad.addColorStop(0, "#162030");
    earthGrad.addColorStop(0.7, "#0f1622");
    earthGrad.addColorStop(1, "#070b12");

    ctx.fillStyle = earthGrad;
    ctx.beginPath();
    ctx.arc(width / 2, height / 2, screenRadius, 0, Math.PI * 2);
    ctx.fill();
    ctx.strokeStyle = "rgba(56, 189, 248, 0.4)";
    ctx.lineWidth = 1.5;
    ctx.stroke();

    // 3D Latitude Parallels
    [-60, -30, 0, 30, 60].forEach((lat) => {
      ctx.beginPath();
      ctx.strokeStyle = lat === 0 ? "rgba(56, 189, 248, 0.35)" : "rgba(255, 255, 255, 0.08)";
      ctx.lineWidth = lat === 0 ? 1.2 : 0.8;
      const latRad = (lat * Math.PI) / 180;
      const rLat = earthRadiusKm * Math.cos(latRad);
      const zLat = earthRadiusKm * Math.sin(latRad);

      let first = true;
      for (let lon = 0; lon <= 360; lon += 10) {
        const lonRad = (lon * Math.PI) / 180;
        const x = rLat * Math.cos(lonRad);
        const y = rLat * Math.sin(lonRad);
        const p = project3D(x, y, zLat, width, height, yaw, pitch, zoom);
        // Only draw visible hemisphere
        if (p.depth > -earthRadiusKm * 0.1) {
          if (first) {
            ctx.moveTo(p.sx, p.sy);
            first = false;
          } else {
            ctx.lineTo(p.sx, p.sy);
          }
        } else {
          first = true;
        }
      }
      ctx.stroke();
    });

    // 3D Longitude Meridians
    [0, 45, 90, 135, 180, 225, 270, 315].forEach((lon) => {
      ctx.beginPath();
      ctx.strokeStyle = "rgba(255, 255, 255, 0.08)";
      ctx.lineWidth = 0.8;
      const lonRad = (lon * Math.PI) / 180;
      let first = true;
      for (let lat = -90; lat <= 90; lat += 10) {
        const latRad = (lat * Math.PI) / 180;
        const rLat = earthRadiusKm * Math.cos(latRad);
        const zLat = earthRadiusKm * Math.sin(latRad);
        const x = rLat * Math.cos(lonRad);
        const y = rLat * Math.sin(lonRad);
        const p = project3D(x, y, zLat, width, height, yaw, pitch, zoom);
        if (p.depth > -earthRadiusKm * 0.1) {
          if (first) {
            ctx.moveTo(p.sx, p.sy);
            first = false;
          } else {
            ctx.lineTo(p.sx, p.sy);
          }
        } else {
          first = true;
        }
      }
      ctx.stroke();
    });

    // Secondary Debris Orbit Track (Red)
    if (tracks?.debris_track && tracks.debris_track.length > 0) {
      ctx.beginPath();
      ctx.strokeStyle = "rgba(254, 30, 52, 0.75)";
      ctx.lineWidth = 1.5;
      ctx.setLineDash([4, 3]);

      tracks.debris_track.forEach((pt, idx) => {
        const p = project3D(pt.x_eci_km, pt.y_eci_km, pt.z_eci_km, width, height, yaw, pitch, zoom);
        if (idx === 0) ctx.moveTo(p.sx, p.sy);
        else ctx.lineTo(p.sx, p.sy);
      });
      ctx.stroke();
      ctx.setLineDash([]);

      // Debris Live Position
      const debPt = tracks.debris_track[(timeStepIndex + 6) % tracks.debris_track.length];
      const pDeb = project3D(debPt.x_eci_km, debPt.y_eci_km, debPt.z_eci_km, width, height, yaw, pitch, zoom);
      ctx.fillStyle = "#fe1e34";
      ctx.beginPath();
      ctx.arc(pDeb.sx, pDeb.sy, 4, 0, Math.PI * 2);
      ctx.fill();
    }

    // Primary Sentinel-2A SSO Orbit Track (Electric Cyan)
    if (tracks?.primary_track && tracks.primary_track.length > 0) {
      ctx.beginPath();
      ctx.strokeStyle = "rgba(56, 189, 248, 0.9)";
      ctx.lineWidth = 2.0;
      tracks.primary_track.forEach((pt, idx) => {
        const p = project3D(pt.x_eci_km, pt.y_eci_km, pt.z_eci_km, width, height, yaw, pitch, zoom);
        if (idx === 0) ctx.moveTo(p.sx, p.sy);
        else ctx.lineTo(p.sx, p.sy);
      });
      ctx.stroke();

      // Sentinel-2A Satellite Icon / Glow
      const s2Pt = tracks.primary_track[timeStepIndex % tracks.primary_track.length];
      const pSat = project3D(s2Pt.x_eci_km, s2Pt.y_eci_km, s2Pt.z_eci_km, width, height, yaw, pitch, zoom);

      // Pulse ring
      ctx.strokeStyle = "rgba(56, 189, 248, 0.6)";
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      ctx.arc(pSat.sx, pSat.sy, 8, 0, Math.PI * 2);
      ctx.stroke();

      // Satellite core dot
      ctx.fillStyle = "#ffffff";
      ctx.beginPath();
      ctx.arc(pSat.sx, pSat.sy, 4, 0, Math.PI * 2);
      ctx.fill();

      // Label
      ctx.fillStyle = "#38bdf8";
      ctx.font = "bold 10px monospace";
      ctx.fillText("S2A (786 km)", pSat.sx + 10, pSat.sy - 6);
    }

    // Conjunction Encounter Apex Waypoint
    if (tracks?.encounter_waypoint) {
      const wp = tracks.encounter_waypoint;
      const pWp = project3D(wp.x_eci_km, wp.y_eci_km, wp.z_eci_km, width, height, yaw, pitch, zoom);

      // Warning pulsating beacon
      ctx.strokeStyle = "rgba(254, 30, 52, 0.8)";
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.arc(pWp.sx, pWp.sy, 12, 0, Math.PI * 2);
      ctx.stroke();

      ctx.fillStyle = "#fe1e34";
      ctx.beginPath();
      ctx.arc(pWp.sx, pWp.sy, 5, 0, Math.PI * 2);
      ctx.fill();

      ctx.fillStyle = "#ff6b7a";
      ctx.font = "bold 10px monospace";
      ctx.fillText("CONJUNCTION APEX", pWp.sx + 14, pWp.sy + 3);
    }
  }, [tracks, pitch, yaw, zoom, timeStepIndex, project3D]);

  // Drag Interactions for 3D Camera Rotation
  const handleMouseDown = (e: React.MouseEvent) => {
    setDragging(true);
    setDragStart({ x: e.clientX, y: e.clientY });
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!dragging) return;
    const dx = e.clientX - dragStart.x;
    const dy = e.clientY - dragStart.y;
    setYaw((prev) => (prev + dx * 0.5) % 360);
    setPitch((prev) => Math.max(-80, Math.min(80, prev - dy * 0.5)));
    setDragStart({ x: e.clientX, y: e.clientY });
  };

  const handleMouseUp = () => {
    setDragging(false);
  };

  const currentPt = tracks?.primary_track[timeStepIndex % (tracks?.primary_track.length || 1)];

  return (
    <div className="p-5 rounded-card bg-charcoal border border-white/10 space-y-4">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-white/10 pb-3">
        <div>
          <div className="flex items-center gap-2">
            <Globe className="w-5 h-5 text-sky-400" />
            <h2 className="text-base font-bold text-bone">
              3D Orbit Digital Twin (Sentinel-2A & Debris Encounter)
            </h2>
            <SimulatedBadge />
          </div>
          <p className="text-xs text-ash font-mono mt-0.5">
            SGP4 Orbit Propagation in Earth-Centered Inertial (ECI) Frame & Sun-Synchronous Phasing
          </p>
        </div>

        {/* View Controls */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => {
              playAudioCue("click");
              setAutoRotate(!autoRotate);
            }}
            className={`px-3 py-1.5 rounded text-xs font-mono flex items-center gap-1.5 transition-all ${
              autoRotate
                ? "bg-sky-500/20 text-sky-300 border border-sky-400/50"
                : "bg-smoke text-ash hover:text-bone"
            }`}
          >
            {autoRotate ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5" />}
            <span>{autoRotate ? "Pause Spin" : "Auto Spin"}</span>
          </button>

          <button
            onClick={() => {
              playAudioCue("click");
              setPitch(25.0);
              setYaw(-45.0);
              setZoom(1.0);
            }}
            className="p-1.5 rounded bg-smoke hover:bg-white/10 text-ash hover:text-bone text-xs font-mono"
            title="Reset Camera"
          >
            <RotateCcw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Main 3D Canvas Box */}
      <div
        className="relative w-full aspect-[16/9] max-h-[460px] bg-void rounded-card border border-white/10 overflow-hidden cursor-grab active:cursor-grabbing select-none"
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
      >
        <canvas
          ref={canvasRef}
          width={800}
          height={450}
          className="w-full h-full object-contain"
        />

        {/* Telemetry HUD (Top-Left) */}
        <div className="absolute top-3 left-3 p-3 rounded-card bg-charcoal/85 backdrop-blur-md border border-white/10 text-xs font-mono space-y-1 shadow-glass max-w-[260px]">
          <div className="text-[10px] uppercase font-bold text-sky-400 flex items-center gap-1.5 border-b border-white/10 pb-1">
            <Radio className="w-3 h-3 text-sky-400 animate-pulse" />
            <span>Telemetry Coordinates (ECI)</span>
          </div>
          {currentPt && (
            <div className="space-y-0.5 text-pebble text-[11px]">
              <div className="flex justify-between">
                <span>X_eci:</span>
                <span className="text-bone font-semibold">{currentPt.x_eci_km.toFixed(1)} km</span>
              </div>
              <div className="flex justify-between">
                <span>Y_eci:</span>
                <span className="text-bone font-semibold">{currentPt.y_eci_km.toFixed(1)} km</span>
              </div>
              <div className="flex justify-between">
                <span>Z_eci:</span>
                <span className="text-bone font-semibold">{currentPt.z_eci_km.toFixed(1)} km</span>
              </div>
              <div className="flex justify-between border-t border-white/5 pt-1">
                <span>Altitude:</span>
                <span className="text-emerald-400 font-semibold">{currentPt.alt_km} km</span>
              </div>
              <div className="flex justify-between">
                <span>Sub-Sat:</span>
                <span className="text-bone">
                  {currentPt.lat.toFixed(1)}°N, {currentPt.lon.toFixed(1)}°E
                </span>
              </div>
            </div>
          )}
        </div>

        {/* Encounter Beacon HUD (Top-Right) */}
        <div className="absolute top-3 right-3 p-3 rounded-card bg-charcoal/85 backdrop-blur-md border border-arterial/40 text-xs font-mono space-y-1 shadow-glass">
          <div className="text-[10px] uppercase font-bold text-arterial flex items-center gap-1.5 border-b border-white/10 pb-1">
            <Eye className="w-3 h-3 text-arterial" />
            <span>Target Conjunction</span>
          </div>
          <div className="text-[11px] text-bone font-bold">{selectedConjunctionName}</div>
          <div className="text-[10px] text-pebble flex justify-between gap-4">
            <span>Inclination: 98.6° (SSO)</span>
            <span>Period: 100.5m</span>
          </div>
        </div>

        {/* Legend (Bottom-Left) */}
        <div className="absolute bottom-3 left-3 px-3 py-1.5 rounded-nav bg-charcoal/85 backdrop-blur-md border border-white/10 text-[11px] font-mono flex items-center gap-4">
          <span className="flex items-center gap-1.5 text-sky-400">
            <span className="w-2.5 h-1 rounded bg-sky-400 inline-block" /> Sentinel-2A
          </span>
          <span className="flex items-center gap-1.5 text-arterial">
            <span className="w-2.5 h-1 rounded bg-arterial inline-block" /> Debris Track
          </span>
          <span className="flex items-center gap-1.5 text-rose-300">
            <span className="w-2 h-2 rounded-full bg-arterial animate-ping inline-block" /> Apex
          </span>
        </div>

        {/* Drag Hint (Bottom-Right) */}
        <div className="absolute bottom-3 right-3 px-2.5 py-1 rounded-nav bg-charcoal/70 text-[10px] font-mono text-pebble">
          Drag to orbit camera | Pitch: {pitch.toFixed(0)}° Yaw: {yaw.toFixed(0)}°
        </div>
      </div>

      {/* Orbit Propagation Time Scrubber */}
      <div className="p-3.5 rounded-card bg-smoke/40 border border-white/5 space-y-2">
        <div className="flex items-center justify-between text-xs font-mono">
          <span className="text-pebble flex items-center gap-1.5">
            <Navigation className="w-3.5 h-3.5 text-sky-400" />
            Orbit Propagation Epoch:
          </span>
          <span className="text-bone font-bold">
            T + {(((timeStepIndex / 48) * 100.5) % 100.5).toFixed(1)} min / 100.5 min Period
          </span>
        </div>
        <input
          type="range"
          min="0"
          max="47"
          value={timeStepIndex}
          onChange={(e) => {
            setAutoRotate(false);
            setTimeStepIndex(parseInt(e.target.value, 10));
          }}
          className="w-full accent-sky-400 cursor-pointer"
        />
      </div>
    </div>
  );
}
