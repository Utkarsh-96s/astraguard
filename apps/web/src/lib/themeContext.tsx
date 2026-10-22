"use client";

import React, { createContext, useContext, useEffect } from "react";

export type Theme = "night";

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

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    try {
      localStorage.removeItem("astraguard_theme");
      const root = document.documentElement;
      root.classList.remove("light");
      root.classList.add("dark");
      root.setAttribute("data-theme", "dark");
      root.style.colorScheme = "dark";
    } catch {
      // quiet fallback
    }
  }, []);

  return (
    <ThemeContext.Provider
      value={{
        theme: "night",
        isNight: true,
        isDay: false,
        toggleTheme: () => {},
        setTheme: () => {},
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
