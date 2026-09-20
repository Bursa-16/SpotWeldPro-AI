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
const PUBLIC_CSS_A = [
  '.pub-topnav{position:sticky;top:0;z-index:50;display:flex;align-items:center;gap:var(--sp-4);padding:10px 28px;background:var(--bg-surface);border-bottom:1px solid var(--border)}',
  '.pub-brand{display:flex;align-items:center;gap:var(--sp-3);font-weight:600;font-size:var(--fs-h4);color:var(--text-primary);text-decoration:none}',
  '.pub-nav-links{display:flex;gap:2px;flex-wrap:wrap}',
  '.pub-nav-links a{color:var(--text-secondary);text-decoration:none;font-size:var(--fs-body);padding:6px 12px;border-radius:var(--r-md)}',
  '.pub-nav-links a:hover{color:var(--text-primary);background:var(--bg-surface-2)}',
  '.pub-nav-links a.active{color:var(--accent);background:var(--accent-soft)}',
].join('')

const PUBLIC_CSS_B1 = [
  '.pub-main{max-width:1180px;margin:0 auto;padding:0 24px}',
  '.pub-section{margin:var(--sp-7) 0}',
  '.pub-h2{font-size:var(--fs-h2);font-weight:600;letter-spacing:-0.01em;margin-bottom:var(--sp-2)}',
  '.pub-sub{color:var(--text-secondary);font-size:var(--fs-body);margin-bottom:var(--sp-3)}',
  '.pub-card{background:var(--bg-surface);border:1px solid var(--border);border-radius:var(--r-lg);padding:var(--sp-5);display:flex;flex-direction:column;gap:var(--sp-3)}',
  '.pub-card-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:var(--sp-4)}',
  '.pub-icon{width:34px;height:34px;border-radius:var(--r-sm);background:var(--accent-soft);border:1px solid var(--border);display:grid;place-items:center;color:var(--accent);font-weight:700;font-size:var(--fs-sm)}',
  '.pub-tag{display:inline-block;font-size:var(--fs-xs);color:var(--text-tertiary);border:1px solid var(--border);padding:2px 8px;border-radius:999px;white-space:nowrap}',
  '.pub-note{font-size:var(--fs-xs);color:var(--text-tertiary)}',
  '.pub-footer{margin-top:var(--sp-8);padding:var(--sp-5) 0;border-top:1px solid var(--border);color:var(--text-tertiary);font-size:var(--fs-xs);text-align:center}',
  '.pub-hero{display:grid;grid-template-columns:minmax(0,1.05fr) minmax(0,0.95fr);gap:var(--sp-6);align-items:start;padding:52px 24px;border-bottom:1px solid var(--border);max-width:1180px;margin:0 auto}',
  '.pub-hero .eyebrow{font-size:var(--fs-xs);text-transform:uppercase;letter-spacing:0.12em;color:var(--accent);font-weight:600;margin-bottom:var(--sp-3)}',
  '.pub-hero h1{font-size:1.75rem;font-weight:650;letter-spacing:-0.015em;line-height:1.2}',
  '.pub-hero .lead{font-size:var(--fs-body-lg);color:var(--text-secondary);max-width:780px;margin:var(--sp-4) 0 0}',
  '.pub-cta{display:flex;flex-wrap:wrap;gap:var(--sp-3);margin:var(--sp-5) 0}',
  '.pub-link-cta{color:var(--text-secondary);text-decoration:none;font-size:var(--fs-body);padding:var(--sp-2) var(--sp-4);border:1px solid var(--border);border-radius:var(--r-md)}',
  '.pub-link-cta:hover{color:var(--text-primary);border-color:var(--border-strong)}',
  '.pub-trust{display:flex;gap:var(--sp-3);padding:var(--sp-4) var(--sp-5);border:1px solid var(--border);border-radius:var(--r-lg);background:var(--bg-surface-2);color:var(--text-secondary);font-size:var(--fs-body);margin:var(--sp-6) 0}',
  '.pub-trust b{color:var(--text-primary)}',
  '.pub-industry-card{border:1px solid var(--border);border-radius:var(--r-lg);background:var(--bg-surface);padding:var(--sp-4);cursor:pointer;text-align:left;display:flex;flex-direction:column;gap:var(--sp-2)}',
  '.pub-industry-card:hover{border-color:var(--border-strong)}',
  '.pub-industry-card.open{border-color:var(--accent);background:var(--bg-surface-2)}',
  '.pub-pkg-mini{border:1px solid var(--border);border-radius:var(--r-lg);background:var(--bg-surface);padding:var(--sp-4);display:flex;flex-direction:column;gap:var(--sp-2)}',
  '.pub-mod-list{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:var(--sp-4)}',
  '.pub-mod-btn{border:1px solid var(--border);border-radius:var(--r-lg);background:var(--bg-surface);padding:var(--sp-4);text-align:left;cursor:pointer;display:flex;flex-direction:column;gap:var(--sp-2)}',
  '.pub-mod-btn:hover{border-color:var(--border-strong)}',
  '.pub-mod-btn.active{border-color:var(--accent);background:var(--bg-surface-2)}',
  '.pub-mod-detail{border:1px solid var(--accent);border-radius:var(--r-lg);background:var(--bg-surface-2);padding:var(--sp-5);display:flex;flex-direction:column;gap:var(--sp-3);margin-top:var(--sp-5)}',
  '.pub-dl{display:grid;grid-template-columns:130px 1fr;gap:var(--sp-2) var(--sp-3);font-size:var(--fs-body)}',
  '.pub-dl dt{color:var(--text-tertiary);font-size:var(--fs-xs);text-transform:uppercase;letter-spacing:0.06em}',
  '.pub-dl dd{color:var(--text-primary);margin:0}',
].join('')

const PUBLIC_CSS_B2 = [
  '.pub-steps{display:flex;flex-wrap:wrap;gap:var(--sp-2)}',
  '.pub-step-btn{border:1px solid var(--border);border-radius:999px;background:var(--bg-surface);color:var(--text-secondary);padding:var(--sp-2) var(--sp-3);font-size:var(--fs-sm);cursor:pointer}',
  '.pub-step-btn:hover{color:var(--text-primary);border-color:var(--border-strong)}',
  '.pub-step-btn.active{background:var(--accent-soft);color:var(--accent);border-color:var(--accent)}',
  '.pub-step-card{border:1px solid var(--accent);border-radius:var(--r-lg);background:var(--bg-surface-2);padding:var(--sp-5);display:flex;flex-direction:column;gap:var(--sp-3)}',
  '.pub-ctrl{display:flex;gap:var(--sp-3);margin-top:var(--sp-4)}',
  '.pub-pkg-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:var(--sp-4)}',
  '.pub-pkg{border:1px solid var(--border);border-radius:var(--r-lg);background:var(--bg-surface);padding:var(--sp-5);display:flex;flex-direction:column;gap:var(--sp-3)}',
  '.pub-preview{background:var(--bg-surface);border:1px solid var(--border);border-radius:var(--r-lg);overflow:hidden;box-shadow:0 1px 2px rgba(0,0,0,0.25)}',
  '.pub-preview-head{display:flex;align-items:center;justify-content:space-between;padding:var(--sp-3) var(--sp-4);border-bottom:1px solid var(--border);background:var(--bg-surface-2);font-size:var(--fs-xs);color:var(--text-tertiary);text-transform:uppercase;letter-spacing:0.08em;font-weight:600}',
  '.pub-preview-body{padding:var(--sp-4);display:flex;flex-direction:column;gap:var(--sp-3)}',
  '.pub-preview-grid{display:grid;grid-template-columns:1fr 1fr;gap:var(--sp-2)}',
  '.pub-preview-field{border:1px solid var(--border);border-radius:var(--r-sm);background:var(--bg-surface-2);padding:var(--sp-2) var(--sp-3);font-size:var(--fs-xs);color:var(--text-tertiary);display:flex;flex-direction:column;gap:2px}',
  '.pub-preview-lobe{border:1px solid var(--border);border-radius:var(--r-sm);background:var(--bg-surface-2);padding:var(--sp-3)}',
  '.pub-preview-axes{height:84px;border-left:1px solid var(--border-strong);border-bottom:1px solid var(--border-strong);position:relative}',
  '.pub-preview-axes::before{content:\"\";position:absolute;left:14%;right:14%;top:32%;bottom:32%;border:1px dashed var(--border-strong);border-radius:var(--r-sm)}',
  '.pub-preview-row{display:flex;flex-wrap:wrap;gap:var(--sp-2)}',
  '.pub-preview-foot{padding:var(--sp-3) var(--sp-4);border-top:1px solid var(--border);font-size:var(--fs-xs);color:var(--text-tertiary);background:var(--bg-surface-2)}',
  '@media (max-width:1024px){.pub-hero{grid-template-columns:1fr}}',
  '.pub-pkg.open{border-color:var(--accent);background:var(--bg-surface-2)}',
  '.pub-table{width:100%;border-collapse:collapse;font-size:var(--fs-body)}',
  '.pub-table th,.pub-table td{border:1px solid var(--border);padding:var(--sp-2) var(--sp-3);text-align:left}',
  '.pub-table th{background:var(--bg-surface-2);color:var(--text-secondary);font-weight:600}',
  '.pub-demo-dots{display:flex;gap:var(--sp-2);align-items:center}',
  '.pub-dot{width:10px;height:10px;border-radius:50%;border:1px solid var(--border);background:var(--bg-surface);cursor:pointer}',
  '.pub-dot.done{background:var(--ok-soft);border-color:var(--ok)}',
  '.pub-dot.current{background:var(--accent);border-color:var(--accent)}',
  '.pub-demo-stage{border:1px solid var(--accent);border-radius:var(--r-lg);background:var(--bg-surface-2);padding:var(--sp-5);display:flex;flex-direction:column;gap:var(--sp-3)}',
  '.pub-metric{border:1px solid var(--border);border-radius:var(--r-md);background:var(--bg-surface);padding:var(--sp-3) var(--sp-4)}',
  '.pub-demo-badge{display:inline-flex;align-items:center;gap:var(--sp-2);padding:2px var(--sp-3);border-radius:999px;font-size:var(--fs-xs);font-weight:600;color:var(--warn);border:1px solid var(--warn)}',
  '@media(max-width:760px){.pub-topnav{flex-wrap:wrap;gap:var(--sp-2)}.pub-card-grid{grid-template-columns:1fr}.pub-hero{padding:28px 16px}.pub-hero h1{font-size:1.35rem}.pub-pkg-grid{grid-template-columns:1fr}.pub-mod-list{grid-template-columns:1fr}}',
].join('')

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
        <style>{PUBLIC_CSS_A + PUBLIC_CSS_B1 + PUBLIC_CSS_B2}</style>
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
