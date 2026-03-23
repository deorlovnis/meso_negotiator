# Frontend Refactoring Plan

Refactoring the React/TypeScript frontend to comply with `react-web.md`.

**Decisions**:
- Feature-based folder structure per react-web.md section 6.1
- Tests written before refactoring for safety
- `onImprove` no-op behavior preserved, flagged as TODO

**Reference**: `react-web.md` — all section numbers below refer to this document.

---

## Table of Contents

1. [Current State](#1-current-state)
2. [Target Structure](#2-target-structure)
3. [Phase 1 — Test Foundation](#3-phase-1--test-foundation)
4. [Phase 2 — Component Tests](#4-phase-2--component-tests)
5. [Phase 3 — Integration Tests](#5-phase-3--integration-tests)
6. [Phase 4 — Refactoring](#6-phase-4--refactoring)
7. [Compliance Matrix](#7-compliance-matrix)
8. [Trade-offs](#8-trade-offs)
9. [TODO](#9-todo)

---

## 1. Current State

### Files (6 files, ~620 lines)

| File | Lines | Role | Violations |
|------|-------|------|------------|
| `App.tsx` | 343 | God component: reducer, 5 API handlers, helpers, 5 phase renderers | sec 1.1 (SRP), 1.3 (container/presentational), 1.4 (split signals), 2.1 (hardcoded values), 6.3 (separation of concerns) |
| `api.ts` | 74 | API client | sec 2.3 (no config for base URL), 6.3 (should live inside feature) |
| `types.ts` | 54 | Type definitions | sec 6.1 (should be feature-scoped) |
| `OfferCard.tsx` | 134 | Presentational card | Duplicates `Signal` type; `signalColor` map should be in constants (sec 2.1) |
| `main.tsx` | 12 | Entry point | Fine |
| `index.css` | 1 | Tailwind import | Fine |

### Violations by react-web.md Section

| Section | Rule | Status |
|---------|------|--------|
| 1.1 Small SRP components | Components under 150-200 lines | `App.tsx` is 343 lines with 5+ responsibilities |
| 1.3 Container vs presentational | Separate data-fetching from display | `App.tsx` mixes API calls with rendering |
| 1.4 When to split | Multiple `useState`, comments as section markers | `App.tsx` has `// Phase: ...` section comments for 5 phases |
| 1.5 Props interface design | Accept only what component uses | N/A yet — no phase components to evaluate |
| 2.1 Constants and enums | Named constants, no magic strings | `NEGOTIATION_ID = 'demo'`, label/icon maps inline |
| 2.3 Environment variables | Single config from env vars | No `config.ts`; API URL only in Vite proxy |
| 5.1 Local vs global state | State colocation | State machine is correctly colocated; will stay in hook |
| 6.1 Feature-based folders | Group by feature, not by type | Flat `src/` with no organization |
| 6.3 Separation of concerns | Business logic in plain TS, not components | `toTitleCase`, `cardToProps`, `errorMessage` live inside App.tsx |
| 7.3 Handle all states | Loading, error, empty, data | Covered (loading/error/offers/agreed/no_deal) |
| 8.1 Business logic in components | Pure functions in `lib/` | Label mapping and formatting live in App.tsx |

### Frontend Tests

Zero. No test framework installed.

---

## 2. Target Structure

Per react-web.md section 6.1 (feature-based folders) and 6.3 (separation of concerns):

```
front/src/
  main.tsx                                    unchanged
  index.css                                   unchanged
  App.tsx                                     REWRITTEN (~40 lines)
  config.ts                                   NEW (sec 2.3)
  test-setup.ts                               NEW

  features/
    negotiation/
      api/
        negotiation-api.ts                    MOVED from api.ts (sec 6.3)
        negotiation-api.test.ts               NEW
      hooks/
        useNegotiation.ts                     NEW (sec 1.3, 7.1)
      components/
        OfferCard.tsx                         MOVED + MODIFIED
        OfferCard.test.tsx                    NEW
        OffersPhase.tsx                       NEW (sec 1.1, 1.4)
        AgreedPhase.tsx                       NEW
        NoDealPhase.tsx                       NEW
        ErrorPhase.tsx                        NEW
        LoadingPhase.tsx                      NEW
      lib/
        format.ts                            NEW (sec 6.3, 8.1)
        format.test.ts                       NEW
        reducer.ts                           NEW (sec 6.3)
        reducer.test.ts                      NEW
      constants.ts                           NEW (sec 2.1)
      types.ts                               MOVED + MODIFIED
      index.ts                               NEW (sec 6.2 barrel)

  shared/
    components/
      StatusBadge.tsx                        NEW (reusable across features)

  .env                                       NEW (sec 2.3)
  .env.example                               NEW
```

### Why This Structure

- **`features/negotiation/`** — all negotiation-related code lives together (sec 6.1: "Feature folders keep related code together")
- **`api/`** — HTTP calls and request/response transforms (sec 6.3)
- **`hooks/`** — data fetching + state management hook (sec 1.3: container/presentational split)
- **`components/`** — pure display components (sec 1.1: SRP, each under 200 lines)
- **`lib/`** — pure TypeScript with no React imports (sec 6.3: "Business logic lives in plain TypeScript files")
- **`constants.ts`** — named constants, no magic strings (sec 2.1)
- **`types.ts`** — feature-scoped types (sec 6.1)
- **`index.ts`** — barrel export at the feature boundary only (sec 6.2)
- **`shared/`** — components reusable across features (sec 6.1: "Shared code is explicitly in shared/")
- **`config.ts`** — single source of truth for env-driven config (sec 2.3)

---

## 3. Phase 1 — Test Foundation

Write unit tests for all pure functions and the state machine. Safety net before refactoring.

### 3.1 Stack Setup

**Install**:
```
npm install -D vitest @testing-library/react @testing-library/jest-dom @testing-library/user-event jsdom
```

**Add to `vite.config.ts`**:
```ts
test: {
  environment: 'jsdom',
  setupFiles: ['./src/test-setup.ts'],
  globals: true,
}
```

**Create `front/src/test-setup.ts`**:
```ts
import '@testing-library/jest-dom/vitest';
```

**Add to `front/package.json` scripts**:
```json
"test": "vitest run",
"test:watch": "vitest"
```

**Prerequisite**: Export `reducer`, `toTitleCase`, `toLabelEnum`, `cardToProps`, `errorMessage`, and the label/icon maps from `App.tsx`. Non-behavioral change to make code testable.

### 3.2 Reducer Tests

**File**: `App.reducer.test.ts` (will become `features/negotiation/lib/reducer.test.ts` after refactor)

| # | Claim | Priority |
|---|-------|----------|
| A1 | `OFFERS_LOADED` from any state produces `{phase: 'offers', data}` | Critical |
| A2 | `OFFERS_UPDATED` produces same shape as `OFFERS_LOADED` | Critical |
| A3 | `ACTION_START` preserves `data` and `pendingAction` | Critical |
| A4 | `AGREED` transitions to `{phase: 'agreed', terms}` | Critical |
| A5 | `NO_DEAL` transitions to `{phase: 'no_deal'}` | High |
| A6 | `ERROR` from any state produces `{phase: 'error', message}` | Critical |
| A7 | Reducer is pure — previous state is never mutated | High |
| A8 | `pendingAction` string preserved verbatim | Medium |

**Key adversarial test**: Dispatch `OFFERS_LOADED` from `error` phase (the retry path). The reducer ignores `_state` entirely — each action fully determines next state. Verify this is intentional by testing from every source phase.

### 3.3 Helper Tests

**File**: `App.helpers.test.ts` (will become `features/negotiation/lib/format.test.ts`)

**toTitleCase** (4 tests):

| # | Input | Expected | Priority |
|---|-------|----------|----------|
| C1 | `'BEST PRICE'` | `'Best Price'` | Medium |
| C2 | `'PRICE'` | `'Price'` | Medium |
| C3 | `''` | `''` | Medium |
| C4 | `'bEsT pRiCe'` | `'Best Price'` | Medium |

**toLabelEnum** (4 tests):

| # | Input | Expected | Priority |
|---|-------|----------|----------|
| C5 | `'Best Price'` | `'BEST_PRICE'` | Critical |
| C6 | `'BEST PRICE'` | `'BEST_PRICE'` | High |
| C7 | `'UNKNOWN'` | throws `Error` | Critical |
| C8 | `'best price'` | `'BEST_PRICE'` | High |

**cardToProps** (3 tests):

| # | Claim | Priority |
|---|-------|----------|
| C9 | Maps all 4 terms with labels: `'Price (per unit)'`, `'Delivery Time'`, `'Payment Terms'`, `'Contract Length'` | Critical |
| C10 | `badge` is `'Recommended'` only when `card.recommended === true` | High |
| C11 | Unknown label gets fallback icon `'📋'` | Medium |

**errorMessage** (6 tests):

| # | Input | Expected | Priority |
|---|-------|----------|----------|
| C12 | `ApiError(409, {error: 'terminal'})` | `'terminal'` | Critical |
| C13 | `ApiError(409, 'some string')` | `'Request failed (409)'` | High |
| C14 | `new Error('Network fail')` | `'Network fail'` | High |
| C15 | `42` / `null` / `undefined` | `'An unexpected error occurred'` | High |
| C16 | `ApiError(422, {error: 0})` | `'0'` (falsy but present) | Medium |
| C17 | `ApiError(500, null)` | `'Request failed (500)'` | High |

### 3.4 API Client Tests

**File**: `api.test.ts` (will become `features/negotiation/api/negotiation-api.test.ts`)

Mock global `fetch`.

| # | Claim | Priority |
|---|-------|----------|
| B1 | Returns parsed JSON on 200 | Critical |
| B2 | Throws `ApiError` with status + parsed JSON detail on non-OK | Critical |
| B3 | Falls back to `response.text()` when error body isn't JSON | High |
| B4 | `getOffers` → GET `/api/negotiations/{id}/offers` | High |
| B5 | `agree` → POST with `{card_label: 'BEST_PRICE'}` | Critical |
| B6 | `secure` → POST to `/secure` | High |
| B7 | `improve` → POST to `/improve` | High |
| B8 | `endNegotiation` → POST, no body | Medium |
| B9 | `resetNegotiation` → POST to `/reset` | Medium |
| B10 | Network failure propagates as raw `Error`, not `ApiError` | High |

---

## 4. Phase 2 — Component Tests

### 4.1 OfferCard Tests

**File**: `components/OfferCard.test.tsx`

| # | Claim | Priority |
|---|-------|----------|
| F1 | Renders title and titleIcon | High |
| F2 | Badge rendered only when provided | High |
| F3 | `recommended=true` → `ring-1` class | Medium |
| F4 | `recommended=false` → `border-gray-200`, no ring | Medium |
| F5 | Detail row renders label, value, and signal color dot | High |
| F6 | Signal mapping: good→emerald, neutral→amber, weak→red | High |
| F7 | All 3 action buttons render | High |
| F8 | `disabled=true` → all buttons disabled | Critical |
| F9 | `disabled=false` → buttons enabled | Medium |
| F10 | "Agree" click calls `onAgree` once | High |
| F11 | "Secure as fallback" calls `onFallback` | High |
| F12 | "Improve terms" calls `onImprove` | High |
| F13 | Details render in array order | Medium |
| F14 | Empty details array → no crash | Medium |

### 4.2 App Phase Rendering Tests

**File**: `App.test.tsx`

| # | Claim | Priority |
|---|-------|----------|
| D1 | Loading phase renders "Loading offers..." | High |
| D2 | After getOffers resolves, one OfferCard per card | Critical |
| D3 | Agreed phase shows "Deal agreed" + all 4 terms | Critical |
| D4 | No-deal phase shows "Negotiation ended" | High |
| D5 | Error phase shows "Something went wrong" + message | Critical |
| D6 | Error phase has "Retry" and "Reset demo" buttons | High |
| D7 | Agreed phase has "Reset demo" button | Medium |
| D8 | Offers phase renders banner text | High |
| D9 | Secured offer indicator when `secured_offer` present | High |
| D10 | No indicator when `secured_offer` is null | Medium |
| D11 | Final round shows "End negotiation" button | Critical |
| D12 | Non-final round hides "End negotiation" | High |
| D13 | Acting phase disables all card buttons | Critical |
| D14 | Acting phase disables "End negotiation" | High |

---

## 5. Phase 3 — Integration Tests

### 5.1 Interaction Tests

**File**: `App.test.tsx` (interaction describe block)

| # | Claim | Priority |
|---|-------|----------|
| E1 | "Agree" calls `api.agree('demo', 'BEST_PRICE')` | Critical |
| E2 | "Secure" calls `api.secure` then `api.getOffers` in sequence | Critical |
| E3 | "Improve" calls `api.improve` when in `actions_available` | Critical |
| E4 | "Improve" is no-op when not in `actions_available` | High |
| E5 | Successful agree → "Deal agreed" screen | Critical |
| E6 | Successful end → "Negotiation ended" screen | Critical |
| E7 | Failed API → error screen with extracted message | Critical |
| E8 | "Retry" calls getOffers, returns to offers | High |
| E9 | "Reset" calls resetNegotiation then getOffers | High |
| E10 | Handlers guard against non-`offers` phase | Medium |
| E11 | Mount calls getOffers exactly once with `'demo'` | High |
| E12 | Mount failure shows error screen | Critical |

### 5.2 Edge Cases

| # | Claim | Priority |
|---|-------|----------|
| G1 | Empty `cards` array → no crash | High |
| G2 | Unknown label → fallback icon | Medium |
| G3 | Whitespace in label → throws | High |
| G4 | `secure` fails → `getOffers` NOT called | High |
| G5 | `resetNegotiation` fails → `getOffers` NOT called | Medium |
| G6 | `ApiError.name` is `'ApiError'` | Low |
| G7 | `NEGOTIATION_ID` is `'demo'` | Low |
| G8 | `cardToProps` maps signals in correct order | High |

---

## 6. Phase 4 — Refactoring

Each step produces a working app. Run tests after each step.

### Step 1: Create feature structure + move types

Create the directory tree:
```
features/negotiation/{api,hooks,components,lib}/
shared/components/
```

**Move** `types.ts` → `features/negotiation/types.ts`
- Remove duplicate `Signal` from `OfferCard.tsx`
- Add `OfferDetail` interface (currently local to OfferCard)
- All imports updated

**react-web.md compliance**: sec 6.1 (feature-scoped types)

### Step 2: Extract constants

**Create** `features/negotiation/constants.ts`:
- `LABEL_DISPLAY_TO_ENUM` (from App.tsx lines 49-53)
- `LABEL_ICON` (from App.tsx lines 55-59)
- `SIGNAL_COLOR` (from OfferCard.tsx `signalColor` lines 21-25)

**react-web.md compliance**: sec 2.1 (constants and enums)

### Step 3: Extract pure functions to lib/

**Create** `features/negotiation/lib/format.ts`:
- `toTitleCase` (from App.tsx lines 61-66)
- `toLabelEnum` (from App.tsx lines 68-75)
- `cardToProps` (from App.tsx lines 77-91)
- `errorMessage` (from App.tsx lines 93-102)

**Create** `features/negotiation/lib/reducer.ts`:
- `NegotiationView` type (exported)
- `Action` type (not exported — implementation detail)
- `reducer` function

**react-web.md compliance**: sec 6.3 (business logic in plain TS), sec 8.1 (logic out of components)

### Step 4: Create config

**Create** `front/src/config.ts`:
```ts
export const config = {
  api: {
    baseUrl: import.meta.env.VITE_API_BASE_URL ?? '',
  },
  negotiationId: import.meta.env.VITE_NEGOTIATION_ID ?? 'demo',
  appName: import.meta.env.VITE_APP_NAME ?? 'MESO Negotiator',
  isDev: import.meta.env.DEV,
  isProd: import.meta.env.PROD,
} as const;
```

**Create** `front/.env` and `front/.env.example`.

**react-web.md compliance**: sec 2.3 (single config, env-driven)

### Step 5: Move API client

**Move** `api.ts` → `features/negotiation/api/negotiation-api.ts`
- Import `config.api.baseUrl` and prepend to fetch paths
- Export `ApiError` class

**react-web.md compliance**: sec 6.3 (API calls in feature api/ folder)

### Step 6: Extract useNegotiation hook

**Create** `features/negotiation/hooks/useNegotiation.ts`:
- Imports reducer from `../lib/reducer`
- Imports API functions from `../api/negotiation-api`
- Imports `config.negotiationId` from config
- Contains `useReducer` + `useEffect` for initial load
- Contains all handler functions (handleAgree, handleFallback, handleImprove, handleEndNegotiation, handleReset, handleRetry)

**Returns**:
```ts
{
  view: NegotiationView
  handleAgree: (card: Card) => void
  handleFallback: (card: Card) => void
  handleImprove: (card: Card) => void
  handleEndNegotiation: () => void
  handleReset: () => void
  handleRetry: () => void
}
```

**react-web.md compliance**: sec 1.3 (container vs presentational), sec 7.1 (custom hooks)

### Step 7: Extract phase components

All presentational, all under 60 lines each.

| Component | Location | Props | Lines |
|-----------|----------|-------|-------|
| `LoadingPhase` | `features/negotiation/components/` | none | ~10 |
| `AgreedPhase` | `features/negotiation/components/` | `{ terms: Terms; onReset: () => void }` | ~35 |
| `NoDealPhase` | `features/negotiation/components/` | `{ onReset: () => void }` | ~20 |
| `ErrorPhase` | `features/negotiation/components/` | `{ message: string; onRetry: () => void; onReset: () => void }` | ~25 |
| `OffersPhase` | `features/negotiation/components/` | `{ data; isActing; onAgree; onFallback; onImprove; onEndNegotiation }` | ~60 |
| `StatusBadge` | `shared/components/` | `{ text: string }` | ~10 |

**Move** `OfferCard.tsx` → `features/negotiation/components/OfferCard.tsx`
- Import `Signal`, `OfferDetail` from `../types`
- Import `SIGNAL_COLOR` from `../constants`

**react-web.md compliance**: sec 1.1 (SRP, under 200 lines), sec 1.4 (split at section comments), sec 1.5 (narrow props)

### Step 8: Rewrite App.tsx

**Final `App.tsx`** (~40 lines):
- Imports `useNegotiation` from feature hook
- Imports phase components from feature components
- Switch on `view.phase`, delegate to appropriate component

**react-web.md compliance**: sec 1.3 (thin glue), sec 1.4 (no section comments)

### Step 9: Create barrel export

**Create** `features/negotiation/index.ts`:
```ts
export { useNegotiation } from './hooks/useNegotiation';
export type { NegotiationView } from './lib/reducer';
export type { Card, Terms, OffersResponse } from './types';
```

Only at the feature boundary, not at every directory level.

**react-web.md compliance**: sec 6.2 (barrel exports at feature boundary)

### Step 10: Move tests

Move test files from pre-refactor locations to feature structure:
- `App.reducer.test.ts` → `features/negotiation/lib/reducer.test.ts`
- `App.helpers.test.ts` → `features/negotiation/lib/format.test.ts`
- `api.test.ts` → `features/negotiation/api/negotiation-api.test.ts`
- `OfferCard.test.tsx` → `features/negotiation/components/OfferCard.test.tsx`
- `App.test.tsx` stays at root (tests the assembled app)

Update imports. Run all tests — must stay green.

---

## 7. Compliance Matrix

Post-refactoring compliance with every applicable react-web.md section:

| Section | Rule | After Refactoring |
|---------|------|--------------------|
| 1.1 | SRP, components under 200 lines | All components under 60 lines. App.tsx ~40 lines. |
| 1.2 | Composition over inheritance | Card uses `children`-style slot pattern already |
| 1.3 | Container vs presentational | `useNegotiation` hook (container) + phase components (presentational) |
| 1.4 | Split at section comments | 5 `// Phase:` comments → 5 separate components |
| 1.5 | Narrow props | Each phase component accepts only what it renders |
| 1.6 | No prop drilling | App passes directly to children, zero intermediate levels |
| 2.1 | Constants and enums | `constants.ts` for all label maps, signal colors |
| 2.3 | Single config from env | `config.ts` with `import.meta.env` |
| 2.4 | No magic strings/numbers | `NEGOTIATION_ID` from config, all maps in constants |
| 5.1 | State colocation | State machine in hook, closest to where it's used |
| 5.3 | State colocation | No top-level provider; state in feature hook |
| 6.1 | Feature-based folders | `features/negotiation/` with api/hooks/components/lib |
| 6.2 | Barrel exports | `index.ts` at feature boundary only |
| 6.3 | Separation of concerns | API in api/, logic in lib/, display in components/ |
| 7.1 | Custom hooks | `useNegotiation` extracts all data-fetching logic |
| 7.3 | Handle all states | loading/error/offers/agreed/no_deal all handled |
| 7.4 | Accessibility | Existing buttons use `<button>` with `type`, SVGs have `aria-hidden` |
| 7.6 | Event naming | Props: `onAgree`, `onReset`. Handlers: `handleAgree`, `handleReset` |
| 8.1 | Business logic out of components | `format.ts` and `reducer.ts` have zero React imports |
| 8.6 | No `any` | All types explicit; `unknown` used for error handling |

---

## 8. Trade-offs

| Decision | What Gets Worse | Why Acceptable |
|----------|----------------|----------------|
| Feature folders for a single feature | More directories than flat structure | Scales when features are added. react-web.md is explicit about this. Migration cost from flat→feature is higher than starting with feature. |
| No TanStack Query | Manual useEffect, no caching | Single page, single data source. useNegotiation encapsulates all fetching. Swap in TanStack Query later by changing one file. |
| No global state library | N/A | Zero prop drilling. App passes directly to children. |
| Tests before refactoring | Slower start | Pure-function tests (Phase 1) take minimal effort and provide safety net for all subsequent steps. |
| Barrel exports only at feature boundary | Slightly longer import paths inside the feature | Avoids circular dependency risk and tree-shaking issues (sec 6.2 recommendation) |

---

## 9. TODO

- [ ] **`onImprove` no-op UX** — When `actions_available` does not include `'improve'`, the "Improve terms" link is clickable but silently does nothing (`onImprove={() => {}}`). Should be hidden or visually disabled. Current behavior preserved during refactor.
- [ ] **`toLabelEnum` contract fragility** — Backend sends display strings (`"Best Price"`), frontend uppercases and maps to enum. If backend changes format, frontend breaks silently. Consider backend sending enum directly, or add a contract test.
- [ ] **Fetch cleanup** — Current `useEffect` data fetching has no `AbortController` cleanup (sec 8.3). Low risk for single mount, but should be added when scope allows.
