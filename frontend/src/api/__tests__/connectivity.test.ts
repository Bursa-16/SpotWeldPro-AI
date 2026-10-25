/**
 * BACKEND-RELIABILITY-FIX-01 — connectivity tests
 *
 * Tests for:
 * - extractErrorCode  : timeout / network / server / credentials classification
 * - pingBackend       : delayed startup recovery, retry-then-ok, exhausted retries
 * - publicContent     : TR/EN login i18n keys exist and are non-empty strings
 */
import { describe, it, expect, vi } from 'vitest'
import axios from 'axios'
import { extractErrorCode, pingBackend } from '../client'
import { PUBLIC_CONTENT } from '../../i18n/publicContent'

// Instant delays — avoids real setTimeout waits in tests (6 entries for maxAttempts=6)
const NO_DELAY = [0, 0, 0, 0, 0, 0] as const

// ── helpers ────────────────────────────────────────────────────────────────

function makeAxiosError(code?: string, status?: number, errorCode?: string) {
  const err = new axios.AxiosError('test', code)
  if (status !== undefined) {
    err.response = {
      status,
      data: errorCode ? { error_code: errorCode, message: 'test' } : {},
      headers: {},
      config: { headers: new axios.AxiosHeaders() },
      statusText: '',
    }
  }
  return err
}

// ── extractErrorCode ────────────────────────────────────────────────────────

describe('extractErrorCode', () => {
  it('returns TIMEOUT_ERROR for ECONNABORTED (axios timeout)', () => {
    expect(extractErrorCode(makeAxiosError('ECONNABORTED'))).toBe('TIMEOUT_ERROR')
  })

  it('returns TIMEOUT_ERROR for ERR_CANCELED', () => {
    expect(extractErrorCode(makeAxiosError('ERR_CANCELED'))).toBe('TIMEOUT_ERROR')
  })

  it('returns NETWORK_ERROR when no response and no timeout code', () => {
    expect(extractErrorCode(makeAxiosError('ECONNREFUSED'))).toBe('NETWORK_ERROR')
  })

  it('returns NETWORK_ERROR when code is undefined and no response', () => {
    expect(extractErrorCode(makeAxiosError(undefined))).toBe('NETWORK_ERROR')
  })

  it('returns SERVER_ERROR for HTTP 500', () => {
    expect(extractErrorCode(makeAxiosError('ERR_BAD_RESPONSE', 500))).toBe('SERVER_ERROR')
  })

  it('returns SERVER_ERROR for HTTP 503', () => {
    expect(extractErrorCode(makeAxiosError('ERR_BAD_RESPONSE', 503))).toBe('SERVER_ERROR')
  })

  it('returns the backend error_code for structured 401', () => {
    expect(extractErrorCode(makeAxiosError('ERR_BAD_RESPONSE', 401, 'INVALID_CREDENTIALS')))
      .toBe('INVALID_CREDENTIALS')
  })

  it('returns UNKNOWN_ERROR for non-axios errors', () => {
    expect(extractErrorCode(new Error('something'))).toBe('UNKNOWN_ERROR')
    expect(extractErrorCode('string error')).toBe('UNKNOWN_ERROR')
    expect(extractErrorCode(null)).toBe('UNKNOWN_ERROR')
  })
})

// ── pingBackend ─────────────────────────────────────────────────────────────

describe('pingBackend', () => {
  it('returns ok when health responds on first attempt', async () => {
    const fetch = vi.fn().mockResolvedValue({ status: 200, data: { status: 'ok' } })
    const result = await pingBackend(4, undefined, fetch, NO_DELAY)
    expect(result).toBe('ok')
    expect(fetch).toHaveBeenCalledTimes(1)
    expect(fetch).toHaveBeenCalledWith('/health')
  })

  it('retries on connection-refused and returns ok when backend starts', async () => {
    const fetch = vi.fn()
      .mockRejectedValueOnce(makeAxiosError('ECONNREFUSED'))
      .mockRejectedValueOnce(makeAxiosError('ECONNREFUSED'))
      .mockResolvedValueOnce({ status: 200 })
    const onRetry = vi.fn()
    const result = await pingBackend(4, onRetry, fetch, NO_DELAY)
    expect(result).toBe('ok')
    expect(fetch).toHaveBeenCalledTimes(3)
    expect(onRetry).toHaveBeenCalledTimes(2)
    expect(onRetry).toHaveBeenNthCalledWith(1, 1)
    expect(onRetry).toHaveBeenNthCalledWith(2, 2)
  })

  it('returns ok immediately if backend is up after cold start on attempt 4', async () => {
    const fetch = vi.fn()
      .mockRejectedValueOnce(makeAxiosError('ECONNREFUSED'))
      .mockRejectedValueOnce(makeAxiosError('ECONNREFUSED'))
      .mockRejectedValueOnce(makeAxiosError('ECONNREFUSED'))
      .mockResolvedValueOnce({ status: 200 })
    const result = await pingBackend(4, undefined, fetch, NO_DELAY)
    expect(result).toBe('ok')
    expect(fetch).toHaveBeenCalledTimes(4)
  })

  it('returns timeout when all attempts exhaust with ECONNABORTED', async () => {
    const fetch = vi.fn().mockRejectedValue(makeAxiosError('ECONNABORTED'))
    const result = await pingBackend(3, undefined, fetch, NO_DELAY)
    expect(result).toBe('timeout')
    expect(fetch).toHaveBeenCalledTimes(3)
  })

  it('returns network when all attempts exhaust with connection-refused', async () => {
    const fetch = vi.fn().mockRejectedValue(makeAxiosError('ECONNREFUSED'))
    const result = await pingBackend(3, undefined, fetch, NO_DELAY)
    expect(result).toBe('network')
  })

  it('returns server when health responds with 500', async () => {
    const fetch = vi.fn().mockRejectedValue(makeAxiosError('ERR_BAD_RESPONSE', 500))
    const result = await pingBackend(1, undefined, fetch, NO_DELAY)
    expect(result).toBe('server')
  })

  it('returns ok (service reachable) when health responds with any 4xx', async () => {
    // A 4xx on /health is unusual but proves TCP+HTTP is working
    const fetch = vi.fn().mockRejectedValue(makeAxiosError('ERR_BAD_RESPONSE', 403))
    const result = await pingBackend(1, undefined, fetch, NO_DELAY)
    expect(result).toBe('ok')
  })

  it('does not retry beyond maxAttempts', async () => {
    const fetch = vi.fn().mockRejectedValue(makeAxiosError('ECONNREFUSED'))
    await pingBackend(2, undefined, fetch, NO_DELAY)
    expect(fetch).toHaveBeenCalledTimes(2)
  })
})

// ── pingBackend — extended cold-start coverage (FIX-F) ─────────────────────

describe('pingBackend — 90 s cold-start coverage', () => {
  it('defaults to 6 attempts', async () => {
    const fetch = vi.fn().mockRejectedValue(makeAxiosError('ECONNREFUSED'))
    await pingBackend(undefined, undefined, fetch, NO_DELAY)
    expect(fetch).toHaveBeenCalledTimes(6)
  })

  it('returns ok when backend wakes on attempt 6', async () => {
    const fetch = vi.fn()
      .mockRejectedValueOnce(makeAxiosError('ECONNREFUSED'))
      .mockRejectedValueOnce(makeAxiosError('ECONNREFUSED'))
      .mockRejectedValueOnce(makeAxiosError('ECONNREFUSED'))
      .mockRejectedValueOnce(makeAxiosError('ECONNREFUSED'))
      .mockRejectedValueOnce(makeAxiosError('ECONNREFUSED'))
      .mockResolvedValueOnce({ status: 200 })
    const result = await pingBackend(6, undefined, fetch, NO_DELAY)
    expect(result).toBe('ok')
    expect(fetch).toHaveBeenCalledTimes(6)
  })

  it('returns network when all 6 attempts fail', async () => {
    const fetch = vi.fn().mockRejectedValue(makeAxiosError('ECONNREFUSED'))
    const result = await pingBackend(6, undefined, fetch, NO_DELAY)
    expect(result).toBe('network')
    expect(fetch).toHaveBeenCalledTimes(6)
  })

  it('returns timeout when all 6 attempts exhaust with ECONNABORTED', async () => {
    const fetch = vi.fn().mockRejectedValue(makeAxiosError('ECONNABORTED'))
    const result = await pingBackend(6, undefined, fetch, NO_DELAY)
    expect(result).toBe('timeout')
    expect(fetch).toHaveBeenCalledTimes(6)
  })
})

// ── pingBackend — AbortSignal cancellation (FIX-F) ─────────────────────────

describe('pingBackend — AbortSignal', () => {
  it('returns immediately without calling fetch when signal is already aborted', async () => {
    const ctrl = new AbortController()
    ctrl.abort()
    const fetch = vi.fn().mockResolvedValue({ status: 200 })
    const result = await pingBackend(4, undefined, fetch, NO_DELAY, ctrl.signal)
    expect(result).toBe('network')
    expect(fetch).not.toHaveBeenCalled()
  })

  it('stops retrying after first failed fetch when signal is aborted inside fetch', async () => {
    const ctrl = new AbortController()
    const fetch = vi.fn().mockImplementationOnce(() => {
      ctrl.abort()
      return Promise.reject(makeAxiosError('ECONNREFUSED'))
    })
    const result = await pingBackend(4, undefined, fetch, NO_DELAY, ctrl.signal)
    expect(fetch).toHaveBeenCalledTimes(1)
    expect(result).toBe('network')
  })

  it('does not invoke onRetry after signal is aborted', async () => {
    const ctrl = new AbortController()
    const fetch = vi.fn().mockImplementation(() => {
      ctrl.abort()
      return Promise.reject(makeAxiosError('ECONNREFUSED'))
    })
    const onRetry = vi.fn()
    await pingBackend(4, onRetry, fetch, NO_DELAY, ctrl.signal)
    expect(onRetry).not.toHaveBeenCalled()
  })

  it('returns ok normally when signal is provided but never aborted', async () => {
    const ctrl = new AbortController()
    const fetch = vi.fn().mockResolvedValue({ status: 200 })
    const result = await pingBackend(4, undefined, fetch, NO_DELAY, ctrl.signal)
    expect(result).toBe('ok')
    expect(fetch).toHaveBeenCalledTimes(1)
  })
})

// ── i18n strings ────────────────────────────────────────────────────────────

describe('login i18n — TR and EN', () => {
  const keys: Array<keyof typeof PUBLIC_CONTENT['tr']['login']> = [
    'connecting', 'retrying', 'errorNetwork', 'errorTimeout', 'errorServer', 'errorCredentials',
  ]

  for (const lang of ['tr', 'en'] as const) {
    describe(`[${lang}]`, () => {
      for (const key of keys) {
        it(`${key} is a non-empty string`, () => {
          const value = PUBLIC_CONTENT[lang].login[key]
          expect(typeof value).toBe('string')
          expect((value as string).length).toBeGreaterThan(0)
        })
      }

      it('connecting is distinct from submitBusy', () => {
        expect(PUBLIC_CONTENT[lang].login.connecting)
          .not.toBe(PUBLIC_CONTENT[lang].login.submitBusy)
      })

      it('errorTimeout is distinct from errorNetwork', () => {
        expect(PUBLIC_CONTENT[lang].login.errorTimeout)
          .not.toBe(PUBLIC_CONTENT[lang].login.errorNetwork)
      })
    })
  }

  it('TR connecting message references server (Sunucuya)', () => {
    expect(PUBLIC_CONTENT.tr.login.connecting).toContain('Sunucu')
  })

  it('TR errorTimeout mentions startup context', () => {
    expect(PUBLIC_CONTENT.tr.login.errorTimeout).toContain('başlatıl')
  })

  it('EN connecting message references server', () => {
    expect(PUBLIC_CONTENT.en.login.connecting.toLowerCase()).toContain('server')
  })

  it('EN errorTimeout mentions startup context', () => {
    expect(PUBLIC_CONTENT.en.login.errorTimeout.toLowerCase()).toContain('start')
  })
})
