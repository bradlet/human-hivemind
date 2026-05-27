import { useLayoutEffect, useState } from "react";

type DarkModeApi = {
  isDark: boolean;
  toggle: () => void;
};

function getInitialIsDark(): boolean {
  if (typeof window === "undefined") return false;
  try {
    const stored = window.localStorage.getItem("theme");
    if (stored === "dark") return true;
    if (stored === "light") return false;
  } catch {
    // ignore — fall through to system preference
  }
  return window.matchMedia("(prefers-color-scheme: dark)").matches;
}

export function useDarkMode(): DarkModeApi {
  const [isDark, setIsDark] = useState<boolean>(getInitialIsDark);

  useLayoutEffect(() => {
    const root = document.documentElement;
    if (isDark) {
      root.classList.add("dark");
    } else {
      root.classList.remove("dark");
    }
    try {
      window.localStorage.setItem("theme", isDark ? "dark" : "light");
    } catch {
      // storage unavailable — non-fatal
    }
  }, [isDark]);

  return {
    isDark,
    toggle: () => setIsDark((v) => !v),
  };
}

export default useDarkMode;
