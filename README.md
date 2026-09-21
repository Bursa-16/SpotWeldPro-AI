# Spot Welding Parameter Analysis

**SpotWeldPro AI** is a professional engineering decision-support platform for **resistance spot welding parameter analysis, governed rule evaluation, machine readiness, engineering traceability, and Digital Weld Passport workflows**.

> **Product name:** Spot Welding Parameter Analysis  
> **Product brand:** SpotWeldPro AI

> **Repository scope:** This repository contains the **Spot Welding Parameter Analysis** product.  
> It does **not** contain image processing, camera inspection, OpenCV, YOLO, or visual defect classification. Those capabilities belong to the separate **Spot Welding Image Processing** product.

---

# Product Vision

Spot Welding Parameter Analysis is designed to support manufacturing, quality, industrialization, and welding engineering teams in making **faster, more systematic, traceable, and reproducible resistance spot welding decisions**.

The platform combines:

- Deterministic engineering calculations
- Governed engineering rules
- Resistance spot welding parameter analysis
- Weld quality engineering
- Weld-lobe / process-window engineering
- DOE and optimization workflows
- Failure and risk analysis
- Machine Readiness Check
- Digital Weld Passport traceability
- AI-assisted engineering explanation and context

The engineering principle is explicit:

> **AI provides explanation, engineering context, and evidence support; final engineering decisions remain based on deterministic engineering rules.**

AI does not override governed engineering calculations, thresholds, lifecycle controls, or human engineering authority.

---

# Release Status

## Current Development Status

Spot Welding Parameter Analysis currently contains two major product layers:

### Governed Engineering Backend

The backend provides the deterministic and governed engineering foundation for:

- Engineering Rule Registry
- Evidence Verification Authority
- Rule lifecycle governance
- Applicability resolution
- Rule evaluation
- Machine Readiness Check
- Digital Weld Passport
- Auditability
- Provenance
- Revision pinning
- Persistent governed idempotency

### Public Frontend Experience

The frontend now provides a complete public pre-login product experience:

```text
/               → Landing Page
/features       → Engineering Features
/how-it-works   → Engineering Workflow
/packages       → Product Packages
/demo           → Demo Experience
/login          → Login
/app            → Authenticated Engineering Application

Current Verification
Backend

Current governed backend verification baseline:

Full backend suite: 361 passed
Digital Weld Passport focused tests: 3 passed
Migration tests: 11 passed
Machine Readiness persistence tests: 8 passed
Ruff: PASS
Alembic migration chain: through 0010_digital_weld_passport

Real PostgreSQL integration remains environment-dependent where explicitly noted by the governed test stages.

Frontend

Current frontend verification:

React + TypeScript build: PASS
Public routing: PASS
Public/app-shell separation: PASS
Public page rendering: PASS
Responsive public UI foundation: PASS
No backend files modified by the public UI stages

Public pages verified:

Landing Page
Features
How It Works
Packages
Demo
Login
Public Product Experience
Landing Page

The public landing experience introduces:

Spot Welding Parameter Analysis product scope
SpotWeldPro AI brand
Core engineering capabilities
Target industries
Engineering workflow
Package overview
Demo access
Engineering trust principles

The visual direction is designed around a premium industrial engineering software identity rather than a generic SaaS interface.

Engineering Features
Engineering Parameter Analysis

Engineering analysis can include:

Welding current
Weld time
Electrode force
Squeeze time
Hold time
Cooling conditions
Material context
Sheet stack
Electrode context
Process context
Weld Quality Analysis

Supports engineering interpretation of welding conditions and quality-related process behavior.

Focus areas include:

Process stability
Engineering result interpretation
Quality-oriented evaluation
Process-window understanding
Parameter interaction analysis
Weld Lobe / Process Window Engineering

Supports understanding of the usable engineering process window.

Capabilities include:

Weld-lobe analysis
Operating-window evaluation
Parameter interaction analysis
Engineering limit visualization
Process robustness assessment
DOE & Optimization

Supports systematic exploration of engineering parameters.

Typical workflow:

Engineering Inputs
        ↓
Parameter Space
        ↓
DOE Exploration
        ↓
Engineering Evaluation
        ↓
Optimization
        ↓
Recommended Engineering Region

Optimization does not replace deterministic engineering acceptance rules.

Failure & Risk Analysis

The parameter-analysis engine can support engineering assessment of potential failure modes such as:

Expulsion / metal splash
Insufficient fusion
Small nugget
Excessive indentation
Electrode sticking
Accelerated electrode wear
LME / surface cracking risk
Coating damage
Shunt-related instability
Cooling-related instability

The platform may provide:

Failure probability context
Parameter sensitivity
Dominant-factor explanation
Engineering decision support
Recommended corrective-action context
How It Works

The public engineering workflow is organized around six stages:

01 — Project / Application Context

Define the engineering context of the weld application.

Examples:

Project
Component
Weld point
Application
Machine / line context
02 — Material & Sheet Information

Define the material stack and sheet configuration.

Examples:

Material type
Sheet thickness
Coating
Stack-up
Surface condition
03 — Welding Parameters

Enter or evaluate the principal resistance spot welding parameters.

Examples:

Welding current
Weld time
Electrode force
Squeeze time
Hold time
Cooling parameters
04 — Analysis & Engineering Checks

The deterministic engineering layer evaluates the available parameter and rule context.

Possible outputs include:

Engineering evaluation
Quality context
Applicable rule checks
Failure context
Engineering warnings
Traceable decision evidence
05 — Process Window & Optimization

Engineering teams may explore:

Weld-lobe behavior
Process window
DOE
Sensitivity
Optimization
Failure-risk context
06 — Result, Validation & Traceability

Engineering outputs can be connected to:

Governed rule evaluation
Machine readiness
Audit history
Revision provenance
Digital Weld Passport
Engineering traceability
Product Packages

The public product structure currently presents three deployment levels.

Starter

Designed for focused resistance spot welding engineering analysis.

Typical capability scope:

Core parameter analysis
Basic weld quality engineering
Standard reporting
Professional

Recommended for engineering teams requiring broader process analysis.

Typical capability scope:

Full engineering analysis
Weld-lobe / process-window tools
DOE and optimization
Failure analysis
Project and weld-point traceability
AI-assisted engineering explanation
Enterprise

Designed for organization-level engineering deployment.

Typical capability scope:

Professional capabilities
Configurable standards and rules
Enterprise traceability
Governance
Integration possibilities
Organization-level deployment

Commercial configuration is defined according to deployment scope and customer requirements.

No commercial prices or contractual limits are hard-coded into the public product presentation.

Demo Experience

The /demo route provides a frontend-only illustrative product experience.

Typical walkthrough:

Select project / weld point
Enter engineering inputs
Run parameter analysis
Review weld-quality / process-window context
Explore optimization / failure context
Review traceable engineering output

The demo does not represent validated production data.

It does not contain:

Customer production measurements
OEM-confidential data
Fabricated production results
Fabricated AI engineering decisions
AI-Assisted Engineering

AI is intentionally positioned as a supporting capability.

AI may assist with:

Engineering explanation
Engineering context
Evidence summary
Knowledge workflows
Interpretation support
User guidance

AI does not:

Invent governed thresholds
Override deterministic calculations
Override engineering rules
Grant lifecycle authority
Activate rules
Approve machine readiness
Approve Digital Weld Passports

AI explanation and engineering context support the user; final engineering decisions remain based on deterministic engineering rules.

Engineering Principles

SpotWeld-AI keeps deterministic engineering logic authoritative.

No hidden or implicit engineering authority
No automatically invented engineering thresholds
Exact revision and provenance pinning
Fail-closed handling of missing, stale, conflicting, or invalid inputs
Human-scoped authority
Separation of duties
Append-only corrections
Immutable historical records
Persistent governed idempotency
Atomic state + audit + receipt transactions
No silent “latest revision” authority
AI may assist with explanation and knowledge workflows but does not override governed deterministic engineering decisions
Governed Engineering Flow
Engineering Rule Registry
        ↓
Evidence + Verification Authority
        ↓
SOURCE_BACKED Promotion
        ↓
ENABLED
        ↓
ACTIVE
        ↓
Deterministic Applicability Resolution
        ↓
Governed Rule Evaluation
        ↓
Persisted Rule Evaluation
        ↓
Machine Readiness Check
        ↓
Persisted MRC Assessment
        ↓
Digital Weld Passport

Each governed stage pins the exact revisions and provenance required to reproduce the engineering decision later.

Engineering Rule Registry

The governed Engineering Rule Registry provides:

Immutable engineering rule revisions
Evidence-to-rule traceability
Explicit SOURCE_BACKED classification
Revision-level provenance
Append-only lifecycle history
Governed promotion, enablement, and activation

Lifecycle:

DRAFT
  ↓
SOURCE_BACKED
  ↓
ENABLED
  ↓
ACTIVE

Important rules:

SOURCE_BACKED does not mean ENABLED
SOURCE_BACKED does not mean ACTIVE
No direct SOURCE_BACKED → ACTIVE transition
Activation requires a separate governed transition
Exact scope and effective-time rules apply
Legacy DEFAULT_RULES / rules_engine paths are not promoted into governed authority
Evidence Verification Authority

Evidence verification is governed by explicit human authority.

Capabilities include:

Human-only authoritative evidence verification
Explicit scoped delegation
Exact EvidenceReference revision pinning
Creator / verifier separation of duties
No wildcard administrator authority
No implicit role-based authority
Immutable authority snapshots
Append-only verification corrections
Auditable authorization denials
Persistent idempotency
Atomic governed transactions

Evidence verification does not automatically promote or activate an engineering rule.

SOURCE_BACKED Promotion

A rule revision may become SOURCE_BACKED only through a separate governed transition.

Requirements include:

Exact rule revision
Verified evidence
Exact evidence revision pinning
Governed promotion authority
Separation from evidence-verification authority where required
Audit traceability
Persistent idempotency
Atomic Unit of Work

SOURCE_BACKED remains distinct from ENABLED and ACTIVE.

Rule Enablement and Activation

Governed rule lifecycle transitions are explicit and append-only.

SOURCE_BACKED
     ↓
  ENABLED
     ↓
   ACTIVE

Controls include:

Explicit human lifecycle authority
Exact customer / project / site / machine scope
Effective-time windows
Fail-closed lifecycle checks
No automatic activation
No direct SOURCE_BACKED → ACTIVE
Historical lifecycle events remain immutable
Governed Applicability Resolution

The applicability resolver determines which ACTIVE rule revision governs an explicit engineering context.

Key characteristics:

Exact customer / project / site / machine context matching
Explicit scopes only
No implicit wildcard fallback
Deterministic governed selection
Conflict conditions fail closed
Zero eligible matches remain unresolved
Deterministic provenance
Immutable provenance-complete results
Governed Rule Evaluation

Rule evaluation operates only on an explicitly governed rule revision.

Supported deterministic operators include:

MIN
MAX
RANGE
EQUALS

Supported outcomes include:

SATISFIED
NOT_SATISFIED
NOT_APPLICABLE
UNIT_MISMATCH
UNRESOLVED

Unit conversion is permitted only through an explicit governed Unit Policy.

The evaluator does not use:

Implicit unit coercion
Hidden threshold lookup
Invented tolerance behavior
Automatic evaluation of unselected rules

Unsupported or malformed inputs fail closed.

Rule Evaluation Persistence

Persisted Rule Evaluations provide:

Stable evaluation identity
Append-only evaluation revisions
Exact rule revision pinning
Exact applicability-result pinning
Exact observation snapshot
Unit-policy and conversion provenance
Immutable result snapshots
Append-only correction / supersession
Governed audit
Persistent idempotency
Atomic completion

The persistence layer does not recompute applicability, unit conversion, or engineering comparison.

Machine Readiness Check — MRC

Machine Readiness Check deterministically aggregates governed engineering evaluations.

Supported outcomes:

READY
NOT_READY
ENGINEERING_REVIEW_REQUIRED
MANUAL_REVIEW_REQUIRED
NOT_EVALUATED

MRC includes:

Governed required / optional check definitions
Exact RuleEvaluation revision pins
Deterministic blocker precedence
Missing evidence handled fail-closed
Invalidated evidence handled fail-closed
Secondary blocker trace retention
Exact context matching
Permutation-invariant aggregation

The MRC layer does not invent engineering requirements or thresholds.

Machine Readiness Persistence

Persisted Machine Readiness Assessments provide:

Stable assessment_id
Immutable revision_number
Exact RuleEvaluation revision pins
Immutable blocker snapshots
Immutable prerequisite snapshots
Append-only correction history
Governed audit
Persistent idempotency
Atomic transaction handling

Downstream consumers pin:

assessment_id + revision_number

There is no authoritative “latest MRC” lookup.

Digital Weld Passport — DWP

The Digital Weld Passport provides governed engineering traceability.

Passport Identity
Stable passport identity
Immutable passport revisions
Exact weld identity scope
Exact revision provenance
Append-only correction and supersession
No mutable “latest passport” authority
MRC Integration

DWP pins an exact Machine Readiness Assessment:

assessment_id + revision_number

There is no “latest MRC” authority.

DWP Lifecycle
CREATED
   ↓
DRAFT
   ↓
ENGINEERING_DEFINED
   ↓
VALIDATION_PENDING
   ↓
VALIDATED
   ↓
APPROVED
   ↓
PRODUCTION_ACTIVE

Historical dispositions may include:

SUPERSEDED
RETIRED
ARCHIVED
Readiness Gate
DRAFT may exist with a non-READY MRC
VALIDATED requires a pinned READY MRC
APPROVED requires a pinned READY MRC
PRODUCTION_ACTIVE requires a pinned READY MRC

Non-READY states remain explicit blockers.

Governance

DWP provides:

Explicit lifecycle transitions
Illegal lifecycle jumps rejected
Finalized revisions immutable
Corrections through new superseding revisions
Separation of duties
Exact engineering provenance
Governed audit
Persistent idempotency
Caller-owned atomic Unit of Work
No MRC or rule-evaluation recomputation
Architecture
Public React UI
        ↓
Authenticated React Application
        ↓
REST API
        ↓
FastAPI Application Layer
        ↓
Application Services
        ↓
Governed Engineering Domain
        ↓
┌─────────────────────────────┐
│ Engineering Rule Registry   │
│ Evidence Verification       │
│ Applicability Resolution    │
│ Rule Evaluation             │
│ Machine Readiness           │
│ Digital Weld Passport       │
└─────────────────────────────┘
        ↓
SQLAlchemy / PostgreSQL

Governed write operations use caller-owned Unit of Work boundaries.

Authoritative state, governed audit events, and persistent idempotency receipts are committed atomically.

Frontend Architecture

Current frontend stack:

React 18
TypeScript
Vite
React Router
Responsive public product UI
Authenticated engineering application shell

Public routes:

/
├── features
├── how-it-works
├── packages
├── demo
└── login

Authenticated application:

/app

Public product pages do not depend on authenticated application state.

Repository Structure
backend/
  app/
    application/
    domain/
    models/
    repositories/

  alembic/
    versions/

  tests/
  tests_postgresql/

frontend/
  src/
    pages/
    App.tsx
    main.tsx
    styles.css

docs/

.github/

docker-compose.yml
Database Evolution

The governed backend migration chain currently extends through:

0010_digital_weld_passport

Major governed migration stages include:

Engineering Rule Registry persistence
Evidence revision and applicability foundation
Evidence Verification Authority
Rule lifecycle events
Rule Evaluation persistence
Machine Readiness persistence
Digital Weld Passport persistence
Governance Documentation

Key governed-engineering documents include:

100_SDS_MASTER_INDEX.md
docs/111_ENGINEERING_RULE_REGISTRY_DESIGN.md
docs/112_MACHINE_READINESS_CHECK_DESIGN.md
docs/113_DIGITAL_WELD_PASSPORT_DESIGN.md
docs/114_REGISTRY_MRC_DWP_IMPLEMENTATION_PLAN.md
docs/115_EVIDENCE_VERIFICATION_AUTHORITY_POLICY.md

100_SDS_MASTER_INDEX.md remains the authoritative SDS registry.

Quick Start with Docker
copy .env.example .env
docker compose up --build

Frontend:

http://localhost:5173

API:

http://localhost:8000

Swagger:

http://localhost:8000/docs
Backend Development
cd backend
py -m pip install -r requirements.txt
py -m pytest -q
py -m uvicorn app.main:app --reload
Frontend Development
cd frontend
npm install
npm run dev

Development URL:

http://127.0.0.1:5173

Production build:

npm run build
Known Limitations

The project remains under active alpha development.

Current limitations include:

Some governed lifecycle capabilities remain under staged production enablement
Real-PostgreSQL governed E2E validation requires an appropriate PostgreSQL test environment
Full frontend-to-backend integration of every governed backend capability is not yet complete
Concession-based production release workflows remain future work
Automatic machine-release actions are not enabled
External system integrations remain future work
Expanded Digital Weld Passport visualization/reporting remains under development

No capability should be interpreted as production-authoritative unless explicitly enabled by the governed backend lifecycle.

Current Alpha Scope

Included in the current alpha development line:

Governed Engineering Rule Registry
Evidence revision foundation
Evidence Verification Authority
SOURCE_BACKED promotion
Governed Rule Enablement
Governed Rule Activation
Deterministic Applicability Resolution
Governed Rule Evaluation
Rule Evaluation Persistence
Machine Readiness Check
Machine Readiness Persistence
Digital Weld Passport foundation
Public product landing experience
Engineering features page
Engineering workflow / How It Works
Product package presentation
Demo experience
Public login
Authenticated engineering application boundary
Responsive industrial frontend design system
Target Industries

Spot Welding Parameter Analysis is designed for engineering use cases in sectors including:

Automotive OEMs
Automotive Tier-1 suppliers
White goods / appliances
Defense
Rail systems
Machinery manufacturing
Sheet-metal manufacturing
Release Philosophy

Alpha releases are intended for:

Engineering validation
Product demonstration
Architecture verification
User feedback
OEM / Tier-1 technical evaluation
Continued frontend and backend integration

They should not be interpreted as unrestricted production deployment approval.

License

See LICENSE for repository licensing terms.


Bunu mevcut README’nin yerine geçirmenizi öneririm. Özellikle eski README’deki `v3.0.0-alpha.3` / `v3.0.0-alpha.1` kar
