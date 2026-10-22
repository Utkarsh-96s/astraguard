import React from "react";

export interface BodyParagraphProps {
  children: React.ReactNode;
  className?: string;
}

export function BodyParagraph({ children, className = "" }: BodyParagraphProps) {
  return (
    <p
      style={{ fontFamily: "var(--font-d-din, var(--font-barlow, sans-serif))" }}
      className={`text-[#f0f0fa] text-[14px] sm:text-[15px] font-medium tracking-[0.10em] leading-[1.7] max-w-[520px] m-0 transition-colors duration-200 ${className}`.trim()}
    >
      {children}
    </p>
  );
}
