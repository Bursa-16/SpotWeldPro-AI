# SpotWeldPro AI — Release Status

**Last updated:** 2026-10-13
**Current version:** v3.0.0-alpha.4

---

## Current Release

| Field | Value |
|-------|-------|
| Version | `v3.0.0-alpha.4` |
| Title | Pre-Transfer Engineering Baseline |
| Date | 2026-10-13 |
| Tag commit | `aff2e8dffe2849eff5627403434d33127ac16b71` |
| Branch | `main` @ `Bursa-16/SpotWeldPro-AI` |
| Classification | **Alpha / Pre-release** |

---

## Release Classification

```
ALPHA / ENGINEERING DEVELOPMENT

NOT PRODUCTION CERTIFIED
NOT FULLY EXPERIMENTALLY VALIDATED

CUSTOMER DEMO READINESS: CONDITIONAL
  → Local private demo: VERIFIED (GATE_12_R5B, 19/19 PASS)
  → Cloud deployment: REQUIRES separate deployment and acceptance gates

SURROGATE MODEL STATUS: v0.9 — field calibration required
```

---

## Engineering Demo Gate Summary (GATE_12_R4/R5)

| Gate | Status | Evidence |
|------|--------|----------|
| GATE_12_R4 Engineering validation | CONDITIONAL PASS | 8/10 TCs PASS; TC10 BLOCKER fixed by R5 |
| GATE_12_R5 Hotfix implementation | PASS | 30/30 regression tests |
| GATE_12_R5A Read-only verification | PASS | Diff verified, no scope creep |
| GATE_12_R5B Live container verification | PASS | 19/19 HTTP checks at 127.0.0.1:8001 |
| GATE_12_R5C Commit | PASS | `aff2e8d` on `main` |
| GATE_12_R5D Push audit | PASS | 0 blockers, fast-forward |
| GATE_12_R5E GitHub push | PASS | `Bursa-16/SpotWeldPro-AI` main = aff2e8d |

---

## Feature Readiness

| Feature | Status |
|---------|--------|
| 2T weld parameter analysis | VERIFIED |
| 3T weld parameter analysis | VERIFIED |
| Coated material handling | VERIFIED |
| TR/EN material normalization | VERIFIED |
| Weld quality analysis | VERIFIED |
| Failure probability analysis | VERIFIED |
| Nugget diameter prediction | EXPERIMENTAL (surrogate v0.9) |
| Weld lobe / process window | EXPERIMENTAL (surrogate v0.9) |
| Weld lobe i18n (zone labels) | PARTIAL — Turkish only |
| Ultrasonic validation | NOT_IMPLEMENTED |
| Customer demo UX (TR/EN) | VERIFIED (local) |
| Governed Rule Registry | IMPLEMENTED (not production-enabled) |
| Evidence Verification | IMPLEMENTED (not production-enabled) |
| Machine Readiness Check | IMPLEMENTED (not production-enabled) |
| Digital Weld Passport | IMPLEMENTED (not production-enabled) |

---

## Pending Actions Before Cloud Demo

| Action | Priority | Status |
|--------|----------|--------|
| Create private demo repo (SpotWeldPro-AI/SpotWeldPro-AI) | P0 | PENDING |
| Configure hosting (Railway/Fly.io) with HTTPS | P0 | PENDING |
| Set HOSTED_DEMO=true, strong JWT_SECRET_KEY | P0 | PENDING |
| Scope CORS_ORIGINS to demo domain | P0 | PENDING |
| Correct cross-project releases on Bursa-16 | P0 | PENDING |
| Create GitHub Release v3.0.0-alpha.4 | P1 | THIS RELEASE |
| Convert material_family to `<select>` dropdown | P1 | PENDING |
| Map weld-lobe zone labels to i18n | P1 | PENDING |

---

## Release History

| Version | Date | GitHub Release | Canonical Tag |
|---------|------|----------------|---------------|
| v3.0.0-alpha.4 | 2026-10-13 | PENDING | `aff2e8d` |
| v3.0.0-alpha.3 | 2026-09-05 | NO (tag only) | `171bbd04` |
| v3.0.0-alpha.2 | 2026-09-01 | YES (SpotWeld) | `3270ea81` |
| v3.0.0-alpha.1 | 2026-08-28 | YES (SpotWeld) | `b39d8f1d` |
| v0.1.0-alpha.6 | 2026-09-17 | YES (**MachiningPro AI** — CROSS-PROJECT) | `e5eb1ad8` |
| v2.5-academy | 2026-07-22 | YES (**TorqPro** — CROSS-PROJECT) | `a63d9d1a` |

### Cross-Project Release Notice

Two GitHub Releases on `Bursa-16/SpotWeldPro-AI` are confirmed cross-project:

- `v2.5-academy` — GitHub release name: "TorqPro Faz Academy — Engineering Question Bank".
  Assets include `torqpro-faz-academy.bundle`. The tag commit contains SpotWeld docs.
- `v0.1.0-alpha.6` — GitHub release name: "MachiningPro AI v0.1.0-alpha.6 — Phase 1A
  Technical Drawing Foundation". No binary assets. Tag commit contains SpotWeld README.

**Recommended action:** Delete or edit these two GitHub Releases before public promotion.
The git tags point to SpotWeld commits and do not contain cross-project source code.

---

## Disclaimer

SpotWeldPro AI is an engineering decision-support tool. All outputs must be reviewed
by qualified welding engineers before use in production, quality, or safety-critical
decisions. Surrogate model predictions require field calibration. No ISO, AWS, DIN,
or OEM certification is claimed.
