import React from "react";
import Link from "next/link";

export type ButtonVariant = "ghost" | "secondary" | "pill";

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  href?: string;
  external?: boolean;
}

export function Button({
  variant = "ghost",
  href,
  external,
  children,
  className = "",
  disabled,
  type = "button",
  ...props
}: ButtonProps) {
  const baseClasses =
    "inline-flex items-center justify-center font-bold uppercase transition-colors duration-200 select-none cursor-pointer tracking-[0.10em] text-[11px] sm:text-[12px] leading-none focus-visible:outline focus-visible:outline-1 focus-visible:outline-[#f0f0fa] focus-visible:outline-offset-[3px] disabled:opacity-40 disabled:cursor-not-allowed";

  let variantClasses = "";
  if (variant === "ghost") {
    variantClasses =
      "border border-[#f0f0fa] bg-transparent text-[#f0f0fa] rounded px-6 py-3.5 hover:bg-[rgba(240,240,250,0.08)]";
  } else if (variant === "secondary") {
    variantClasses =
      "border border-[#545457] bg-transparent text-[#545457] rounded px-6 py-3.5 hover:border-[#f0f0fa] hover:text-[#f0f0fa] hover:bg-[rgba(240,240,250,0.04)]";
  } else if (variant === "pill") {
    variantClasses =
      "border border-[#f0f0fa] bg-transparent text-[#f0f0fa] rounded-full px-4 py-2 text-[10px] sm:text-[11px] hover:bg-[rgba(240,240,250,0.08)]";
  }

  const combinedClasses = `${baseClasses} ${variantClasses} ${className}`.trim();

  if (href) {
    if (external) {
      return (
        <a
          href={href}
          target="_blank"
          rel="noopener noreferrer"
          className={combinedClasses}
          {...(props as React.AnchorHTMLAttributes<HTMLAnchorElement>)}
        >
          {children}
        </a>
      );
    }
    return (
      <Link href={href} className={combinedClasses} {...(props as React.AnchorHTMLAttributes<HTMLAnchorElement>)}>
        {children}
      </Link>
    );
  }

  return (
    <button type={type} disabled={disabled} className={combinedClasses} {...props}>
      {children}
    </button>
  );
}
