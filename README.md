# SpotWeldPro AI

**SpotWeldPro AI**, direnç nokta kaynağı mühendisliği için parametrik analiz, kalite değerlendirmesi, hata olasılığı analizi ve yönetilen kaynak mühendisliği kararlarını destekleyen profesyonel bir mühendislik karar destek platformudur.

**SpotWeldPro AI** is a professional engineering decision-support platform for resistance spot welding — covering parametric analysis, quality evaluation, failure probability analysis, welding lobe / process window engineering, and governed welding engineering traceability.

> **Repository scope:** This repository contains the SpotWeldPro AI platform only.
> It does **not** contain image processing, OpenCV, YOLO, or visual defect classification.

---

## Release Status / Sürüm Durumu

**v3.0.0-alpha.4 — Pre-Transfer Engineering Baseline**
`2026-10-13` · Pre-release · Alpha

This release establishes the complete engineering baseline before repository transfer to the dedicated SpotWeldPro-AI account. It includes the full customer demo UX, material family normalization hotfix, TR/EN internationalization, organization/profile foundation, and all GATE-12 acceptance verification results.

| Gate | Result |
|------|--------|
| Frontend build (tsc + vite) | **PASS** |
| Backend focused regression (144 tests) | **PASS** |
| Material family validation (30 tests) | **PASS** |
| Live API acceptance (GATE_12_R5B, 19 checks) | **PASS** |
| `git diff --check` | **PASS** |
| Pre-existing test failures | 2 (4T scope — known, unrelated to demo path) |
| Secret scan | CLEAN |

**Classification:** Alpha / Pre-release. Not production deployment approval.
**Engineering validation:** Surrogate models v0.9 — field calibration required.

---

## Product Overview / Ürün Özeti

SpotWeldPro AI, aşağıdaki mühendislik bileşenlerini birleştirir:

- Deterministik direnç nokta kaynağı parametre hesapları
- Malzeme ailesi doğrulama ve TR/EN normalleştirmesi
- Nugget çapı tahmini (süroge model v0.9)
- Kaynak lobu / proses penceresi analizi
- Kaynak kalite analizi (4 parametre kontrolü)
- Hata olasılığı analizi (10 hata modu)
- İki ve üç katlı istif kaynağı desteği
- Kaplı / kaplamasız malzeme değerlendirmesi
- Yönetilen mühendislik kuralı kayıt defteri (Governed Rule Registry)
- Kanıt doğrulama otoritesi (Evidence Verification Authority)
- Makine hazırlık kontrolü (Machine Readiness Check — MRC)
- Dijital kaynak pasaportu (Digital Weld Passport — DWP)

The engineering principle is explicit:

> **AI provides explanation, engineering context and evidence support.
> Final engineering decisions remain based on deterministic engineering rules.**

---

## Architecture / Mimari

```
Public React UI (Vite + TypeScript)
        ↓
Authenticated Engineering Application
        ↓
REST API  (FastAPI / Python 3.12)
        ↓
Application Services
        ↓
Engineering Domain Layer
  ┌─────────────────────────────┐
  │ Weld Analysis Engine        │
  │ Failure Probability Engine  │
  │ Reference Profile System    │
  │ Material Normalization      │
  │ Engineering Rule Registry   │
  │ Evidence Verification       │
  │ Machine Readiness Check     │
  │ Digital Weld Passport       │
  └─────────────────────────────┘
        ↓
SQLAlchemy / PostgreSQL
```

### Backend
- Python 3.12 · FastAPI · SQLAlchemy · Alembic
- PBKDF2-SHA256 password hashing (240,000 iterations)
- HMAC-HS256 JWT authentication
- In-process sliding-window rate limiter (60 req/IP/60 s)
- Pydantic v2 request validation

### Frontend
- React 18 · TypeScript · Vite · React Router
- Bilingual TR/EN (appContent.ts + publicContent.ts)
- Public routes: `/` · `/features` · `/how-it-works` · `/packages` · `/demo` · `/login`
- Authenticated app: `/app` (dashboard, analysis, engineering, failure probability)

### Infrastructure
- Docker Compose (backend + PostgreSQL; frontend dev server external)
- GitHub Actions CI: SQLite tests · PostgreSQL E2E tests · frontend build
- Alembic migration chain: `0016_merge_heads` (current head)

---

## Engineering Capabilities / Mühendislik Yetkinlikleri

### Material Family Validation / Malzeme Ailesi Doğrulama

Supports 7 canonical material families (Turkish-keyed) with 26 unambiguous English aliases:

| Turkish (canonical) | English aliases |
|---------------------|-----------------|
| Düşük / Orta Karbonlu Çelik | Mild Steel, Low Carbon Steel |
| AHSS / UHSS / PHS | AHSS, UHSS, PHS |
| Galvanizli / Kaplamalı Çelik | Galvanized Steel, Coated Steel, Zinc Coated |
| Paslanmaz Çelik | Stainless Steel, Stainless |
| Alüminyum Alaşımları | Aluminum Alloys, Aluminium Alloys |
| Süper Alaşımlar | Superalloy, Superalloys |
| Karma Malzeme | Mixed, Mixed Material, Dissimilar |

Unknown and ambiguous inputs (e.g. bare `"Steel"`) return HTTP 422 with `UNSUPPORTED_MATERIAL_FAMILY`.

### Weld Parameter Engine / Kaynak Parametre Motoru

For 2T and 3T stack-ups, the engine evaluates:

- **Welding current / Kaynak akımı** — material-family-aware range (kA)
- **Weld time / Kaynak süresi** — thickness-dependent range (cycles)
- **Electrode force / Elektrot kuvveti** — thickness-dependent range (kN)
- **Electrode tip diameter / Elektrot uç çapı** — thickness-dependent range (mm)
- Cooling flow and temperature checks
- Coated material penalty (kaynak çapağı riski / expulsion risk flag)
- 3T multi-layer penalty

Output: `score` (0–100), `risk_level` (LOW/MEDIUM/HIGH), `recommended_ranges`, `risks`, `actions`.

### Nugget Diameter Prediction / Nugget Çapı Tahmini

**Status: IMPLEMENTED_NOT_FULLY_VALIDATED (Surrogate model v0.9)**

Predicts `nugget_min_mm` and `nugget_opt_mm` from minimum sheet thickness using a calibrated interpolation table. Field calibration pending.

Example (t = 1.5 mm): min = 5.2 mm · opt = 6.7 mm · ISO 5√t = 6.12 mm.

### Welding Lobe / Proses Penceresi Analizi

**Status: IMPLEMENTED_NOT_FULLY_VALIDATED (Surrogate model v0.9)**

Generates a process-window map across current × time space:
- Safe / Insufficient fusion / Expulsion zones
- Optimum operating point
- Sensitivity analysis (current-dominant)
- ~77 evaluation points per analysis

Zone labels currently Turkish-only ("Güvenli", "Yetersiz Füzyon"). i18n mapping is a known gap.

### Weld Quality Analysis / Kaynak Kalite Analizi

Evaluates 4 weld parameters against thickness-based reference ranges.
Status per parameter: `Uygun` / `Düşük` / `Yüksek`.
GATE_12_R4 TC6: all 4 parameters `Uygun` at nominal settings.

### Failure Probability Analysis / Hata Olasılığı Analizi

10 failure modes with `probability_percent`, `severity`, `priority_actions`, and engineering disclaimer.
Response schema: `failure_modes[]` array at `/api/v1/failure-probability`.
GATE_12_R4 TC7: 10 failure modes, probability range 1.3–17.8%.

### Ultrasonic Validation / Ultrasonik Doğrulama

**Status: NOT_IMPLEMENTED** — UI guidance text only (`ultrasonicGuidance` keys in i18n).
No dedicated API endpoint. Not available for customer demo.

### Governed Engineering Backend

**Status: IMPLEMENTED_AND_TESTED (PostgreSQL E2E)**

- Engineering Rule Registry: DRAFT → SOURCE_BACKED → ENABLED → ACTIVE lifecycle
- Evidence Verification Authority: human-only, separation of duties
- Governed Rule Evaluation: MIN/MAX/RANGE/EQUALS operators
- Machine Readiness Check: READY/NOT_READY/ENGINEERING_REVIEW_REQUIRED
- Digital Weld Passport: CREATED → DRAFT → ... → PRODUCTION_ACTIVE

Governed capabilities are functional but not declared production-enabled in this alpha.

---

## Authentication & Security / Kimlik Doğrulama ve Güvenlik

| Feature | Detail |
|---------|--------|
| Password hashing | PBKDF2-SHA256, 240,000 iterations |
| Token format | HMAC-HS256 JWT |
| Access token TTL | 30 min (configurable) |
| Refresh token TTL | 7 days (configurable) |
| Demo account role | `READ_ONLY` |
| Rate limiting | 60 req/IP/60 s (in-process, single-worker) |
| Demo hardening | `HOSTED_DEMO=true` enforces strong JWT secret at startup |
| API docs hiding | `DISABLE_DOCS=true` removes `/docs`, `/redoc`, `/openapi.json` |

**For customer demo deployment:** `HOSTED_DEMO=true`, strong `JWT_SECRET_KEY` (≥32 chars), HTTPS termination, and scoped `CORS_ORIGINS` are required before external access.

---

## TR/EN Internationalization / TR/EN Uluslararasılaştırma

UI language switching between Turkish and English is implemented throughout the authenticated application and public pages.

Key files:
- `frontend/src/i18n/appContent.ts` — authenticated app (TR + EN, ~1153 lines)
- `frontend/src/i18n/publicContent.ts` — public pages (TR + EN)
- `frontend/src/i18n/AppLanguageContext.tsx` — language context provider

**Gap:** Weld-lobe zone labels (`"Güvenli"`, `"Yetersiz Füzyon"`) are hardcoded in the backend engine — not yet mapped to i18n keys.

---

## Prerequisites / Ön Koşullar

- Docker Desktop (Windows/Mac/Linux) — for full-stack deployment
- Python 3.12 + pip — for backend development
- Node.js 20 + npm — for frontend development

---

## Quick Start with Docker / Docker ile Hızlı Başlangıç

```bash
# 1. Copy and configure environment
copy .env.example .env
# Edit .env: set ADMIN_PASSWORD, DEMO_PASSWORD, JWT_SECRET_KEY, POSTGRES_PASSWORD

# 2. Start PostgreSQL and backend
docker compose up --build

# Backend API:   http://localhost:8000
# Swagger UI:    http://localhost:8000/docs  (disable with DISABLE_DOCS=true)
```

Start the frontend separately (Vite dev server is not in the Docker Compose file):

```bash
cd frontend
npm install
npm run dev
# Frontend:  http://127.0.0.1:5173
```

---

## Local Development / Yerel Geliştirme

### Backend

```bash
cd backend
py -m pip install -r requirements.txt

# Run migrations (SQLite for local dev)
py -m alembic upgrade head

# Start development server
py -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# Run tests
py -m pytest -q tests/
```

### Frontend

```bash
cd frontend
npm install
npm run dev        # Vite dev server → http://127.0.0.1:5173
npm run build      # Production build (includes tsc + vite)
```

---

## Environment Configuration / Ortam Yapılandırması

Copy `.env.example` to `.env` and set all required values:

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `JWT_SECRET_KEY` | Yes | ≥32 chars; non-placeholder when `HOSTED_DEMO=true` |
| `ADMIN_USERNAME` | Yes | Admin account username |
| `ADMIN_PASSWORD` | Yes | Admin account password |
| `DEMO_USERNAME` | Yes | Demo account username (default: `demo`) |
| `DEMO_PASSWORD` | Yes | Demo account password |
| `POSTGRES_PASSWORD` | Yes | PostgreSQL root password |
| `CORS_ORIGINS` | Recommended | Comma-separated allowed origins |
| `HOSTED_DEMO` | Hosting | `true` enforces JWT strength checks at startup |
| `DISABLE_DOCS` | Hosting | `true` hides `/docs`, `/redoc`, `/openapi.json` |

**Never commit `.env` to version control.** `.env` and `.env.*` are gitignored.

---

## Testing / Test Altyapısı

```bash
cd backend

# Core regression suite (SQLite)
py -m pytest -q tests/

# Material family validation (30 regression tests)
py -m pytest -q tests/test_material_family_validation.py

# PostgreSQL governed E2E (requires POSTGRES_TEST_DATABASE_URL)
py -m pytest -q tests_postgresql/
```

**Known pre-existing failures (unrelated to demo path):**
- `test_H_4T_requires_engineering_review` — 4T scope boundary (not a supported product scope)
- `test_H_4T_no_t_min_fallback` — same

Full suite baseline: 144 PASS · 2 pre-existing FAIL (confirmed in GATE_12_R4/R5) · 9 warnings.

---

## API Documentation / API Dokümantasyonu

When `DISABLE_DOCS=false` (default for development):

| Endpoint | URL |
|----------|-----|
| Swagger UI | `http://localhost:8000/docs` |
| ReDoc | `http://localhost:8000/redoc` |
| OpenAPI JSON | `http://localhost:8000/openapi.json` |

Key endpoints:

| Endpoint | Auth | Description |
|----------|------|-------------|
| `POST /api/v1/auth/login` | Public | Username + password → JWT tokens |
| `GET  /api/v1/auth/me` | Bearer | Current user info |
| `POST /api/v1/weld-analysis` | Public | 2T/3T weld parameter analysis |
| `POST /api/v1/failure-probability` | Bearer | 10-mode failure probability |
| `GET  /api/v1/health` | Public | Service health check |

---

## Repository Structure / Depo Yapısı

```
SpotWeldPro-AI/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # FastAPI routers
│   │   ├── application/     # Application services
│   │   ├── core/            # security.py, rate_limit.py
│   │   ├── domain/          # engine.py, materials.py, failure_probability.py,
│   │   │                    # reference_profile.py, rules_engine.py, …
│   │   ├── models/          # SQLAlchemy models + enums
│   │   ├── repositories/    # DB access layer
│   │   └── schemas/         # Pydantic request/response schemas
│   ├── alembic/versions/    # 0001 → 0016_merge_heads
│   ├── tests/               # SQLite-based test suite
│   ├── tests_postgresql/    # PostgreSQL E2E test suite
│   ├── scripts/             # seed_demo_user.py, seed_default_profile.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/           # AnalysisPage, EngineeringPage, FailureProbabilityPage, …
│   │   ├── components/      # weld/, engineering/, public/
│   │   ├── i18n/            # appContent.ts, publicContent.ts, AppLanguageContext.tsx
│   │   ├── context/         # WeldAnalysisContext.tsx
│   │   └── api/client.ts    # API client (VITE_API_URL)
│   ├── public/
│   └── package.json
├── docs/                    # Engineering design documents
├── .github/
│   ├── workflows/ci.yml     # CI: SQLite tests + PostgreSQL E2E + frontend build
│   └── ISSUE_TEMPLATE/
├── docker-compose.yml
├── .env.example
├── CHANGELOG.md
└── README.md
```

---

## Version History / Sürüm Geçmişi

| Version | Date | Description |
|---------|------|-------------|
| v3.0.0-alpha.4 | 2026-10-13 | Pre-transfer engineering baseline; material family hotfix; full demo UX |
| v3.0.0-alpha.3 | 2026-09-05 | PostgreSQL E2E governance validation |
| v3.0.0-alpha.2 | 2026-09-01 | Governed API integration |
| v3.0.0-alpha.1 | 2026-08-28 | Governed engineering foundation |
| v1.3.0 | 2026-07-17 | Frontend TypeScript build; security hardening |
| v1.2.0 | 2026-07-16 | GitHub-ready repository structure |

---

## Demo Availability / Demo Erişimi

A local private demo is available for authorized users at `http://127.0.0.1:8001` (guarded port) on the development machine. Customer-facing cloud deployment is planned via a dedicated private repository.

No public live demo URL currently exists. Do not use development credentials on any internet-accessible instance.

---

## Known Limitations / Bilinen Kısıtlamalar

| Area | Limitation |
|------|------------|
| Surrogate model accuracy | Nugget diameter and weld-lobe predictions are surrogate model v0.9 — field calibration with independent reference measurements is required before use in production engineering decisions |
| Weld-lobe zone i18n | Zone labels ("Güvenli", "Yetersiz Füzyon") are hardcoded in Turkish in the backend engine |
| Ultrasonic validation | No dedicated API endpoint — UI guidance text only |
| Rate limiter | In-process only; effective limit multiplies per uvicorn worker in multi-worker deployments |
| Material family input | `material_family` remains a free-text field in `StackDefinitionPanel.tsx` — a `<select>` dropdown conversion is planned |
| 4T stack-up | Not supported (`UNSUPPORTED_PRODUCT_SCOPE`); returns 422 |
| Governed backend | Functional but not declared production-enabled in this alpha |

---

## Roadmap / Yol Haritası

Near-term:
- Private cloud demo deployment (SpotWeldPro-AI account, Railway / Fly.io)
- `material_family` dropdown in frontend
- Weld-lobe zone label i18n
- GitHub Release v3.0.0-alpha.4 on canonical repository

Medium-term:
- Surrogate model field calibration against independent reference data
- Ultrasonic validation endpoint
- Redis-backed rate limiter for multi-worker production deployment
- Expanded engineering library and reference profile seeding

---

## Engineering Validation Status / Mühendislik Doğrulama Durumu

| Capability | Status |
|------------|--------|
| 2T weld parameter analysis | VERIFIED (GATE_12_R4 TC2) |
| 3T weld parameter analysis | VERIFIED (GATE_12_R4 TC3) |
| Coated/uncoated material | VERIFIED (GATE_12_R4 TC1) |
| Weld quality analysis | VERIFIED (GATE_12_R4 TC6) |
| Failure probability analysis | VERIFIED (GATE_12_R4 TC7) |
| TR/EN material normalization | VERIFIED (GATE_12_R5B, 19/19) |
| Nugget diameter prediction | EXPERIMENTAL (surrogate v0.9) |
| Weld lobe calculation | EXPERIMENTAL (surrogate v0.9) |
| Ultrasonic validation | NOT_IMPLEMENTED |
| Governed Rule Registry (PostgreSQL) | IMPLEMENTED (not production-enabled) |

---

## License / Lisans

See `LICENSE` for repository licensing terms.

---

## Disclaimer / Sorumluluk Reddi

SpotWeldPro AI is an **engineering decision-support tool**, not a certified engineering standard or production approval authority.

All engineering calculations, surrogate model outputs, and governed rule evaluations must be reviewed and validated by qualified welding engineers before use in production, quality, or safety-critical decisions.

Surrogate model predictions (nugget diameter, weld lobe) are based on parametric models and require field calibration against independent reference measurements.

No ISO, AWS, DIN, or OEM certification is claimed. No production accuracy guarantee is implied.

---

*SpotWeldPro AI — Resistance Spot Welding Engineering Decision Support*
*v3.0.0-alpha.4 — Pre-Transfer Engineering Baseline — 2026-10-13*
