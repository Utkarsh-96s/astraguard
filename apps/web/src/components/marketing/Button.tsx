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
    "inline-flex items-center justify-center font-bold uppercase transition-all duration-200 select-none cursor-pointer tracking-[0.10em] text-[11px] sm:text-[12px] leading-none focus-visible:outline focus-visible:outline-1 focus-visible:outline-space-fg focus-visible:outline-offset-[3px] disabled:opacity-40 disabled:cursor-not-allowed";

  let variantClasses = "";
  if (variant === "ghost") {
    variantClasses =
      "border border-space-fg bg-transparent text-space-fg rounded px-6 py-3.5 hover:bg-space-fg/10 active:bg-space-fg/15";
  } else if (variant === "secondary") {
    variantClasses =
      "border border-space-secondary/70 bg-transparent text-space-fg rounded px-6 py-3.5 hover:border-space-fg hover:text-space-fg hover:bg-space-fg/5 active:bg-space-fg/10";
  } else if (variant === "pill") {
    variantClasses =
      "border border-space-fg bg-transparent text-space-fg rounded-full px-4 py-2 text-[10px] sm:text-[11px] hover:bg-space-fg/10";
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
