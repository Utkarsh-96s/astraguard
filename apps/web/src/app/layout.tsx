import type { Metadata } from "next";
import { Inter, Playfair_Display } from "next/font/google";
import "./globals.css";
import { AppProviders } from "../components/AppProviders";
import { Footer } from "../components/Footer";

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

export const metadata: Metadata = {
  title: "ASTRA-GUARD | AI Space Mission Safety & Intelligence",
  description:
    "Integrated Space Mission Safety & Intelligence Platform fusing Spacecraft Health, Debris Collision Risk, and Disaster Intelligence (Team OMEN · AITHON 2.0)",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body
        className={`${inter.variable} ${playfair.variable} bg-void text-bone antialiased min-h-screen flex flex-col font-sans selection:bg-arterial selection:text-white`}
      >
        <AppProviders>{children}</AppProviders>
        <Footer />
      </body>
    </html>
  );
}
