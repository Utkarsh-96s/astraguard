import React from "react";
import type { Metadata } from "next";
import {
  SiteNav,
  FullBleedSection,
  SectionHeadline,
  BodyParagraph,
  Button,
  TelemetryStrip,
  MetricsList,
  Footer,
} from "../components/marketing";

export const metadata: Metadata = {
  title: "ASTRA-GUARD | AI-Powered Integrated Space Mission Safety and Intelligence",
  description:
    "ASTRA-GUARD fuses spacecraft health, debris collision risk and satellite disaster intelligence into one explainable Mission Risk Score. Operators see what needs attention, and why.",
  openGraph: {
    title: "ASTRA-GUARD | AI-Powered Integrated Space Mission Safety and Intelligence",
    description:
      "ASTRA-GUARD fuses spacecraft health, debris collision risk and satellite disaster intelligence into one explainable Mission Risk Score.",
    images: ["/images/home/hero-earth.webp"],
  },
  twitter: {
    card: "summary_large_image",
    title: "ASTRA-GUARD | AI-Powered Integrated Space Mission Safety and Intelligence",
    description:
      "ASTRA-GUARD fuses spacecraft health, debris collision risk and satellite disaster intelligence into one explainable Mission Risk Score.",
    images: ["/images/home/hero-earth.webp"],
  },
};

export default function MarketingHomePage() {
  return (
    <div className="w-full bg-space-canvas text-space-fg min-h-screen relative overflow-x-hidden selection:bg-space-secondary/20 selection:text-space-fg transition-colors duration-300">
      {/* 1. Top Navigation */}
      <SiteNav />

      <main id="main-content" className="w-full">
        {/* 2. HERO */}
        <FullBleedSection
          id="mission"
          imageSrc="/images/home/hero-earth.webp"
          imageAlt="Earth curvature against deep space void"
          priority
          contentVerticalAlign="center"
        >
          <SectionHeadline as="h1">
            MONITOR THE SPACECRAFT. PREDICT THE THREAT.
          </SectionHeadline>
          <BodyParagraph>
            ASTRA-GUARD fuses spacecraft health, debris collision risk and satellite disaster intelligence into one explainable Mission Risk Score. Operators see what needs attention, and why.
          </BodyParagraph>
          <div className="flex flex-wrap items-center gap-3 pt-2">
            <Button variant="ghost" href="/dashboard">
              LAUNCH DASHBOARD
            </Button>
            <Button variant="secondary" href="/demo">
              WATCH DEMO
            </Button>
          </div>
          <TelemetryStrip />
        </FullBleedSection>

        {/* 3. PROBLEM */}
        <FullBleedSection
          id="problem"
          imageSrc="/images/home/problem-orbit.webp"
          imageAlt="Orbital constellation planes around Earth"
        >
          <SectionHeadline>
            THREE DATA STREAMS. ONE DECISION.
          </SectionHeadline>
          <BodyParagraph>
            Telemetry, orbital data and satellite imagery live in separate tools. Operators correlate them by hand. ASTRA-GUARD joins them automatically and ranks what matters now.
          </BodyParagraph>
        </FullBleedSection>

        {/* 4. HEALTH */}
        <FullBleedSection
          id="health"
          imageSrc="/images/home/health-satellite.webp"
          imageAlt="Earth observation satellite in low Earth orbit"
        >
          <SectionHeadline>
            SPACECRAFT HEALTH
          </SectionHeadline>
          <BodyParagraph>
            Anomaly detection on multichannel telemetry using Isolation Forest and LSTM models. Every alert names the channels that drove it.
          </BodyParagraph>
          <div className="pt-2">
            <Button variant="ghost" href="/dashboard/health">
              EXPLORE HEALTH AI
            </Button>
          </div>
        </FullBleedSection>

        {/* 5. DEBRIS */}
        <FullBleedSection
          id="debris"
          imageSrc="/images/home/debris-orbit.webp"
          imageAlt="Space debris and orbital conjunction paths"
        >
          <SectionHeadline>
            DEBRIS COLLISION RISK
          </SectionHeadline>
          <BodyParagraph>
            SGP4 propagation, conjunction screening and collision probability, with a trend model trained on real conjunction data messages. Screening-grade from public orbit data.
          </BodyParagraph>
          <div className="pt-2">
            <Button variant="ghost" href="/dashboard/debris">
              EXPLORE DEBRIS AI
            </Button>
          </div>
        </FullBleedSection>

        {/* 6. EARTH */}
        <FullBleedSection
          id="earth"
          imageSrc="/images/home/earth-disaster.webp"
          imageAlt="Earth observation multispectral satellite imagery"
        >
          <SectionHeadline>
            DISASTER INTELLIGENCE
          </SectionHeadline>
          <BodyParagraph>
            Segmentation and change detection on satellite imagery turn floods and fires into ranked observation priorities.
          </BodyParagraph>
          <div className="pt-2">
            <Button variant="ghost" href="/dashboard/disaster">
              EXPLORE EARTH INTEL
            </Button>
          </div>
        </FullBleedSection>

        {/* 7. ENGINE */}
        <FullBleedSection
          id="engine"
          imageSrc="/images/home/engine-space.webp"
          imageAlt="Spacecraft propulsion thruster firing in vacuum"
        >
          <SectionHeadline>
            ONE EXPLAINABLE SCORE
          </SectionHeadline>
          <BodyParagraph>
            A Mission Risk Engine fuses the three signals into a 0 to 100 score with drivers, confidence and a recommended action. Hard safety overrides stay transparent.
          </BodyParagraph>
          <div className="pt-2">
            <Button variant="ghost" href="/dashboard">
              SEE THE ENGINE
            </Button>
          </div>
        </FullBleedSection>

        {/* 8. HUMANS (Black Section) */}
        <FullBleedSection id="humans" isBlackOnly>
          <SectionHeadline>
            HUMANS DECIDE
          </SectionHeadline>
          <BodyParagraph>
            ASTRA-GUARD is advisory. Every recommendation needs operator approval, and every decision is logged.
          </BodyParagraph>
        </FullBleedSection>

        {/* 9. DEMO */}
        <FullBleedSection
          id="demo"
          imageSrc="/images/home/demo-space.webp"
          imageAlt="Satellite constellation passing over dark side of Earth"
        >
          <SectionHeadline>
            WATCH A DAY UNFOLD
          </SectionHeadline>
          <BodyParagraph>
            Replay a seeded mission scenario through the real pipeline, from the first drift to a critical alert.
          </BodyParagraph>
          <div className="pt-2">
            <Button variant="ghost" href="/demo">
              START DEMO
            </Button>
          </div>
        </FullBleedSection>

        {/* 10. EVIDENCE (Black Section) */}
        <FullBleedSection id="evidence" isBlackOnly>
          <SectionHeadline>
            MEASURED, NOT CLAIMED
          </SectionHeadline>
          <BodyParagraph>
            Every number comes from our evaluation scripts on public datasets.
          </BodyParagraph>
          <MetricsList />
        </FullBleedSection>
      </main>

      {/* 11. FOOTER */}
      <Footer />
    </div>
  );
}
