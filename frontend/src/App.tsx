import { BrowserRouter, Routes, Route, Navigate, useNavigate } from 'react-router-dom'
import { useState } from 'react'
import { DashboardPage } from './pages/DashboardPage'
import { EngineeringPage } from './pages/EngineeringPage'
import { LoginPage } from './pages/LoginPage'
import { OptimizationPage } from './pages/OptimizationPage'
import { FailureProbabilityPage } from './pages/FailureProbabilityPage'
import { AnalysisPage } from './pages/AnalysisPage'
import { ProjectsPage } from './pages/ProjectsPage'
import { WeldPointWizard } from './pages/WeldPointWizard'
import { LandingPage } from './pages/LandingPage'
import { FeaturesPage } from './pages/FeaturesPage'
import { HowItWorksPage } from './pages/HowItWorksPage'
import { PackagesPage } from './pages/PackagesPage'
import { DemoPage } from './pages/DemoPage'
import type { Project } from './types/project'
import './styles.css'

/* Public pre-login design system — global stylesheet injected once at root.
   Short lines only to keep the file writer stable. */
type Page = 'dashboard' | 'projects' | 'analysis' | 'engineering' | 'optimization' | 'failure'

const NAV: { section: string; items: { id: Page; label: string; code: string }[] }[] = [
  {
    section: 'Overview',
    items: [{ id: 'dashboard', label: 'Command Center', code: 'CC' }],
  },
  {
    section: 'Production',
    items: [
      { id: 'projects', label: 'Projects & Weld Points', code: 'PW' },
      { id: 'analysis', label: 'Weld Quality Analysis', code: 'WQ' },
    ],
  },
  {
    section: 'Engineering',
    items: [
      { id: 'engineering', label: 'Weld Lobe Lab', code: 'WL' },
      { id: 'optimization', label: 'DOE Optimization', code: 'DO' },
      { id: 'failure', label: 'Failure Analysis', code: 'FA' },
    ],
  },
]

function Sidebar({ page, setPage }: { page: Page; setPage: (p: Page) => void }) {
  return (
    <aside className="sidebar" aria-label="Primary navigation">
      <div className="sidebar-brand">
        <div className="brand-mark" aria-hidden="true">SW</div>
        <div className="brand-name">
          <strong>SpotWeldPro AI</strong>
          <span>Spot Welding Parametre Analysis</span>
        </div>
      </div>
      <nav className="sidebar-nav">
        {NAV.map((group) => (
          <div key={group.section} className="sidebar-group">
            <div className="nav-section">{group.section}</div>
            {group.items.map((item) => (
              <button
                key={item.id}
                className={'nav-item' + (page === item.id ? ' active' : '')}
                aria-current={page === item.id ? 'page' : undefined}
                onClick={() => setPage(item.id)}
              >
                <span className="nav-code" aria-hidden="true">{item.code}</span>
                <span className="nav-label">{item.label}</span>
                {page === item.id && <span className="nav-dot" aria-hidden="true" />}
              </button>
            ))}
          </div>
        ))}
      </nav>
      <div className="sidebar-foot">Engineering workstation · deterministic authority preserved</div>
    </aside>
  )
}

function Topbar({ page, userName, onSignOut }: { page: Page; userName: string; onSignOut: () => void }) {
  const item = NAV.flatMap((g) => g.items).find((i) => i.id === page)
  const group = NAV.find((g) => g.items.some((i) => i.id === page))?.section ?? 'SpotWeldPro'
  const title = item?.label ?? 'SpotWeldPro'
  const initials = userName.trim() ? userName.trim().split(/\s+/).slice(0, 2).map((w) => w[0]).join('').toUpperCase() : '…'
  return (
    <header className="topbar">
      <div className="topbar-module">
        <span className="topbar-title">{title}</span>
        <span className="topbar-crumb">SpotWeldPro AI / {group}</span>
      </div>
      <div className="topbar-user">
        <span className="user-chip"><span className="user-avatar" aria-hidden="true">{initials}</span>{userName}</span>
        <button className="signout-btn" onClick={onSignOut}>
          Sign out
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
  const navigate = useNavigate()

  if (!authenticated) return <Navigate to="/login" replace />
  if (project) return <WeldPointWizard project={project} onBack={() => setProject(null)} />

  if (!userName) {
    setUserName('Demo Engineer — Engineering')
  }

  return (
    <div className="app-shell">
      <Topbar
        page={page}
        userName={userName || '…'}
        onSignOut={() => {
          localStorage.clear()
          navigate('/login')
        }}
      />
      <Sidebar page={page} setPage={setPage} />
      <main className="main">
        {page === 'dashboard' && <DashboardPage />}
        {page === 'projects' && <ProjectsPage onOpen={setProject} />}
        {page === 'analysis' && <AnalysisPage />}
        {page === 'engineering' && <EngineeringPage />}
        {page === 'optimization' && <OptimizationPage />}
        {page === 'failure' && <FailureProbabilityPage />}
      </main>
    </div>
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

export default function App() {
  return (
    <BrowserRouter>

      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/features" element={<FeaturesPage />} />
        <Route path="/how-it-works" element={<HowItWorksPage />} />
        <Route path="/packages" element={<PackagesPage />} />
        <Route path="/demo" element={<DemoPage />} />
        <Route path="/login" element={<PublicLogin />} />
        <Route path="/app" element={<AuthenticatedApp />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
