export const defaultLocale = "en";

export const supportedLocales = ["en", "tr"] as const;

export type Locale = (typeof supportedLocales)[number];

export function isSupported(locale: string): locale is Locale {
  return supportedLocales.includes(locale as Locale);
}
