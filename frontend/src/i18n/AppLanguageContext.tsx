/**
 * APP-I18N-01A: Global authenticated-app language context.
 *
 * State lives in AuthenticatedApp (AppLanguageContext.Provider).
 * Components consume via useAppLanguage() → useContext(AppLanguageContext).
 * One toggle in AuthenticatedApp re-renders all consuming children.
 *
 * Storage key : spotweldpro_lang
 * Default     : tr
 * Type        : AppLanguage = 'tr' | 'en'
 *
 * Does NOT interfere with:
 *   - access_token (authentication)
 *   - sb_collapsed / sb_open (sidebar)
 *   - pub_lang (public pre-login layer)
 */
import { createContext } from 'react'
import type { AppLanguage } from './appContent'

const STORAGE_KEY = 'spotweldpro_lang'
const DEFAULT_LANG: AppLanguage = 'tr'

/** Read language from localStorage; fall back to TR. */
export function getInitialAppLang(): AppLanguage {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored === 'tr' || stored === 'en') return stored as AppLanguage
  } catch {
    // localStorage unavailable (private browsing, blocked)
  }
  return DEFAULT_LANG
}

/** Persist language selection; silently ignores localStorage errors. */
export function persistAppLang(next: AppLanguage): void {
  try {
    localStorage.setItem(STORAGE_KEY, next)
  } catch {
    // in-session toggle still works without persistence
  }
}

export interface AppLanguageContextValue {
  lang: AppLanguage
  setLang: (next: AppLanguage) => void
}

export const AppLanguageContext = createContext<AppLanguageContextValue>({
  lang: DEFAULT_LANG,
  setLang: () => {},
})
