# SpotWeldPro AI v3.0.0-alpha.4
## Pre-Transfer Engineering Baseline

**Release date:** 2026-10-13
**Release type:** GitHub Prerelease · Alpha
**Tag:** `v3.0.0-alpha.4`
**Commit:** `aff2e8dffe2849eff5627403434d33127ac16b71`
**Branch:** `main` @ `Bursa-16/SpotWeldPro-AI`

---

## Overview

This release establishes a complete, verified engineering baseline for SpotWeldPro AI
before the repository is transferred to the dedicated SpotWeldPro-AI GitHub account for
private customer demo deployment.

It resolves the GATE_12_R4 blocker, delivers the full customer demo UX with TR/EN
internationalization, completes the organization and reference profile foundation,
and passes all GATE-12 acceptance verification gates.

**82 commits** since the previous valid SpotWeld release (`v3.0.0-alpha.3`, 2026-09-05).

---

## Critical Fix

### BLOCKER: material_family KeyError → HTTP 500 (GATE_12_R4)

**Symptom:** Any non-Turkish `material_family` value (e.g. `"Steel"`, `"Mild Steel"`)
caused `engine.py` to raise `KeyError` on `MATERIAL_FAMILIES[fam]`, returning
HTTP 500 to the caller.

**Root cause:** Bare dict lookup `fam = i["material_family"]` followed immediately
by `MATERIAL_FAMILIES[fam]["status"]` — no normalization or validation.

**Fix:**
- Added `resolve_material_family(value: str) → str` in `backend/app/domain/materials.py`
- 26-entry `_MATERIAL_FAMILY_ALIASES` dict for unambiguous English → Turkish mapping
- Added Pydantic `@field_validator("material_family", mode="before")` in
  `backend/app/schemas/analysis.py` — returns HTTP 422 for unknown values
- Updated `engine.py` call site to use `resolve_material_family()`

**Verification:** GATE_12_R5B live HTTP — 19/19 PASS at `127.0.0.1:8001`.
`"Steel"` → 422 (was 500). `"Mild Steel"` → 200 (score=100.0, nugget=5.2/6.7).

---

## New Engineering Capabilities

### Customer Demo UX (TR/EN)
- Full authenticated engineering application: Weld Analysis, Engineering Workstation,
  Failure Probability Analysis pages
- Public product pages: Landing, Features, How It Works, Packages, Demo, Login
- TR/EN language switching throughout (`appContent.ts` ~1153 lines, `publicContent.ts`)
- Visual weld inspector component
- Electrode guide modal

### Organization and Reference Profile Foundation (Phase 1)
- `Organization` and `ReferenceProfile` models (Alembic `0015_organization_and_profile_tables`)
- `REF_PROFILE_MS_2T_50HZ_V1` — mild steel 2T 50Hz reference profile
- Band selection and parameter guidance (`get_effective_thickness`, `get_parameter_band`)
- Phase 1 organization model: 12 tests PASS

### Authentication Improvements
- Username-based login (replacing email-based; Alembic `0014_auth_ux03_username`)
- Structured error contract: `GovernedAPIError` response schema on all auth errors
- `HOSTED_DEMO=true` mode: startup rejects known placeholder JWT secrets and secrets <32 chars
- `DISABLE_DOCS=true`: hides `/docs`, `/redoc`, `/openapi.json`
- Complete auth error regression coverage (structured 401/422/409 responses)

### Failure Probability Analysis
- `POST /api/v1/failure-probability` endpoint
- 10 failure modes with `probability_percent`, `severity`, `priority_actions`
- Response schema uses `failure_modes[]` array
- TR/EN failure mode labels via i18n

### Rate Limiting
- In-process sliding-window rate limiter: 60 req/IP/60 s on public weld-analysis endpoint
- `_MAX_TRACKED_IPS = 10,000` memory cap
- Thread-safe implementation

### Engineering Library Foundation
- Governed engineering library services and persistence API (backend, PostgreSQL)
- Electrode, weld gun, and weld schedule persistence models

---

## Engineering Validation Results (GATE_12_R4/R5)

| Test Case | Input | Result | Status |
|-----------|-------|--------|--------|
| TC1 Coating | Galvanized vs uncoated | score=85 vs 100; coating risk flagged | PASS |
| TC2 2T analysis | Mild Steel, 1.5+1.5mm, 8.5kA/12cyc | score=100, risk=LOW, nugget=5.2/6.7mm | PASS |
| TC3 3T analysis | Mild Steel, 3T stack | score=75, risk=MEDIUM, 3T penalty | PASS |
| TC4 Weld lobe | Mild Steel, 2T | 77 points; optimum=6.5kA/12cyc; current-dominant | PASS |
| TC6 Weld quality | Nominal params | 4 checks all `Uygun` | PASS |
| TC7 Failure probability | Mild Steel, LOW score | 10 modes, 1.3–17.8% | PASS |
| TC8 Consistency | LOW quality ↔ LOW severity | Directionally consistent | PASS |
| R5B C1 | `"Steel"` | 422 (was 500 KeyError) | PASS |
| R5B C2 | `"Mild Steel"` | 200, score=100.0 | PASS |
| R5B C6–C12 | All 7 Turkish canonical keys | 200 | PASS |
| R5B C13–C15 | TR/EN equivalence | score/nugget identical | PASS |

Live container verification: **19/19 PASS** at `127.0.0.1:8001`.

---

## Test Summary

| Suite | Count | Result |
|-------|-------|--------|
| Material family validation | 30 tests | 30/30 PASS |
| Focused regression (test_api, test_gate07/08, test_phase1_org, test_reference_profile) | 146 tests | 144 PASS, 2 pre-existing FAIL |
| Frontend build (tsc -b + vite) | 114 modules | PASS |
| `git diff --check` | — | PASS (0 whitespace errors) |

**Pre-existing failures (not introduced by this release):**
- `test_H_4T_requires_engineering_review` — `get_effective_thickness("4T", …)` raises `ValueError` instead of returning `ENGINEERING_REVIEW_REQUIRED`. Function is in `reference_profile.py`, unmodified by this release. Does not affect demo path.
- `test_H_4T_no_t_min_fallback` — same function, same boundary issue.

These failures existed in `v3.0.0-alpha.3`. First confirmed in GATE_12_R4 (2026-10-13).

---

## Migration Requirements

Alembic head: `0016_merge_heads` (merge point).

Fresh deployment requires:
```bash
alembic upgrade head
```

The Compose `command` runs migrations automatically at container startup:
```yaml
command: sh -c "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"
```

Migration chain verified through `0016_merge_heads` in GATE_12_R4.

---

## Breaking Changes

| Change | Impact |
|--------|--------|
| `material_family` validation now strict | Values not in 7 Turkish canonical families or 26 EN aliases → HTTP 422 (was HTTP 500 on unknown, or silent wrong result on partial match) |
| Auth changed to username-based | API clients using email login must switch to username |
| `validate_stack` rejects 4T | 4T stack-count now returns HTTP 422 (was HTTP 500 via domain ValueError leaking through) |
| `failure_modes[]` array schema | Failure probability response uses `failure_modes[]`, not top-level `failure_probability` field |

---

## Security Notes

- `.env` and all `.env.*` files are gitignored.
- `.env.example` contains only empty placeholder values. No real credentials.
- `HOSTED_DEMO=true` must be set before any internet-accessible deployment.
- `JWT_SECRET_KEY` must be ≥32 chars and not a known placeholder.
- HTTPS termination and scoped `CORS_ORIGINS` required before external customer access.
- Demo account password must be strong (not reused from local development).

---

## Known Limitations

| Area | Status |
|------|--------|
| Weld-lobe zone i18n | Zone labels ("Güvenli", "Yetersiz Füzyon") hardcoded in Turkish in engine |
| Ultrasonic validation | No API endpoint; UI guidance text only |
| material_family UI | Free-text input; `<select>` dropdown planned |
| Surrogate model accuracy | v0.9; field calibration with independent reference data required |
| Rate limiter scope | In-process only; multiplies per uvicorn worker in multi-worker deployment |
| Canonical repo visibility | `Bursa-16/SpotWeldPro-AI` is public — source visible to anyone |
| Governed backend | Functional; not declared production-enabled in this alpha |

---

## Deployment Readiness

| Check | Status |
|-------|--------|
| Local private demo | READY (127.0.0.1:8001, GATE_12_R5B verified) |
| Cloud/hosted demo | REQUIRES: HTTPS, HOSTED_DEMO=true, strong secrets, scoped CORS |
| Demo repo creation | PENDING (SpotWeldPro-AI/SpotWeldPro-AI — not yet created) |
| Production deployment | NOT READY (alpha; surrogate model uncalibrated; governed backend not enabled) |

---

## Classification

```
RELEASE_TYPE:           Alpha / Pre-release
STATUS:                 ENGINEERING DEVELOPMENT BASELINE
NOT PRODUCTION CERTIFIED
NOT FULLY EXPERIMENTALLY VALIDATED
CUSTOMER DEMO READINESS: CONDITIONAL — local demo PASS; cloud deployment requires separate gates
SURROGATE MODEL:        v0.9 — field calibration required
```

---

## Files Changed in This Release

**Since `v3.0.0-alpha.3` (`171bbd04`):** 134 files, 82 commits.

Key source files:
- `backend/app/domain/materials.py` — `resolve_material_family()`, `_MATERIAL_FAMILY_ALIASES`
- `backend/app/domain/engine.py` — `resolve_material_family()` call site
- `backend/app/schemas/analysis.py` — `field_validator` for `material_family`
- `backend/tests/test_material_family_validation.py` — 30 regression tests (new)
- `backend/app/domain/reference_profile.py` — `REF_PROFILE_MS_2T_50HZ_V1`, band system
- `frontend/src/i18n/appContent.ts` — complete TR/EN authenticated app content
- `frontend/src/i18n/publicContent.ts` — TR/EN public page content
- `frontend/src/pages/` — AnalysisPage, EngineeringPage, FailureProbabilityPage, …
- `backend/alembic/versions/0015_organization_and_profile_tables.py`
- `backend/alembic/versions/0016_merge_heads.py`
