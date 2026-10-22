"use client";

import React, { useEffect, useRef } from "react";
import { usePathname } from "next/navigation";
import Lenis from "lenis";

export function SmoothScrollProvider({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const lenisRef = useRef<Lenis | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    // Respect prefers-reduced-motion
    if (typeof window === "undefined") return;
    const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (prefersReducedMotion) {
      return;
    }

    // Initialize Lenis with subtle aerospace inertia
    const lenis = new Lenis({
      lerp: 0.1,
      duration: 1.2,
      smoothWheel: true,
      syncTouch: false, // never hijack native mobile touch scrolling
      touchMultiplier: 1.0,
      autoRaf: true,
    });

    lenisRef.current = lenis;
    (window as any).lenis = lenis;

    // In-page smooth anchor navigation with exact 64px offset
    const handleAnchorClick = (e: MouseEvent) => {
      const target = e.target as HTMLElement | null;
      const anchor = target?.closest('a[href*="#"]') as HTMLAnchorElement | null;
      if (!anchor) return;

      const rawHref = anchor.getAttribute("href");
      if (!rawHref) return;

      let hash = "";
      if (rawHref.startsWith("#")) {
        hash = rawHref;
      } else if (rawHref.startsWith("/#") && (window.location.pathname === "/" || window.location.pathname === "")) {
        hash = rawHref.substring(1);
      } else {
        return;
      }

      if (!hash || hash === "#") return;

      const targetEl = document.querySelector(hash) as HTMLElement | null;
      if (targetEl) {
        e.preventDefault();
        lenis.scrollTo(targetEl, {
          offset: 0,
          duration: 1.2,
          easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
        });
      }
    };

    document.addEventListener("click", handleAnchorClick, { capture: true });

    return () => {
      document.removeEventListener("click", handleAnchorClick, { capture: true });
      lenis.destroy();
      lenisRef.current = null;
    };
  }, []);

  // Route change: smooth scroll-to-top with subtle opacity cross-fade (150-200ms)
  useEffect(() => {
    if (lenisRef.current) {
      lenisRef.current.scrollTo(0, { immediate: true });
    } else if (typeof window !== "undefined") {
      window.scrollTo(0, 0);
    }

    if (containerRef.current) {
      containerRef.current.style.opacity = "0.75";
      containerRef.current.style.transition = "opacity 180ms ease-in-out";
      const raf = requestAnimationFrame(() => {
        if (containerRef.current) {
          containerRef.current.style.opacity = "1";
        }
      });
      return () => cancelAnimationFrame(raf);
    }
  }, [pathname]);

  return (
    <div ref={containerRef} className="w-full flex-1 flex flex-col transition-opacity duration-200">
      {children}
    </div>
  );
}
