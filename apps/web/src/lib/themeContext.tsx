"use client";

import React, { createContext, useContext, useEffect, useState } from "react";

export type Theme = "night" | "day";

interface ThemeContextType {
  theme: Theme;
  isNight: boolean;
  isDay: boolean;
  toggleTheme: () => void;
  setTheme: (theme: Theme) => void;
}

const ThemeContext = createContext<ThemeContextType>({
  theme: "night",
  isNight: true,
  isDay: false,
  toggleTheme: () => {},
  setTheme: () => {},
});

function applyThemeToDocument(t: Theme) {
  if (typeof document === "undefined") return;
  const root = document.documentElement;
  if (t === "day") {
    root.classList.remove("dark");
    root.classList.add("light");
    root.setAttribute("data-theme", "light");
    root.style.colorScheme = "light";
  } else {
    root.classList.remove("light");
    root.classList.add("dark");
    root.setAttribute("data-theme", "dark");
    root.style.colorScheme = "dark";
  }
}

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setThemeState] = useState<Theme>("night");
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    try {
      const saved = localStorage.getItem("astraguard_theme") as Theme | null;
      if (saved === "day" || saved === "night") {
        setThemeState(saved);
        applyThemeToDocument(saved);
      } else {
        // Default to night mode (aerospace dark spec), or respect light preference
        const prefersLight = window.matchMedia("(prefers-color-scheme: light)").matches;
        const initial: Theme = prefersLight ? "day" : "night";
        setThemeState(initial);
        applyThemeToDocument(initial);
      }
    } catch {
      // localStorage may be unavailable in some iframe/restricted contexts
    }
    setMounted(true);
  }, []);

  const setTheme = (nextTheme: Theme) => {
    setThemeState(nextTheme);
    applyThemeToDocument(nextTheme);
    try {
      localStorage.setItem("astraguard_theme", nextTheme);
    } catch {
      // quiet fallback
    }
  };

  const toggleTheme = () => {
    setTheme(theme === "night" ? "day" : "night");
  };

  return (
    <ThemeContext.Provider
      value={{
        theme,
        isNight: !mounted || theme === "night",
        isDay: mounted && theme === "day",
        toggleTheme,
        setTheme,
      }}
    >
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error("useTheme must be used within a ThemeProvider");
  }
  return context;
}
