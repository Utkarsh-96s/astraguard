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

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark scroll-smooth">
      <body
        className={`${inter.variable} ${playfair.variable} ${barlow.variable} bg-black text-[#f0f0fa] antialiased min-h-screen flex flex-col font-sans selection:bg-[#404040] selection:text-[#f0f0fa]`}
      >
        {children}
      </body>
    </html>
  );
}

