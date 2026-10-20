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
      className={`min-h-screen relative w-full overflow-hidden flex items-center bg-[#000000] ${className}`.trim()}
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
          {/* Uniform subtle dim overlay (max rgba(0,0,0,0.40)) */}
          <div
            className="absolute inset-0"
            style={{ backgroundColor: "rgba(0, 0, 0, 0.40)" }}
            aria-hidden="true"
          />
        </div>
      ) : (
        <DotFieldFallback />
      )}

      {/* Content Layer (Left-aligned in left third, 30-35% width, max 500px, 18px element gap) */}
      <div
        className={`w-full max-w-7xl mx-auto px-6 sm:px-10 lg:px-16 py-24 sm:py-32 z-10 flex min-h-screen ${
          contentVerticalAlign === "top"
            ? "items-center sm:items-start sm:pt-36 lg:pt-40"
            : "items-center"
        }`}
      >
        <div
          className={`w-full max-w-[500px] flex flex-col gap-[18px] transition-opacity duration-300 ${
            align === "center" ? "mx-auto text-center items-center" : "self-end sm:self-auto pb-12 sm:pb-0"
          }`}
        >
          {children}
        </div>
      </div>
    </section>
  );
}
