# Changelog

All notable changes to SpotWeldPro AI are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [3.0.0-alpha.4] - 2026-10-13

**Pre-Transfer Engineering Baseline**

Establishes the complete engineering baseline before repository transfer to the
dedicated SpotWeldPro-AI account. Includes the full customer demo UX, material
family normalization hotfix, TR/EN internationalization, organization/profile
foundation, GATE-12 acceptance verification, and governed backend improvements.

### Fixed
- **BLOCKER (GATE_12_R4):** `MATERIAL_FAMILIES[key]` bare dict lookup in
  `engine.py` raised `KeyError` → HTTP 500 for any non-Turkish `material_family`
  value. Now returns HTTP 422 with `UNSUPPORTED_MATERIAL_FAMILY` detail.

### Added
- `resolve_material_family()` in `materials.py`: canonical Turkish key lookup
  + 26 unambiguous English aliases (case-insensitive, whitespace-stripped).
- Pydantic `@field_validator("material_family", mode="before")` in
  `WeldAnalysisRequest` schema — validation at API boundary.
- `_MATERIAL_FAMILY_ALIASES` dict covering all 7 families (Mild Steel, AHSS,
  Galvanized Steel, Stainless Steel, Aluminum Alloys, Superalloy, Mixed/Dissimilar).
- 30 regression tests in `test_material_family_validation.py` covering TR
  canonical keys, EN aliases, TR/EN numerical equivalence, ambiguous/unknown/empty
  inputs — all pass.
- Full customer demo UX (TR/EN): Weld Analysis, Engineering, Failure Probability,
  public product pages (Landing, Features, How It Works, Packages, Demo, Login).
- Organization and reference profile foundation (Phase 1).
- 2T reference parameter guidance (REF_PROFILE_MS_2T_50HZ_V1).
- Username-based authentication (replacing email-based login).
- Canonical error contract (structured `GovernedAPIError` response schema).
- Visual weld inspector component.
- Demo account hardening: `HOSTED_DEMO=true` enforces JWT secret strength at
  startup; `DISABLE_DOCS=true` hides API documentation.
- Rate limiter: 60 req/IP/60 s sliding-window on public weld-analysis endpoint.
- Failure probability endpoint: 10 failure modes with `failure_modes[]` array.
- `seed_demo_user.py`: idempotent READ_ONLY demo account seeding from env var.

### Changed
- `engine.py` line 27: `fam=i["material_family"]` → `fam=resolve_material_family(i["material_family"])`.
- `schemas/analysis.py`: added `field_validator` + `resolve_material_family` import.
- `WeldAnalysisRequest.validate_stack`: 4T stack-up now raises 422 (was 500).
- CORS configuration: `CORS_ORIGINS` env var; dev default includes 5173/5174 ports.
- Alembic head: `0016_merge_heads` (merge point for 0015_organization_and_profile
  and 0012_electrode_weldgun branches).

### Security
- PBKDF2-SHA256 password hashing (240,000 iterations).
- HMAC-HS256 JWT token implementation.
- Known-placeholder JWT secret rejection under `HOSTED_DEMO=true`.
- No real credentials in `.env.example` (empty placeholder values only).

### Validation (GATE_12_R4/R5)
- TC1 Coated material: score=85 vs uncoated=100; coating risk flagged. PASS.
- TC2 2T analysis: score=100, risk=LOW, nugget_min=5.2 mm, nugget_opt=6.7 mm. PASS.
- TC3 3T analysis: score=75, risk=MEDIUM, 3T penalty applied. PASS.
- TC4 Weld lobe: 77 points; sensitivity current-dominant. PASS.
- TC6 Weld quality: 4 checks all `Uygun`. PASS.
- TC7 Failure probability: 10 modes, 1.3–17.8%. PASS.
- R5B live HTTP: 19/19 checks PASS at 127.0.0.1:8001.
- Material family regression: 30/30 PASS.
- Frontend build (tsc + vite): PASS.

### Known Limitations
- Weld-lobe zone labels hardcoded in Turkish ("Güvenli", "Yetersiz Füzyon").
- `material_family` remains free-text input in `StackDefinitionPanel.tsx`.
- Surrogate model v0.9 requires field calibration.
- Ultrasonic validation: no API endpoint (UI guidance text only).
- Rate limiter is in-process only (single-worker safe).
- 2 pre-existing test failures: `test_H_4T_*` (4T scope, unrelated to demo path).

### Classification
Alpha / pre-release. Not production deployment approval.
Not production certification. Not ISO/AWS/OEM approved.

---

## [3.0.0-alpha.3] - 2026-09-05

PostgreSQL E2E governance validation milestone.

### Added
- Phase 6A1: real-PostgreSQL CI/test foundation for governed E2E.
- Phase 6A2: governed PostgreSQL happy-path E2E (identity → DWP chain).
- Phase 6A2: canonical-scope repair for lifecycle audit metadata.
- Phase 6A3: lifecycle negative-path E2E coverage
  (`SEPARATION_OF_DUTIES_VIOLATION`, `MISSING_SCOPE_SNAPSHOT`, `UNRESOLVED_BASIS`).
- Phase 6A4: evidence-verification negative-path E2E coverage (10 denial codes +
  idempotency `CONFLICT` coverage).
- Phase 6A5: governed historical staleness E2E coverage.
- Governed active rule revision supersession.
- Governed current revision resolution.

### Validation
- Phase 6A2: full PostgreSQL happy-path E2E passes end-to-end (identity → DWP).
- Phase 6A3: 5 lifecycle denial-path assertions pass under real PostgreSQL.
- Phase 6A4: 10 evidence-verification denial-path assertions + 1 idempotency CONFLICT pass.
- CI: PostgreSQL E2E runs on every push.

### Classification
Alpha / pre-release. No engineering threshold values introduced.
No new production enablement.

---

## [3.0.0-alpha.2] - 2026-09-01

Governed API integration.

### Added
- Governed Evidence Verification API.
- Governed Engineering Rule Registry lifecycle API.
- Governed Rule Evaluation API (MIN/MAX/RANGE/EQUALS).
- Governed Machine Readiness API (READY/NOT_READY/ENGINEERING_REVIEW_REQUIRED).
- Governed Digital Weld Passport Draft and Lifecycle API.

### Validation
- Full backend regression suite: 361 passed.

### Classification
Alpha / pre-release.

---

## [3.0.0-alpha.1] - 2026-08-28

Governed engineering foundation.

### Added
- Governed Engineering Rule Registry (DRAFT → SOURCE_BACKED → ENABLED → ACTIVE).
- Evidence Verification Authority (human-only, separation of duties).
- Governed applicability resolution (deterministic, fail-closed).
- Machine Readiness Check foundation.
- Digital Weld Passport foundation.

### Classification
Alpha / pre-release.

---

## [1.3.0] - 2026-07-17

- Fixed frontend TypeScript build and API contract drift.
- Stabilized Windows SQLite test teardown.
- Removed fallback JWT secret and default admin bootstrap.
- Enforced Alembic-first container startup.
- CI now requires backend tests and frontend build.

---

## [1.2.0] - 2026-07-16

- GitHub-ready repository structure.
- Architecture, requirements, engineering, API, database, security, testing,
  deployment and roadmap documentation.
- GitHub issue templates and pull-request template.
- CI workflow for backend tests and frontend build.
- Product scope clarified: parameter analysis only (not image processing).

---

## [1.1.0]

- Parameter-based potential failure probability engine.
- Ten potential failure modes with probability, confidence, severity,
  contributors, validation tests, and recommended actions.
- 17 automated backend tests.

---

## [1.0.0]

- FastAPI + React professional architecture.
- Model-4, DOE optimization, ensemble prediction, weld-lobe support,
  authentication, projects, weld points, revisions, approvals and tests.
