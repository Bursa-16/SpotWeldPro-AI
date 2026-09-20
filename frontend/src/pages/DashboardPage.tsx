
import { useEffect, useState } from 'react'
import { currentUser, dashboard } from '../api/client'

type DashboardData = {
  total_projects: number
  active_projects: number
  total_weld_points: number
  risky_weld_points: number
  pending_approvals: number
  rejected_approvals: number
  total_users: number
  recent_audit_events: number
}

export function DashboardPage() {
  const [data, setData] = useState<DashboardData | null>(null)
  const [user, setUser] = useState<{ full_name: string; role: string } | null>(null)
  const [error, setError] = useState(false)

  useEffect(() => {
    Promise.all([dashboard(), currentUser()])
      .then(([d, u]) => {
        setData(d)
        setUser(u)
      })
      .catch(() => setError(true))
  }, [])

  if (error) {
    return (
      <div className="page active">
        <div className="ws-kicker">Command Center</div>
        <header className="page-header">
          <div>
            <h1>Command Center</h1>
            <p className="subtitle">Production quality and engineering overview</p>
          </div>
        </header>
        <div className="alert danger" role="alert">
          <div>
            <div className="alert-title">Backend connection unavailable</div>
            <div className="alert-text">Engineering data could not be loaded. Verify the API service and retry.</div>
          </div>
        </div>
      </div>
    )
  }

  if (!data) {
    return (
      <div className="page active">
        <div className="state-msg" role="status">
          <div className="spinner" aria-hidden="true" />
          <span>Loading command center…</span>
        </div>
      </div>
    )
  }

  const cards: { label: string; value: number; state?: 'ok' | 'warn' | 'danger'; sub?: string }[] = [
    { label: 'Total Projects', value: data.total_projects },
    { label: 'Active Projects', value: data.active_projects, state: 'ok' },
    { label: 'Total Weld Points', value: data.total_weld_points },
    { label: 'Risky Weld Points', value: data.risky_weld_points, state: data.risky_weld_points > 0 ? 'warn' : undefined, sub: data.risky_weld_points > 0 ? 'engineering review required' : 'no review required' },
    { label: 'Pending Approvals', value: data.pending_approvals, state: data.pending_approvals > 0 ? 'warn' : undefined, sub: 'awaiting human decision' },
    { label: 'Rejected Approvals', value: data.rejected_approvals, state: data.rejected_approvals > 0 ? 'danger' : undefined },
    { label: 'Users', value: data.total_users },
    { label: 'Audit Events (7 d)', value: data.recent_audit_events },
  ]

  return (
    <div className="page active">
      <div className="ws-kicker">Overview · Spot Welding Parametre Analysis</div>
      <header className="page-header">
        <div>
          <h1>Command Center</h1>
          <p className="subtitle">
            {user ? `${user.full_name} — ${user.role}` : '…'} · production quality &amp; engineering overview
          </p>
        </div>
      </header>
      <div className="ws-context-bar" aria-label="Engineering context">
        <span className="ctx-chip accent">Authority: <strong>deterministic rules</strong></span>
        <span className="ctx-chip info">AI role: <strong>explanatory support</strong></span>
        <span className="ctx-chip">Traceability: <strong>audit-backed</strong></span>
      </div>
      <div className="ws-zone-label">Status overview</div>
      <section className="grid-4" aria-label="Key production metrics">
        {cards.map((c) => (
          <article className={`metric-card${c.state ? ` state-${c.state}` : ''}`} key={c.label}>
            <span className="metric-label">{c.label}</span>
            <strong className="metric-value">{c.value}</strong>
            {c.sub && <span className="metric-sub">{c.sub}</span>}
          </article>
        ))}
      </section>
      <div className="ws-grid-main" style={{ marginTop: 'var(--sp-5)' }}>
        <section className="panel" aria-label="Engineering activity">
          <div className="panel-header"><h3>Engineering activity</h3><span className="panel-meta">current backend state</span></div>
          <div className="panel-body">
          <div className="trace-block">
            <div className="trace-row"><span className="label">Projects</span><span className="value">{data.total_projects} total · {data.active_projects} active</span></div>
            <div className="trace-row"><span className="label">Weld points</span><span className="value">{data.total_weld_points} total · {data.risky_weld_points} risky</span></div>
            <div className="trace-row"><span className="label">Approvals</span><span className="value">{data.pending_approvals} pending · {data.rejected_approvals} rejected</span></div>
          </div>
          </div>
          <div className="panel-footer">Live backend counts only — no sampled metrics.</div>
        </section>
        <section className="panel" aria-label="System readiness">
          <div className="panel-header"><h3>System readiness</h3><span className="panel-meta">connection</span></div>
          <div className="panel-body">
          <div className="trace-block">
            <div className="trace-row"><span className="label">Backend</span><span className="value">connected</span></div>
            <div className="trace-row"><span className="label">Audit events (7 d)</span><span className="value">{data.recent_audit_events}</span></div>
            <div className="trace-row"><span className="label">Users</span><span className="value">{data.total_users}</span></div>
          </div>
          </div>
          <div className="panel-footer">Audit-backed traceability context.</div>
        </section>
      </div>
    </div>
  )
}
