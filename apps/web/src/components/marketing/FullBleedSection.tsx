"use client";

import React, { useState } from "react";
import Image from "next/image";
import { DotFieldFallback } from "./DotFieldFallback";

export interface FullBleedSectionProps {
  id: string;
  imageSrc?: string;
  imageAlt?: string;
  priority?: boolean;
  children: React.ReactNode;
  align?: "left" | "center";
  contentVerticalAlign?: "center" | "top";
  className?: string;
  isBlackOnly?: boolean;
}

export function FullBleedSection({
  id,
  imageSrc,
  imageAlt = "ASTRA-GUARD mission background",
  priority = false,
  children,
  align = "left",
  contentVerticalAlign = "center",
  className = "",
  isBlackOnly = false,
}: FullBleedSectionProps) {
  const [hasImageError, setHasImageError] = useState(false);

  const shouldRenderImage = !isBlackOnly && Boolean(imageSrc) && !hasImageError;

  return (
    <section
      id={id}
      className={`min-h-screen relative w-full overflow-hidden flex items-center bg-space-canvas transition-colors duration-300 ${className}`.trim()}
    >
      {/* Background Layer */}
      {shouldRenderImage ? (
        <div className="absolute inset-0 w-full h-full pointer-events-none select-none mask-edge-fade">
          <Image
            src={imageSrc!}
            alt={imageAlt}
            fill
            priority={priority}
            sizes="100vw"
            quality={85}
            onError={() => setHasImageError(true)}
            className="object-cover object-center"
          />
          {/* Uniform dim overlay: rgba(0,0,0, 0.50) */}
          <div
            className="absolute inset-0 transition-colors duration-300 pointer-events-none"
            style={{ backgroundColor: "rgba(0, 0, 0, 0.50)" }}
            aria-hidden="true"
          />
          {/* Pure black horizontal legibility scrim behind text */}
          {align === "left" && (
            <div
              className="absolute inset-0 pointer-events-none"
              style={{
                background: "linear-gradient(to right, rgba(0, 0, 0, 0.70) 0%, rgba(0, 0, 0, 0.40) 35%, transparent 60%)",
              }}
              aria-hidden="true"
            />
          )}
        </div>
      ) : (
        <DotFieldFallback />
      )}

      {/* Content Layer (Left-aligned in left third, 30-35% width, max 500px, 18px element gap) */}
      <div
        className={`w-full px-[clamp(16px,2vw,40px)] py-24 sm:py-32 z-10 flex min-h-[100dvh] ${
          contentVerticalAlign === "top"
            ? "items-center sm:items-start sm:pt-36 lg:pt-40"
            : "items-center"
        }`}
      >
        <div
          className={`w-full max-w-[520px] flex flex-col gap-[18px] transition-all duration-300 ${
            align === "center" ? "mx-auto text-center items-center" : "self-end sm:self-auto pb-12 sm:pb-0"
          }`}
        >
          {children}
        </div>
      </div>
    </section>
  );
}
