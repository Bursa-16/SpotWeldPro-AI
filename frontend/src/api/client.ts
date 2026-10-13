import axios, { isAxiosError } from 'axios'
import type { WeldAnalysisRequest, WeldAnalysisResponse } from '../types/weld'
import type { Project, ProjectCreate, WeldPoint, WeldPointCreate } from '../types/project'

export type BackendApiErrorCode =
  | 'INVALID_TOKEN'
  | 'INACTIVE_USER'
  | 'PERMISSION_DENIED'
  | 'RESOURCE_NOT_FOUND'
  | 'INVALID_REQUEST'
  | 'IDEMPOTENCY_CONFLICT'
  | 'IDEMPOTENCY_IN_PROGRESS'
  | 'GOVERNED_TRANSACTION_FAILED'
  | 'MISSING_IDEMPOTENCY_KEY'
  | 'INTERNAL_ERROR'
  | 'VALIDATION_ERROR'
  | 'INVALID_CREDENTIALS'
  | 'USERNAME_ALREADY_EXISTS'
  | 'MACHINE_READINESS_REVISION_NOT_FOUND'
  | 'LIBRARY_RESOURCE_NOT_FOUND'
  | 'INVALID_REFRESH_TOKEN'
  | 'INVALID_ROLE'
  | 'EMAIL_ALREADY_EXISTS'
  | 'NO_ACTIVE_REVISION'
  | 'AMBIGUOUS_CURRENT_REVISION'
  | 'RESOURCE_CONFLICT'
  | 'LIBRARY_CONFLICT'

export type FrontendErrorCode = BackendApiErrorCode | 'NETWORK_ERROR' | 'UNKNOWN_ERROR'

export function extractErrorCode(err: unknown): FrontendErrorCode {
  if (isAxiosError(err)) {
    const data = err.response?.data
    if (data && typeof data === 'object' && 'error_code' in data && typeof data.error_code === 'string') {
      return data.error_code as BackendApiErrorCode
    }
    if (!err.response) {
      return 'NETWORK_ERROR'
    }
  }
  return 'UNKNOWN_ERROR'
}

// AUTH-UX-04-R3A: verified from backend/app/schemas/auth.py — all fields required, non-optional
export interface UserResponse {
  id: number
  username: string
  email: string
  full_name: string   // min_length=2 at creation — always non-empty
  role: string
  is_active: boolean
}

// AUTH-UX-04-R3A: /auth/me error classification by HTTP status (not extractErrorCode)
// unauthorized → 401: invalid/expired token — clear auth and redirect /login
// retryable    → no response (network/CORS/timeout) or 500/502/503 — tokens preserved
// error        → 403, 422, other — tokens preserved, show safe error
export type MeErrorKind = 'unauthorized' | 'retryable' | 'error'

export function classifyMeError(err: unknown): MeErrorKind {
  if (!isAxiosError(err)) return 'retryable'
  const status = err.response?.status
  if (status === 401) return 'unauthorized'
  if (err.response === undefined) return 'retryable'
  if (status === 500 || status === 502 || status === 503) return 'retryable'
  return 'error'
}

// AUTH-UX-04-R3: targeted removal — never use localStorage.clear()
const AUTH_KEYS = ['access_token', 'refresh_token'] as const
export function clearAuthStorage() {
  AUTH_KEYS.forEach((k) => localStorage.removeItem(k))
}

const client = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api/v1',
  timeout: 15000,
})

client.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// AUTH-UX-04-R3A: 401 interceptor — exact pathname matching, duplicate-redirect guard
function getRequestPath(url: string | undefined): string {
  if (!url) return ''
  let path: string
  try {
    path = new URL(url, 'http://x').pathname
  } catch {
    path = url.split('?')[0].split('#')[0]
  }
  return path.replace(/^\/api\/v1/, '')
}

const INTERCEPTOR_EXCLUDED = new Set(['/auth/login', '/auth/me'])
let redirecting401 = false

client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (
      isAxiosError(error) &&
      error.response?.status === 401 &&
      !redirecting401 &&
      !INTERCEPTOR_EXCLUDED.has(getRequestPath(error.config?.url))
    ) {
      redirecting401 = true
      clearAuthStorage()
      window.location.replace('/login')
    }
    return Promise.reject(error)
  }
)

// AUTH-UX-03: login authenticates by username (not email).
// JWT subject (sub) remains user.email internally — see AUTH-UX-03B.
export async function login(username: string, password: string) {
  const response = await client.post('/auth/login', { username, password })
  localStorage.setItem('access_token', response.data.access_token)
  localStorage.setItem('refresh_token', response.data.refresh_token)
  return response.data
}
export function logout() { clearAuthStorage() }
export async function currentUser(): Promise<UserResponse> {
  return (await client.get<UserResponse>('/auth/me')).data
}
export async function dashboard() { return (await client.get('/dashboard')).data }
export async function analyzeWeld(payload: WeldAnalysisRequest): Promise<WeldAnalysisResponse> {
  return (await client.post<WeldAnalysisResponse>('/weld-analysis', payload)).data
}
export async function listProjects(): Promise<Project[]> { return (await client.get<Project[]>('/projects')).data }
export async function createProject(payload: ProjectCreate): Promise<Project> { return (await client.post<Project>('/projects', payload)).data }
export async function listWeldPoints(projectId: number): Promise<WeldPoint[]> { return (await client.get<WeldPoint[]>(`/projects/${projectId}/weld-points`)).data }
export async function createWeldPoint(projectId: number, payload: WeldPointCreate): Promise<WeldPoint> {
  return (await client.post<WeldPoint>(`/projects/${projectId}/weld-points`, payload)).data
}
export default client
