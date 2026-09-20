import { FormEvent, useEffect, useState } from 'react'
import { createProject, listProjects } from '../api/client'
import type { Project } from '../types/project'

export function ProjectsPage({ onOpen }: { onOpen: (project: Project) => void }) {
  const [projects, setProjects] = useState<Project[]>([])
  const [code, setCode] = useState('')
  const [name, setName] = useState('')
  const [customer, setCustomer] = useState('')
  const [platform, setPlatform] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  async function refresh() {
    try { setProjects(await listProjects()) }
    catch { setError('Backend connection unavailable. Engineering data could not be loaded. Verify the API service and retry.') }
  }

  useEffect(() => {
    refresh()
  }, [])

  async function submit(e: FormEvent) {
    e.preventDefault()
    setError('')
    setBusy(true)
    try {
      await createProject({ project_code: code, project_name: name, customer, vehicle_platform: platform })
      setCode('')
      setName('')
      setCustomer('')
      setPlatform('')
      await refresh()
    } catch {
      setError('Backend connection unavailable. Engineering data could not be saved. Verify the API service and retry.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="page active">
      <div className="ws-kicker">Production · Spot Welding Parametre Analysis</div>
      <header className="page-header">
        <div>
          <h1>Projects &amp; Weld Points</h1>
          <p className="subtitle">Project registry and weld-point definitions</p>
        </div>
      </header>

      {error && (
        <div className="alert danger" role="alert">
          <div>
            <div className="alert-title">Backend connection unavailable</div>
            <div className="alert-text">Engineering data could not be loaded. Verify the API service and retry.</div>
          </div>
        </div>
      )}

      <div className="ws-grid-main">
        <form className="panel" onSubmit={submit} aria-label="New project">
          <div className="panel-header">
            <h3>New project record</h3>
            <span className="panel-meta">project context</span>
          </div>
          <div className="panel-body">
          <div className="ws-zone-label">Project identity</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-3)' }}>
            <div className="field">
              <label htmlFor="proj-code">Proje Kodu</label>
              <input id="proj-code" value={code} onChange={(e) => setCode(e.target.value)} placeholder="ör. PRJ-2026-A" required />
            </div>
            <div className="field">
              <label htmlFor="proj-name">Proje Adı</label>
              <input id="proj-name" value={name} onChange={(e) => setName(e.target.value)} placeholder="ör. Gövde Yan Panel Kaynak Hattı" required />
            </div>
            <div className="field">
              <label htmlFor="proj-cust">Müşteri</label>
              <input id="proj-cust" value={customer} onChange={(e) => setCustomer(e.target.value)} placeholder="ör. OEM Automotive" />
            </div>
            <div className="field">
              <label htmlFor="proj-plat">Araç / Platform</label>
              <input id="proj-plat" value={platform} onChange={(e) => setPlatform(e.target.value)} placeholder="ör. EV-Platform-C" />
            </div>
            <button className="btn btn-primary" type="submit" disabled={busy}>
              {busy ? 'Kaydediliyor…' : 'Projeyi Kaydet'}
            </button>
          </div>
          </div>
          <div className="panel-footer">Creates a governed project record via backend API.</div>
        </form>

        <section className="panel" aria-label="Registered projects">
          <div className="panel-header">
            <h3>Registered projects</h3>
            <span className="panel-meta">{projects.length} project(s)</span>
          </div>
          <div className="panel-body">
          <div className="ws-zone-label">Project list · select to manage weld points</div>
          {projects.length === 0 ? (
            <div className="ws-empty" role="status">
              <span className="empty-glyph" aria-hidden="true">PJ</span>
              <strong>No project context selected</strong>
              <span className="ws-empty-hint">No projects are registered yet. Create the first project record using the adjacent form.</span>
              <span className="empty-action">Next action: create a project record.</span>
            </div>
          ) : (
            <div className="grid-2">
              {projects.map((p) => (
                <article
                  key={p.id}
                  className="metric-card"
                  style={{ cursor: 'pointer', transition: 'border-color 0.15s' }}
                  onClick={() => onOpen(p)}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span className="mono" style={{ fontSize: 'var(--fs-xs)', color: 'var(--accent)' }}>
                      {p.project_code}
                    </span>
                    <span className="badge ok">{p.status}</span>
                  </div>
                  <strong className="metric-value" style={{ fontSize: 'var(--fs-h4)', marginTop: 'var(--sp-1)' }}>
                    {p.project_name}
                  </strong>
                  <span className="metric-sub">{p.customer || 'No customer specified'}</span>
                </article>
              ))}
            </div>
          )}
          </div>
          <div className="panel-footer">Only backend-registered fields are shown.</div>
        </section>
      </div>
    </div>
  )
}

