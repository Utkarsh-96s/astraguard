import React from "react";

export interface SectionHeadlineProps {
  as?: "h1" | "h2" | "h3" | "span";
  children: React.ReactNode;
  className?: string;
  id?: string;
}

export function SectionHeadline({
  as: Component = "h2",
  children,
  className = "",
  id,
}: SectionHeadlineProps) {
  return (
    <Component
      id={id}
      style={{ fontFamily: "var(--font-d-din-bold, var(--font-barlow, sans-serif))" }}
      className={`text-space-fg uppercase font-bold tracking-[0.02em] text-[28px] sm:text-[36px] md:text-[48px] leading-[1.08] md:leading-[1.15] m-0 transition-colors duration-200 ${className}`.trim()}
    >
      {children}
    </Component>
  );
}
