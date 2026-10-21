import React from "react";

export interface BodyParagraphProps {
  children: React.ReactNode;
  className?: string;
}

export function BodyParagraph({ children, className = "" }: BodyParagraphProps) {
  return (
    <p
      style={{ fontFamily: "var(--font-d-din, var(--font-barlow, sans-serif))" }}
      className={`text-space-secondary text-[13.5px] sm:text-[14px] font-normal tracking-[0.08em] sm:tracking-[0.09em] leading-[1.75] max-w-[480px] m-0 transition-colors duration-200 ${className}`.trim()}
    >
      {children}
    </p>
  );
}
