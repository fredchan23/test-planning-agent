# PRD: Singapore Healthspan Simulator

## 1. Product Overview

### 1.1 What It Is
The **Healthspan SG Simulator** is a public web tool that shows Singapore residents how their current lifestyle and clinical markers compound to affect their biological *healthspan* — the portion of life spent in good health — and the *morbidity gap* (lifespan minus healthspan). The calculation is deterministic and rule-based (not ML), making every result fully explainable through a structured audit ledger.

### 1.2 Target Users
- **Health-conscious Singapore residents**: Personal risk awareness; English and Simplified Chinese.
- **Healthcare consumers researching lifestyle impact**: Evidence-based lifestyle planning.
- **Clinicians and health educators**: Demonstration tool; explainable output.

### 1.3 Core Value Proposition
- **Explainable**: Every year gained or lost is traced to a specific factor via a structured audit ledger.
- **Actionable**: A "highest-leverage move" recommender surfaces the single change with the biggest healthspan return.
- **Localised**: Full English / Simplified Chinese toggle; clinical terminology anchored to a 15-term reviewed glossary.
- **Trustworthy**: GBD 2019 hazard ratios; Singapore DOS baselines; all sources cited.

---

## 2. Technical Architecture

### 2.1 Stack
- **Frontend framework**: Next.js 16 (App Router), TypeScript, Tailwind CSS 4
- **Frontend tests**: Vitest + @testing-library/react + jsdom
- **Backend**: Python 3.12, FastAPI, Pydantic v2
- **Backend tests**: pytest
- **Deployment**: Vercel all-in-one (static Next.js export + Python serverless function via Mangum adapter)
- **Fonts**: Space Grotesk (body), Instrument Serif (healthspan figure), DM Mono (monospace)
- **i18n**: Custom `useT` hook + `useSyncExternalStore` (`LocaleProvider`); no routing dependency

### 2.2 Deployment Model
- `frontend/` builds to a static export (`output: export`).
- `api/v1/calculate.py` is a Python serverless function bundled with `backend/app/**` via Mangum.
- Both live on one Vercel domain; no separate backend host.
- `NEXT_PUBLIC_BACKEND_URL` is intentionally unset on Vercel — the frontend calls `/api/v1/calculate` (same-origin), routed by Vercel to the Python function.

### 2.3 Request Flow
ControlPanel (user input)  
→ debounced POST `/api/v1/calculate` (400ms, AbortController for stale cancellation)  
→ FastAPI HealthspanEngine (4-tier + time dimension + recommender)  
→ JSON response `{metrics, calendar, audit_ledger, leverage}`  
→ HealthspanCard + LifeCalendar + LeverageCard + AuditLedgerPanel (conditional)

---

## 3. Data Model and Ground Truth

### 3.1 Baseline Stratification (Tier 1)
- **Male**: Base Lifespan = 81.8 years, Base Healthspan = 73.0 years (Source: Singapore DOS 2024-2025 + GBD 2019)
- **Female**: Base Lifespan = 86.0 years, Base Healthspan = 75.0 years (Source: Singapore DOS 2024-2025 + GBD 2019)

### 3.2 Factor Set (Frozen at 8 for v1.0)
All hazard ratios sourced from IHME Global Burden of Disease 2019 Risk Factor Analysis.

| Factor | States | Multiplier Range | Notes |
| :--- | :--- | :--- | :--- |
| `smoking` | `non_smoker`, `active_smoker` | 1.00–0.85 | Recovery curve applies (time-dimension) |
| `physical_activity` | `active`, `moderate`, `sedentary` | 1.12–0.90 | Recovery curve applies (time-dimension) |
| `bmi` | `optimal`, `overweight`, `obese` | 1.02–0.88 | — |
| `alcohol` | `none`, `moderate`, `heavy` | 1.01–0.87 | — |
| `sleep` | `optimal`, `poor` | 1.00–0.91 | — |
| `diet` | `optimal`, `average`, `poor` | 1.04–0.90 | — |
| `social_connection` | `high`, `moderate`, `isolated` | 1.05–0.88 | — |
| `blood_pressure` | `normal`, `elevated`, `high` | 1.00–0.86 | — |

### 3.3 Compounding Formula (Tier 2)
- `raw_M = ∏ m_i` # product of all 8 factor multipliers
- `effective_M = α + (1 − α) × raw_M` # asymptotic floor; α = 0.70
- `standard_hs = base_hs × effective_M`
  - `α = 0.70` is loaded from `ruleset.json` -> `curve_params.alpha` (never hardcoded).
  - Worst-case all-negative: `raw_M ≈ 0.415` -> `effective_M ≈ 0.825` -> `~60 healthy years` (male).
  - `marginal_hs_delta = base_hs × (1 - α) × (m_i - 1.0)` — used in audit ledger per-factor entries.

### 3.4 Tier 3 — Interaction Overrides
If a collision rule's conditions match the payload, the override is computed as:
- `override_hs = base_hs × override_M` # direct, no asymptotic wrapping
- **Reconciliation**: `protected_hs = min(standard_hs, override_hs)` — most penalising wins. A reconciliation audit entry is always appended.

### 3.5 Tier 4 — Biological Caps
- `ceiling = min(absolute_max_healthspan, base_lifespan − minimum_morbidity_period_years)`
- `final_hs = min(protected_hs, ceiling)`

### 3.6 Time Dimension
- `smoking_change_age` and `physical_activity_change_age` are optional fields. When provided and the factor is at its worst state, the engine applies linear interpolation over the recovery curve anchors.

### 3.7 Rounding Contract
- `predicted_healthspan` and `predicted_morbidity_period` are pre-rounded to one decimal place server-side using round-half-up (`math.floor(x * 10 + 0.5) / 10`) before serialisation.

---

## 4. API Contract

### POST `/api/v1/calculate`
#### Request Payload
```json
{
  "user_profile": {
    "sex": "male" | "female",
    "current_age": 35,
    "lifestyle": {
      "smoking": "non_smoker" | "active_smoker",
      "smoking_change_age": 40,
      "physical_activity": "active" | "moderate" | "sedentary",
      "physical_activity_change_age": 45,
      "bmi": "optimal" | "overweight" | "obese",
      "alcohol": "none" | "moderate" | "heavy",
      "sleep": "optimal" | "poor",
      "diet": "optimal" | "average" | "poor",
      "social_connection": "high" | "moderate" | "isolated"
    },
    "clinical": {
      "blood_pressure": "normal" | "elevated" | "high"
    }
  }
}
```

---

## 5. Frontend — Pages and Components

### 5.1 Site Structure (Three-Page Marketing Site)
- `/` (`LandingBody` - Server Component): Hero + value proposition; "Try Simulator →" CTA
- `/simulator` (`page.tsx` - Client Component): The interactive calculator
- `/explore` (`explore/page.tsx` - Server Component): "Explore the Science" — GBD data, compounding chart, cost-of-risk bars
- **Shared Chrome**: `SiteNav` (with EN/中文 locale toggle), `SiteFooter`, `RevealWrapper`

### 5.2 Key Components
- **ControlPanel**: 8 lifestyle/clinical inputs (radio groups, dropdowns) + 3 age fields (custom stepper ▲/▼). Conditionally reveals change ages.
- **LifeCalendar**: CSS grid of 8x8px dots (spent, healthy, morbid, future) padding to `MAX_YEARS = 100` rows.
- **HealthspanCard**: Metric display showing projected healthspan and morbidity period.
- **LeverageCard**: Highlights the single modifiable factor with the largest healthspan gain.
- **AuditLedgerPanel**: Expandable details of calculations (Tiers 1–4).
