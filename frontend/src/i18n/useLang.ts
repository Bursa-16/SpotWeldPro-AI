/**
 * PUBLIC-01B: Language context.
 * State lives in PublicLayout (LangContext.Provider).
 * Pages consume via useLang() → useContext(LangContext).
 * No independent useState per caller — toggling in PublicLayout
 * immediately re-renders all consuming children.
 */
import { createContext, useContext } from 'react'
import type { Lang } from './publicContent'

const STORAGE_KEY = 'pub_lang'
const DEFAULT_LANG: Lang = 'tr'

/** Read language from localStorage; fall back to TR. */
export function getInitialLang(): Lang {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored === 'tr' || stored === 'en') return stored as Lang
  } catch {
    // localStorage unavailable (private browsing, blocked)
  }
  return DEFAULT_LANG
}

/** Persist language selection; silently ignores localStorage errors. */
export function persistLang(next: Lang): void {
  try {
    localStorage.setItem(STORAGE_KEY, next)
  } catch {
    // in-session toggle still works without persistence
  }
}

export interface LangContextValue {
  lang: Lang
  setLang: (next: Lang) => void
}

export const LangContext = createContext<LangContextValue>({
  lang: DEFAULT_LANG,
  setLang: () => {},
})

export function useLang(): LangContextValue {
  return useContext(LangContext)
}
