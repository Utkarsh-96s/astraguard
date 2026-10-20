import React from "react";

export interface BodyParagraphProps {
  children: React.ReactNode;
  className?: string;
}

export function BodyParagraph({ children, className = "" }: BodyParagraphProps) {
  return (
    <p
      style={{ fontFamily: "var(--font-d-din, var(--font-barlow, sans-serif))" }}
      className={`text-[#545457] text-[13px] font-normal tracking-[0.10em] leading-[1.7] max-w-[480px] m-0 ${className}`.trim()}
    >
      {children}
    </p>
  );
}
