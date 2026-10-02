import { BrowserRouter, Routes, Route, Navigate, Outlet, useNavigate } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { DashboardPage } from './pages/DashboardPage'
import { EngineeringPage } from './pages/EngineeringPage'
import { LoginPage } from './pages/LoginPage'
import { FailureProbabilityPage } from './pages/FailureProbabilityPage'
import { AnalysisPage } from './pages/AnalysisPage'
import { ProjectsPage } from './pages/ProjectsPage'
import { WeldPointWizard } from './pages/WeldPointWizard'
import { LandingPage } from './pages/LandingPage'
import { FeaturesPage } from './pages/FeaturesPage'
import { HowItWorksPage } from './pages/HowItWorksPage'
import { PackagesPage } from './pages/PackagesPage'
import { DemoPage } from './pages/DemoPage'
import { AppLanguageContext, getInitialAppLang, persistAppLang } from './i18n/AppLanguageContext'
import { useAppLanguage } from './i18n/useAppLanguage'
import { LangContext, getInitialLang, persistLang } from './i18n/useLang'
import type { AppLanguage } from './i18n/appContent'
import type { Lang } from './i18n/publicContent'
import type { Project } from './types/project'
import './styles.css'

/* Public pre-login design system — global stylesheet injected once at root.
   Short lines only to keep the file writer stable. */
type Page = 'dashboard' | 'projects' | 'analysis' | 'engineering' | 'failure'

type NavItem = { id: Page; label: string; mk: string }
type NavGroup = { id: string; label: string; accordion: boolean; items: NavItem[] }

/** Static nav structure — internal IDs are stable, labels are translated at render time. */
const NAV: NavGroup[] = [
  {
    id: 'dash', label: 'Dashboard', accordion: false,
    items: [{ id: 'dashboard', label: 'Dashboard', mk: 'D' }],
  },
  {
    id: 'work', label: 'WORK', accordion: true,
    items: [
      { id: 'projects', label: 'Projects & Weld Points', mk: 'P' },
      { id: 'engineering', label: 'Weld Lobe Lab', mk: 'L' },
    ],
  },
  {
    id: 'analysis', label: 'ANALYSIS', accordion: true,
    items: [
      { id: 'analysis', label: 'Weld Quality Analysis', mk: 'Q' },
      { id: 'failure', label: 'Failure Analysis', mk: 'F' },
    ],
  },
]

function Sidebar({
  page, setPage, collapsed, setCollapsed, mobileOpen, setMobileOpen,
}: {
  page: Page
  setPage: (p: Page) => void
  collapsed: boolean
  setCollapsed: (v: boolean) => void
  mobileOpen: boolean
  setMobileOpen: (v: boolean) => void
}) {
  const { t } = useAppLanguage()

  const [open, setOpen] = useState<Record<string, boolean>>(() => {
    try { const s = localStorage.getItem('sb_open'); return s ? JSON.parse(s) : {} } catch { return {} }
  })

  useEffect(() => {
    const gid = NAV.find((g) => g.accordion && g.items.some((i) => i.id === page))?.id
    if (gid) {
      setOpen((prev) => {
        if (prev[gid]) return prev
        const next = { ...prev, [gid]: true }
        try { localStorage.setItem('sb_open', JSON.stringify(next)) } catch { /**/ }
        return next
      })
    }
  }, [page])

  useEffect(() => {
    if (!mobileOpen) return
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') setMobileOpen(false) }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [mobileOpen, setMobileOpen])

  function toggleGroup(id: string) {
    setOpen((prev) => {
      const next = { ...prev, [id]: !prev[id] }
      try { localStorage.setItem('sb_open', JSON.stringify(next)) } catch { /**/ }
      return next
    })
  }

  function handleNav(id: Page) {
    setPage(id)
    setMobileOpen(false)
  }

  function toggleCollapsed() {
    const next = !collapsed
    setCollapsed(next)
    try { localStorage.setItem('sb_collapsed', String(next)) } catch { /**/ }
  }

  const iconOnly = collapsed && !mobileOpen

  return (
    <>
      {mobileOpen && (
        <div className="sb-backdrop" aria-hidden="true" onClick={() => setMobileOpen(false)} />
      )}
      <aside className={'sidebar' + (mobileOpen ? ' sb-mobile-open' : '')} aria-label="Primary navigation">
        <div className="sidebar-brand">
          <div className="brand-mark" aria-hidden="true">SW</div>
          {!iconOnly && (
            <div className="brand-name">
              <strong>SpotWeldPro AI</strong>
              <span>Spot Welding Analysis</span>
            </div>
          )}
        </div>
        <nav className="sidebar-nav">
          {iconOnly ? (
            NAV.flatMap((g) => g.items).map((item) => (
              <button
                key={item.id}
                className={'nav-item' + (page === item.id ? ' active' : '')}
                aria-current={page === item.id ? 'page' : undefined}
                onClick={() => handleNav(item.id)}
                title={t.nav.items[item.id] ?? item.label}
              >
                <span className="nav-mk" aria-hidden="true">{item.mk}</span>
              </button>
            ))
          ) : (
            NAV.map((group) => {
              if (!group.accordion) {
                const item = group.items[0]
                return (
                  <button
                    key={item.id}
                    className={'nav-item' + (page === item.id ? ' active' : '')}
                    aria-current={page === item.id ? 'page' : undefined}
                    onClick={() => handleNav(item.id)}
                  >
                    <span className="nav-mk" aria-hidden="true">{item.mk}</span>
                    <span className="nav-label">{t.nav.items[item.id] ?? item.label}</span>
                  </button>
                )
              }
              const isOpen = !!open[group.id]
              const panelId = 'sbp-' + group.id
              return (
                <div key={group.id} className="sb-group">
                  <button
                    className="sb-group-hd"
                    aria-expanded={isOpen}
                    aria-controls={panelId}
                    onClick={() => toggleGroup(group.id)}
                  >
                    <span className="sb-group-label">{t.nav.groups[group.id] ?? group.label}</span>
                    <span className="sb-chevron" aria-hidden="true">{isOpen ? '▴' : '▾'}</span>
                  </button>
                  {isOpen && (
                    <div id={panelId} role="group">
                      {group.items.map((item) => (
                        <button
                          key={item.id}
                          className={'nav-item' + (page === item.id ? ' active' : '')}
                          aria-current={page === item.id ? 'page' : undefined}
                          onClick={() => handleNav(item.id)}
                        >
                          <span className="nav-mk" aria-hidden="true">{item.mk}</span>
                          <span className="nav-label">{t.nav.items[item.id] ?? item.label}</span>
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              )
            })
          )}
        </nav>
        <div className="sidebar-foot-wrap">
          <button
            className="sb-collapse-btn"
            aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            onClick={toggleCollapsed}
          >
            <span aria-hidden="true">{collapsed ? '▶' : '◀'}</span>
          </button>
        </div>
      </aside>
    </>
  )
}

function Topbar({ page, userName, onSignOut, onHamburger }: { page: Page; userName: string; onSignOut: () => void; onHamburger: () => void }) {
  const { lang, setLang, t } = useAppLanguage()
  const item = NAV.flatMap((g) => g.items).find((i) => i.id === page)
  const group = NAV.find((g) => g.items.some((i) => i.id === page))
  const title = t.nav.items[page] ?? item?.label ?? 'SpotWeldPro'
  const groupLabel = group ? (t.nav.groups[group.id] ?? group.label) : 'SpotWeldPro'
  const initials = userName.trim() ? userName.trim().split(/\s+/).slice(0, 2).map((w) => w[0]).join('').toUpperCase() : '…'

  function handleLang(next: AppLanguage) {
    persistAppLang(next)
    setLang(next)
  }

  return (
    <header className="topbar">
      <div className="topbar-start">
        <button className="hamburger-btn" aria-label="Open navigation" onClick={onHamburger}>
          <span aria-hidden="true">☰</span>
        </button>
        <div className="topbar-module">
          <span className="topbar-title">{title}</span>
          <span className="topbar-crumb">SpotWeldPro AI / {groupLabel}</span>
        </div>
      </div>
      <div className="topbar-user">
        <div className="lang-switch" role="group" aria-label="Language">
          {(['tr', 'en'] as AppLanguage[]).map((l) => (
            <button
              key={l}
              type="button"
              className={'lang-btn' + (lang === l ? ' lang-btn-active' : '')}
              aria-pressed={lang === l}
              onClick={() => handleLang(l)}
            >
              {l.toUpperCase()}
            </button>
          ))}
        </div>
        <span className="user-chip"><span className="user-avatar" aria-hidden="true">{initials}</span>{userName}</span>
        <button className="signout-btn" onClick={onSignOut}>
          {t.topbar.signOut}
        </button>
      </div>
    </header>
  )
}

/* Authenticated application shell — preserved from the existing app.
   Runs ONLY under /app; guarded by the demo session marker. */
function AuthenticatedApp() {
  const [authenticated, setAuthenticated] = useState(Boolean(localStorage.getItem('access_token')))
  const [page, setPage] = useState<Page>('dashboard')
  const [project, setProject] = useState<Project | null>(null)
  const [userName, setUserName] = useState('')
  const [collapsed, setCollapsed] = useState(() => {
    try { return localStorage.getItem('sb_collapsed') === 'true' } catch { return false }
  })
  const [mobileOpen, setMobileOpen] = useState(false)
  const [lang, setLang] = useState<AppLanguage>(getInitialAppLang)
  const navigate = useNavigate()

  if (!authenticated) return <Navigate to="/login" replace />
  if (project) return <WeldPointWizard project={project} onBack={() => setProject(null)} />

  if (!userName) {
    setUserName('Demo Engineer — Engineering')
  }

  return (
    <AppLanguageContext.Provider value={{ lang, setLang }}>
      <div className={'app-shell' + (collapsed ? ' shell-collapsed' : '')}>
        <Topbar
          page={page}
          userName={userName || '…'}
          onSignOut={() => {
            localStorage.clear()
            navigate('/login')
          }}
          onHamburger={() => setMobileOpen(true)}
        />
        <Sidebar
          page={page} setPage={setPage}
          collapsed={collapsed} setCollapsed={setCollapsed}
          mobileOpen={mobileOpen} setMobileOpen={setMobileOpen}
        />
        <main className="main">
          {page === 'dashboard' && <DashboardPage />}
          {page === 'projects' && <ProjectsPage onOpen={setProject} />}
          {page === 'analysis' && <AnalysisPage />}
          {page === 'engineering' && <EngineeringPage />}
          {page === 'failure' && <FailureProbabilityPage />}
        </main>
      </div>
    </AppLanguageContext.Provider>
  )
}

/* Public /login route — demo credentials only, frontend mock session. */
function PublicLogin() {
  const navigate = useNavigate()
  return (
    <LoginPage
      onLogin={() => {
        navigate('/app')
      }}
    />
  )
}

/**
 * PUBLIC-I18N-01-HF2: Single source of truth for public language state.
 * Owns useState<Lang>, reads localStorage via getInitialLang(), writes via
 * persistLang(). Renders LangContext.Provider so every descendant — both the
 * page component AND its <PublicLayout> child — reads from the same reactive
 * context value.  PublicLayout is now a pure consumer (useLang() only).
 *
 * Uses React Router's layout-route / Outlet pattern so the Provider is NOT
 * remounted on navigation between public routes — lang state survives
 * cross-route navigation, fulfilling the route persistence requirement.
 */
function PublicLangProvider() {
  const [lang, setLangState] = useState<Lang>(getInitialLang)

  function setLang(next: Lang) {
    persistLang(next)
    setLangState(next)
  }

  return (
    <LangContext.Provider value={{ lang, setLang }}>
      <Outlet />
    </LangContext.Provider>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<PublicLangProvider />}>
          <Route path="/" element={<LandingPage />} />
          <Route path="/features" element={<FeaturesPage />} />
          <Route path="/how-it-works" element={<HowItWorksPage />} />
          <Route path="/packages" element={<PackagesPage />} />
          <Route path="/demo" element={<DemoPage />} />
          <Route path="/login" element={<PublicLogin />} />
        </Route>
        <Route path="/app" element={<AuthenticatedApp />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
