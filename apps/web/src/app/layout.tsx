import type { Metadata } from "next";
import { Inter, Playfair_Display, Barlow } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

const playfair = Playfair_Display({
  subsets: ["latin"],
  variable: "--font-playfair",
  style: ["normal", "italic"],
  display: "swap",
});

const barlow = Barlow({
  subsets: ["latin"],
  weight: ["400", "700"],
  variable: "--font-barlow",
  display: "swap",
});

export const metadata: Metadata = {
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL || "https://astra-guard-mission.vercel.app"),
  title: "ASTRA-GUARD | AI-Powered Integrated Space Mission Safety and Intelligence",
  description:
    "Integrated Space Mission Safety & Intelligence Platform fusing Spacecraft Health, Debris Collision Risk, and Disaster Intelligence (Team OMEN · AITHON 2.0)",
  openGraph: {
    title: "ASTRA-GUARD | AI-Powered Integrated Space Mission Safety and Intelligence",
    description:
      "Integrated Space Mission Safety & Intelligence Platform fusing Spacecraft Health, Debris Collision Risk, and Disaster Intelligence",
    images: ["/images/home/hero-earth.webp"],
  },
  twitter: {
    card: "summary_large_image",
    title: "ASTRA-GUARD | AI-Powered Integrated Space Mission Safety and Intelligence",
    description:
      "Integrated Space Mission Safety & Intelligence Platform fusing Spacecraft Health, Debris Collision Risk, and Disaster Intelligence",
    images: ["/images/home/hero-earth.webp"],
  },
};

import { ThemeProvider } from "../lib/themeContext";

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark scroll-smooth" suppressHydrationWarning>
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: `
              (function() {
                try {
                  var saved = localStorage.getItem('astraguard_theme');
                  var prefersLight = window.matchMedia('(prefers-color-scheme: light)').matches;
                  var theme = saved === 'day' || saved === 'night' ? saved : (prefersLight ? 'day' : 'night');
                  if (theme === 'day') {
                    document.documentElement.classList.remove('dark');
                    document.documentElement.classList.add('light');
                    document.documentElement.setAttribute('data-theme', 'light');
                    document.documentElement.style.colorScheme = 'light';
                  } else {
                    document.documentElement.classList.remove('light');
                    document.documentElement.classList.add('dark');
                    document.documentElement.setAttribute('data-theme', 'dark');
                    document.documentElement.style.colorScheme = 'dark';
                  }
                } catch (e) {}
              })();
            `,
          }}
        />
      </head>
      <body
        className={`${inter.variable} ${playfair.variable} ${barlow.variable} bg-space-canvas text-space-fg antialiased min-h-screen min-h-[100dvh] w-full flex flex-col font-sans selection:bg-space-secondary/20 selection:text-space-fg transition-colors duration-300`}
      >
        <ThemeProvider>{children}</ThemeProvider>
      </body>
    </html>
  );
}

