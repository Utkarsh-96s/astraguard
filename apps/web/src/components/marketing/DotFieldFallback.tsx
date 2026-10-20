import React from "react";

// Deterministic sparse dot coordinates to ensure pure server/client hydration consistency
const STATIC_DOTS = [
  { x: 12, y: 18, o: 0.22, s: 1.5 },
  { x: 28, y: 34, o: 0.12, s: 1 },
  { x: 42, y: 15, o: 0.28, s: 1.5 },
  { x: 58, y: 22, o: 0.15, s: 1 },
  { x: 74, y: 19, o: 0.32, s: 2 },
  { x: 88, y: 31, o: 0.18, s: 1 },
  { x: 15, y: 48, o: 0.25, s: 1 },
  { x: 35, y: 56, o: 0.14, s: 1.5 },
  { x: 62, y: 45, o: 0.22, s: 1 },
  { x: 82, y: 52, o: 0.30, s: 1.5 },
  { x: 94, y: 64, o: 0.16, s: 1 },
  { x: 22, y: 72, o: 0.20, s: 1.5 },
  { x: 48, y: 81, o: 0.26, s: 1 },
  { x: 68, y: 75, o: 0.18, s: 1.5 },
  { x: 85, y: 88, o: 0.24, s: 1 },
  { x: 7, y: 89, o: 0.15, s: 1 },
  { x: 53, y: 61, o: 0.28, s: 2 },
  { x: 38, y: 29, o: 0.14, s: 1 },
  { x: 91, y: 12, o: 0.20, s: 1.5 },
  { x: 6, y: 38, o: 0.25, s: 1 },
];

export function DotFieldFallback() {
  return (
    <div
      className="absolute inset-0 w-full h-full bg-[#000000] overflow-hidden pointer-events-none select-none"
      aria-hidden="true"
    >
      {STATIC_DOTS.map((dot, i) => (
        <span
          key={i}
          className="absolute bg-[#f0f0fa] rounded-full"
          style={{
            left: `${dot.x}%`,
            top: `${dot.y}%`,
            width: `${dot.s}px`,
            height: `${dot.s}px`,
            opacity: dot.o,
          }}
        />
      ))}
    </div>
  );
}
