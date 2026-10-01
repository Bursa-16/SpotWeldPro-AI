/**
 * APP-I18N-01A: Hook for consuming the authenticated-app language context.
 *
 * Usage:
 *   const { lang, setLang, t } = useAppLanguage()
 *   // t = APP_CONTENT[lang]
 *   // e.g. t.analysisPage.title, t.stackEditor.coated, t.riskLabels['HIGH']
 *
 * Must be called inside a subtree wrapped by AppLanguageContext.Provider.
 * In the authenticated shell that Provider is in AuthenticatedApp.
 */
import { useContext } from 'react'
import { AppLanguageContext } from './AppLanguageContext'
import type { AppLanguageContextValue } from './AppLanguageContext'
import { APP_CONTENT } from './appContent'
import type { AppContent } from './appContent'

export interface UseAppLanguageResult extends AppLanguageContextValue {
  t: AppContent
}

export function useAppLanguage(): UseAppLanguageResult {
  const { lang, setLang } = useContext(AppLanguageContext)
  return { lang, setLang, t: APP_CONTENT[lang] }
}
