"use client";

import React, { createContext, useContext, useState, useCallback, ReactNode } from "react";
import { defaultLocale, isSupported, Locale } from "./config";

import en from "./locales/en.json";
import tr from "./locales/tr.json";

const messages: Record<Locale, Record<string, any>> = { en, tr };

interface I18nContextType {
  locale: Locale;
  setLocale: (l: Locale) => void;
  t: (key: string) => string;
}

const I18nContext = createContext<I18nContextType | null>(null);

export function I18nProvider({ children, initialLocale }: { children: ReactNode; initialLocale?: string }) {
  const [locale, setLocaleState] = useState<Locale>(
    isSupported(initialLocale || "") ? (initialLocale as Locale) : defaultLocale
  );

  const setLocale = useCallback((l: Locale) => {
    setLocaleState(l);
    localStorage.setItem("locale", l);
  }, []);

  const t = useCallback(
    (key: string): string => {
      const parts = key.split(".");
      let val: any = messages[locale];
      for (const p of parts) {
        val = val?.[p];
      }
      if (typeof val === "string") return val;
      // Fallback to default locale
      val = messages[defaultLocale];
      for (const p of parts) {
        val = val?.[p];
      }
      return typeof val === "string" ? val : key;
    },
    [locale]
  );

  return <I18nContext.Provider value={{ locale, setLocale, t }}>{children}</I18nContext.Provider>;
}

export function useI18n() {
  const ctx = useContext(I18nContext);
  if (!ctx) throw new Error("useI18n must be used within I18nProvider");
  return ctx;
}
