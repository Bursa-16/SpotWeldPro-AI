/**
 * Marketing-only entry point for GitHub Pages build.
 * Includes only public marketing routes — no auth, no engineering dashboard.
 * BrowserRouter basename matches the GitHub Pages sub-path /SpotWeldPro-AI/.
 */
import { StrictMode, useState } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import type { ReactNode } from 'react'
import { LangContext, getInitialLang, persistLang } from './i18n/useLang'
import type { Lang } from './i18n/publicContent'
import { LandingPage } from './pages/LandingPage'
import { FeaturesPage } from './pages/FeaturesPage'
import { HowItWorksPage } from './pages/HowItWorksPage'
import { PackagesPage } from './pages/PackagesPage'
import { DemoPage } from './pages/DemoPage'
import './styles.css'

function MarketingLangProvider({ children }: { children: ReactNode }) {
  const [lang, setLangState] = useState<Lang>(getInitialLang)
  function setLang(next: Lang) { persistLang(next); setLangState(next) }
  return <LangContext.Provider value={{ lang, setLang }}>{children}</LangContext.Provider>
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter basename="/SpotWeldPro-Web">
      <MarketingLangProvider>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/features" element={<FeaturesPage />} />
          <Route path="/how-it-works" element={<HowItWorksPage />} />
          <Route path="/packages" element={<PackagesPage />} />
          <Route path="/demo" element={<DemoPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </MarketingLangProvider>
    </BrowserRouter>
  </StrictMode>
)
