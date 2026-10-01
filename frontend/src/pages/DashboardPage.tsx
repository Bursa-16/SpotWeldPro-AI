
import { useEffect, useState } from 'react'
import { currentUser, dashboard } from '../api/client'
import { useAppLanguage } from '../i18n/useAppLanguage'

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
  const { t } = useAppLanguage()

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
        <div className="ws-kicker">{t.dashboardPage.kicker}</div>
        <header className="page-header">
          <div>
            <h1>{t.dashboardPage.title}</h1>
            <p className="subtitle">{t.dashboardPage.subtitle}</p>
          </div>
        </header>
        <div className="alert danger" role="alert">
          <div>
            <div className="alert-title">{t.dashboardPage.errorTitle}</div>
            <div className="alert-text">{t.dashboardPage.errorText}</div>
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
          <span>{t.dashboardPage.loading}</span>
        </div>
      </div>
    )
  }

  const d = t.dashboardPage
  const cards: { label: string; value: number; state?: 'ok' | 'warn' | 'danger'; sub?: string }[] = [
    { label: d.totalProjects, value: data.total_projects },
    { label: d.activeProjects, value: data.active_projects, state: 'ok' },
    { label: d.totalWeldPoints, value: data.total_weld_points },
    { label: d.riskyWeldPoints, value: data.risky_weld_points, state: data.risky_weld_points > 0 ? 'warn' : undefined, sub: data.risky_weld_points > 0 ? d.engineeringReview : d.noReview },
    { label: d.pendingApprovals, value: data.pending_approvals, state: data.pending_approvals > 0 ? 'warn' : undefined, sub: d.awaitingDecision },
    { label: d.rejectedApprovals, value: data.rejected_approvals, state: data.rejected_approvals > 0 ? 'danger' : undefined },
    { label: d.users, value: data.total_users },
    { label: d.auditEvents, value: data.recent_audit_events },
  ]

  const roleLabel = t.roleLabels[user?.role ?? ''] ?? user?.role ?? ''

  return (
    <div className="page active">
      <div className="ws-kicker">{d.kickerData}</div>
      <header className="page-header">
        <div>
          <h1>{d.title}</h1>
          <p className="subtitle">
            {user ? `${user.full_name} — ${roleLabel}` : '…'} · {d.subtitle}
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
          <div className="panel-header"><h3>{d.engineeringActivity}</h3><span className="panel-meta">{d.engineeringActivityMeta}</span></div>
          <div className="panel-body">
          <div className="trace-block">
            <div className="trace-row"><span className="label">{d.projects}</span><span className="value">{data.total_projects} {d.total} · {data.active_projects} {d.active}</span></div>
            <div className="trace-row"><span className="label">{d.weldPoints}</span><span className="value">{data.total_weld_points} {d.total} · {data.risky_weld_points} {d.risky}</span></div>
            <div className="trace-row"><span className="label">{d.approvals}</span><span className="value">{data.pending_approvals} {d.pending} · {data.rejected_approvals} {d.rejected}</span></div>
          </div>
          </div>
          <div className="panel-footer">{d.activityFooter}</div>
        </section>
        <section className="panel" aria-label="System readiness">
          <div className="panel-header"><h3>{d.systemReadiness}</h3><span className="panel-meta">{d.systemReadinessMeta}</span></div>
          <div className="panel-body">
          <div className="trace-block">
            <div className="trace-row"><span className="label">{d.backend}</span><span className="value">{d.connected}</span></div>
            <div className="trace-row"><span className="label">{d.auditEvents7d}</span><span className="value">{data.recent_audit_events}</span></div>
            <div className="trace-row"><span className="label">{d.users}</span><span className="value">{data.total_users}</span></div>
          </div>
          </div>
          <div className="panel-footer">{d.readinessFooter}</div>
        </section>
      </div>
    </div>
  )
}
