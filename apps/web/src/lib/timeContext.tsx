"use client";

import React, { createContext, useContext, useEffect, useState, useCallback } from "react";

interface TimeContextType {
  currentTime: string;
  isPaused: boolean;
  speed: number;
  scrubTo: (timeIso: string) => void;
  togglePlayPause: () => void;
  setSpeed: (multiplier: number) => void;
  formatMissionTime: (timeIso: string) => string;
}

const BASE_MISSION_EPOCH = "2026-10-20T12:00:00.000Z";

const TimeContext = createContext<TimeContextType>({
  currentTime: BASE_MISSION_EPOCH,
  isPaused: false,
  speed: 1,
  scrubTo: () => {},
  togglePlayPause: () => {},
  setSpeed: () => {},
  formatMissionTime: (t) => t,
});

export function TimeProvider({ children }: { children: React.ReactNode }) {
  const [currentTime, setCurrentTime] = useState<string>(BASE_MISSION_EPOCH);
  const [isPaused, setIsPaused] = useState<boolean>(false);
  const [speed, setSpeedState] = useState<number>(1);

  // Initialize from URL param if available
  useEffect(() => {
    if (typeof window !== "undefined") {
      const params = new URLSearchParams(window.location.search);
      const urlTime = params.get("t") || params.get("time");
      if (urlTime) {
        const parsed = new Date(urlTime);
        if (!isNaN(parsed.getTime())) {
          setCurrentTime(parsed.toISOString());
        }
      }
    }
  }, []);

  // Update URL search param on scrubbing
  const scrubTo = useCallback((timeIso: string) => {
    const parsed = new Date(timeIso);
    if (!isNaN(parsed.getTime())) {
      const validIso = parsed.toISOString();
      setCurrentTime(validIso);

      if (typeof window !== "undefined") {
        const url = new URL(window.location.href);
        url.searchParams.set("t", validIso);
        window.history.replaceState({}, "", url.toString());
      }
    }
  }, []);

  const togglePlayPause = useCallback(() => {
    setIsPaused((prev) => !prev);
  }, []);

  const setSpeed = useCallback((multiplier: number) => {
    setSpeedState(multiplier);
  }, []);

  // Time advancement ticker
  useEffect(() => {
    if (isPaused) return;

    const interval = setInterval(() => {
      setCurrentTime((prev) => {
        const curr = new Date(prev).getTime();
        const next = new Date(curr + 1000 * speed);
        return next.toISOString();
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [isPaused, speed]);

  const formatMissionTime = useCallback((timeIso: string): string => {
    try {
      const d = new Date(timeIso);
      return d.toISOString().replace("T", " ").replace(/\.\d{3}Z$/, " UTC");
    } catch {
      return timeIso;
    }
  }, []);

  return (
    <TimeContext.Provider
      value={{
        currentTime,
        isPaused,
        speed,
        scrubTo,
        togglePlayPause,
        setSpeed,
        formatMissionTime,
      }}
    >
      {children}
    </TimeContext.Provider>
  );
}

export function useMissionTime() {
  return useContext(TimeContext);
}
