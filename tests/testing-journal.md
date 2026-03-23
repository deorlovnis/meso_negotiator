# Testing Journal

## Session: 2026-03-23 — Frontend Component and Integration Tests

### Claims Analyzed

**OfferCard component (14 claims — F1 through F14):**
- F1: Renders title and titleIcon props as visible text
- F2: Badge rendered only when `badge` prop provided
- F3: `recommended=true` applies `ring-1` CSS class to card root
- F4: `recommended=false` applies `border-gray-200`, no ring
- F5: Detail row renders label, value, and signal color dot
- F6: Signal mapping: good -> bg-emerald-400, neutral -> bg-amber-400, weak -> bg-red-400
- F7: All 3 action buttons render ("Agree", "Secure as fallback", "Improve terms")
- F8: `disabled=true` disables all buttons
- F9: `disabled=false` enables all buttons
- F10: "Agree" click calls `onAgree` once
- F11: "Secure as fallback" calls `onFallback`
- F12: "Improve terms" calls `onImprove`
- F13: Details render in array order
- F14: Empty details array does not crash

**App component — phase rendering (14 claims — D1 through D14):**
- D1: Loading phase renders "Loading offers..."
- D2: After getOffers resolves, one OfferCard per card
- D3: Agreed phase shows "Deal agreed" + all 4 terms
- D4: No-deal phase shows "Negotiation ended"
- D5: Error phase shows "Something went wrong" + message
- D6: Error phase has "Retry" and "Reset demo" buttons
- D7: Agreed phase has "Reset demo" button
- D8: Offers phase renders banner text
- D9: Secured offer indicator when `secured_offer` present
- D10: No indicator when `secured_offer` is null
- D11: Final round shows "End negotiation" button
- D12: Non-final round hides "End negotiation"
- D13: Acting phase disables all card buttons
- D14: Acting phase disables "End negotiation"

**App component — interactions (10 claims — E1 through E12, minus E4):**
- E1: "Agree" calls `api.agree('demo', 'BEST_PRICE')`
- E2: "Secure" calls `api.secure` then `api.getOffers` in sequence
- E3: "Improve" calls `api.improve` when in `actions_available`
- E5: Successful agree transitions to "Deal agreed" screen
- E6: Successful end transitions to "Negotiation ended" screen
- E7: Failed API call shows error screen with extracted message
- E8: "Retry" calls getOffers, returns to offers
- E9: "Reset" calls resetNegotiation then getOffers
- E10: Handlers guard against non-offers phase
- E11: Mount calls getOffers exactly once with 'demo'
- E12: Mount failure shows error screen

**App component — edge cases (4 claims — G1, G2, G4, G5):**
- G1: Empty cards array does not crash
- G2: Unknown label uses fallback icon
- G4: `secure` fails -> `getOffers` NOT called
- G5: `resetNegotiation` fails -> `getOffers` NOT called

### Existing Test Audit

No existing tests prior to this session. This is the first test suite for the frontend.

| Error Category | Test Count | Blind Spot? |
|----------------|-----------|-------------|
| Input/output errors | 14 | No |
| Logic errors | 14 | No |
| Computation errors | 1 (F6) | Partial — signal mapping only |
| Interface errors | 6 | No |
| Data errors | 3 (F14, G1, G2) | Partial — more boundary data could be tested |
| Configuration errors | 0 | Yes — env vars, base URL not tested here |
| Integration errors | 4 (G4, G5, E7, E12) | No — API failure chains well covered |
| Regression errors | 0 | N/A — no prior bugs to regress |

### Tests Written

| Test | Claim Targeted | Error Category | Risk Level |
|------|---------------|----------------|------------|
| **OfferCard.test.tsx** (16 tests) | | | |
| F1: renders title text and titleIcon | F1 | Input/output | L |
| F2: renders badge when provided | F2 | Logic | L |
| F2 negative: omits badge when not provided | F2 | Logic | L |
| F3: recommended=true applies ring-1 class | F3 | Logic | M |
| F4: recommended=false applies border-gray-200, no ring | F4 | Logic | M |
| F5: renders label, value, and signal color dot | F5 | Input/output | M |
| F6: signal mapping (good/neutral/weak) | F6 | Computation | M |
| F7: renders all 3 action buttons | F7 | Input/output | M |
| F8: disabled=true disables all buttons | F8 | Logic | H |
| F9: disabled=false enables all buttons | F9 | Logic | M |
| F10: Agree calls onAgree once | F10 | Interface | H |
| F11: Secure calls onFallback | F11 | Interface | H |
| F12: Improve calls onImprove | F12 | Interface | H |
| F13: details render in array order | F13 | Input/output | L |
| F14: empty details array no crash | F14 | Data | M |
| **App.test.tsx** (28 tests) | | | |
| D1: loading phase renders text | D1 | Input/output | L |
| D2: one OfferCard per card | D2 | Input/output | H |
| D3: agreed phase content | D3 | Input/output | H |
| D4: no-deal phase content | D4 | Input/output | M |
| D5: error phase content | D5 | Input/output | H |
| D6: error phase buttons | D6 | Input/output | M |
| D7: agreed phase reset button | D7 | Input/output | L |
| D8: banner text | D8 | Input/output | L |
| D9: secured offer indicator present | D9 | Logic | M |
| D10: no indicator when null | D10 | Logic | M |
| D11: final round end button | D11 | Logic | H |
| D12: non-final hides end button | D12 | Logic | H |
| D13: acting disables buttons | D13 | Logic | H |
| D14: acting disables end button | D14 | Logic | H |
| E1: agree API arguments | E1 | Interface | H |
| E2: secure then getOffers chain | E2 | Interface | H |
| E3: improve API call | E3 | Interface | H |
| E5: agree -> agreed screen | E5 | Logic | H |
| E6: end -> no-deal screen | E6 | Logic | H |
| E7: failed API -> error screen | E7 | Integration | H |
| E8: retry recovery | E8 | Logic | H |
| E9: reset recovery | E9 | Logic | H |
| E10: phase guard | E10 | Logic | H |
| E11: mount calls getOffers once | E11 | Interface | H |
| E12: mount failure | E12 | Integration | H |
| G1: empty cards no crash | G1 | Data | M |
| G2: unknown label fallback icon | G2 | Logic | M |
| G4: secure fail skips getOffers | G4 | Integration | H |
| G5: reset fail skips getOffers | G5 | Integration | H |

### Verdicts

All 44 claims: **NOT YET FALSIFIED** — tests pass against the current implementation.

Notable finding during test development:
- D9 initially failed due to `$12.50/k` appearing twice in the DOM (once in the secured offer indicator, once in the card detail row). Fixed by scoping the assertion to the indicator paragraph's `textContent` rather than a global text search. This is not a bug in the component — the duplication is expected when the secured card is also displayed.

### Remaining Blind Spots

1. **Configuration errors**: Base URL, proxy configuration, environment-dependent behavior not tested at this layer.
2. **Concurrency**: Rapid successive clicks (double-click on Agree before first resolves) — partially covered by the acting-phase disable tests, but not explicitly tested as a race condition.
3. **ApiError with structured `detail` object**: The `errorMessage` helper has a branch for `detail.error` extraction from ApiError — better tested in unit tests for the helper function.
4. **E4 (improve no-op)**: Skipped per instructions — the no-op is implemented as passing `() => {}` when improve is not in `actions_available`.
5. **G3, G6, G7, G8**: Deferred to unit tests per instructions.

---

## Session: 2026-03-23 — Frontend Unit Tests (Phase 1 of Refactoring Plan, Sections 3.2-3.4)

### Scope

Unit tests for all pure functions and the state machine in the React frontend,
per the refactoring plan sections 3.2, 3.3, and 3.4. These serve as a safety
net before the planned refactoring in Phase 4.

### Claims Analyzed

**Reducer (App.reducer.test.ts) — 8 claims:**
- A1: OFFERS_LOADED from any state produces {phase: 'offers', data}
- A2: OFFERS_UPDATED produces same shape as OFFERS_LOADED
- A3: ACTION_START preserves data and pendingAction
- A4: AGREED transitions to {phase: 'agreed', terms}
- A5: NO_DEAL transitions to {phase: 'no_deal'}
- A6: ERROR from any state produces {phase: 'error', message}
- A7: Reducer is pure — previous state is never mutated
- A8: pendingAction string preserved verbatim

**Helpers (App.helpers.test.ts) — 17 claims:**
- C1-C4: toTitleCase string transformation (4 cases)
- C5-C8: toLabelEnum lookup and error handling (4 cases)
- C9-C11: cardToProps field mapping, badge, icon fallback (3 cases)
- C12-C17: errorMessage extraction chain across ApiError, Error, and unknown (6 cases)

**API client (api.test.ts) — 10 claims:**
- B1: Returns parsed JSON on 200
- B2: Throws ApiError with status + parsed JSON detail on non-OK
- B3: Falls back to response.text() when error body isn't JSON
- B4-B9: Each API function hits the correct URL/method/body
- B10: Network failure propagates as raw Error, not ApiError

### Existing Test Audit

Prior to this session, the project had component and integration tests
(App.test.tsx, OfferCard.test.tsx) but no unit tests for the pure functions
and state machine that those components depend on.

| Error Category | Test Count (new) | Blind Spot? |
|---------------|-----------------|-------------|
| Input/output errors | 14 | No |
| Logic errors | 32 | No |
| Computation errors | 4 | No |
| Interface errors | 22 | No |
| Data errors | 12 | No |
| Configuration errors | 0 | Yes — no tests for NEGOTIATION_ID or env config |
| Integration errors | 0 | Yes — no end-to-end API contract tests (unit mocks only) |
| Regression errors | 0 | N/A — no known defects to regress |

### Tests Written

| Test File | Test Count | Claims Targeted | Error Categories |
|-----------|-----------|----------------|-----------------|
| App.reducer.test.ts | 27 | A1-A8 | Logic, Data |
| App.helpers.test.ts | 25 | C1-C17 | Logic, Input/output, Computation, Interface |
| api.test.ts | 15 | B1-B10 | Interface |
| **Total** | **67** | | |

### Risk Census

| Claim | Test Idea | Risk (1-10) | Error Category | In Automation? |
|-------|-----------|-------------|----------------|----------------|
| A1 | OFFERS_LOADED from error phase (retry path) | 8 | Logic | Yes |
| A6 | ERROR from any phase | 7 | Logic | Yes |
| A7 | Reducer purity (immutability) | 7 | Data | Yes |
| C7 | toLabelEnum throws on unknown | 8 | Input/output | Yes |
| C12 | errorMessage extracts error field from ApiError | 8 | Logic | Yes |
| C16 | errorMessage with falsy error value (0) | 7 | Logic | Yes |
| B2 | ApiError thrown on non-OK response | 9 | Interface | Yes |
| B3 | Text fallback on non-JSON error body | 7 | Interface | Yes |
| B10 | Network error vs ApiError discrimination | 8 | Interface | Yes |
| --- cut line --- | | | | |
| C3 | toTitleCase empty string | 3 | Input/output | Yes |
| C9 | cardToProps label ordering | 4 | Interface | Yes |
| B8 | endNegotiation no body | 4 | Interface | Yes |

### Verdicts

All 35 claims: **NOT YET FALSIFIED** — each claim survived adversarial testing.

Notable observations:
- The reducer ignores `_state` entirely (leading underscore convention). Every
  action fully determines the next state. This is a deliberate design choice
  that simplifies the state machine but means invalid transitions are accepted
  silently (e.g., AGREED from loading phase). Acceptable because the component
  guards against invalid dispatches in the handler functions.
- `errorMessage` correctly handles the instanceof ordering issue: ApiError
  extends Error, so the ApiError check must come first. Verified with an
  explicit test that confirms both instanceof checks pass on an ApiError
  instance, but the function returns the extracted error field (not err.message).
- `fetchApi` error path tries `response.json()` first, catches, then falls
  back to `response.text()`. The `detail` field can be any type (object,
  string, null). This is correctly reflected in the `detail: unknown` typing.
- `endNegotiation` and `resetNegotiation` send POST with Content-Type header
  but no body property. This is intentional — the backend only needs the
  negotiation ID from the URL path.

### Remaining Blind Spots

1. **Configuration errors**: No tests for `NEGOTIATION_ID` constant value or
   env-driven config (planned in refactoring Phase 4, Step 4).
2. **Integration contract tests**: All API tests use mocked fetch. No tests
   verify the actual backend contract matches the frontend expectations.
   Flagged in refactoring plan TODO as "toLabelEnum contract fragility".
3. **AbortController cleanup**: The useEffect has no cleanup — flagged in the
   refactoring plan TODO but not testable at the unit level.
4. **Concurrent dispatch safety**: Rapid successive dispatches to the reducer
   are safe (pure function, no shared mutable state), but the async handler
   chains in the component could theoretically interleave. Partially covered
   by the acting-phase disable tests in App.test.tsx.

---

## Session: 2026-03-23 -- Backend Phase 1: Test Foundation (F1-F14)

### Scope

Implementing Phase 1 (Test Foundation) from docs/backend-refactoring-plan.md:
shared factories, conftest fixtures, safety-net tests, and factory migration.

### Claims Analyzed

**Shared Factories (F1-F5):**
- F1: make_config(**overrides) returns dict[str, TermConfig] with defaults matching demo seed
- F2: make_negotiation(**overrides) returns Negotiation in PENDING state
- F3: make_active_negotiation(**overrides) activates + sets stub MESO set
- F4: make_meso_set(**overrides) returns deterministic MesoSet
- F5: make_weights(**overrides) auto-normalizes to sum=1.0

**Conftest Fixtures (F7-F10):**
- F7: client fixture (TestClient with fresh repo + dependency override)
- F8: mock_repo fixture (MagicMock with NegotiationRepository spec)
- F9: seeded_client fixture (seeds PENDING negotiation via factory)
- F10: terminal_client fixture (pre-advanced to ACCEPTED state)

**Factory Migration (F6):**
- F6: Migrate test_negotiation_state.py and test_api_integration.py to shared factories

**Safety-Net Tests (F11-F14):**
- F11: server.py seed config vs routes.py reset config equivalence (EXPECTED FAIL)
- F12: InMemoryNegotiationRepository satisfies NegotiationRepository protocol
- F13: All 5 routes return correct response_model Pydantic shapes
- F14: Snapshot test of GET /offers response for known seed

### Existing Test Audit

| Error Category | Test Count (before) | Blind Spot? |
|---------------|-------------------|-------------|
| Input/output errors | 8 | No |
| Logic errors | 30 | No |
| Computation errors | 17 | No |
| Interface errors | 4 | Yes -- no protocol conformance test |
| Data errors | 6 | No |
| Configuration errors | 0 | Yes -- no config drift detection |
| Integration errors | 38 | No |
| Regression errors | 0 | Yes -- no snapshot tests |

### Tests Written

| Test | Claim Targeted | Error Category | Risk Level |
|------|---------------|----------------|------------|
| **test_safety_net.py** (13 tests) | | | |
| test_seed_config_matches_reset_config | F11 "seed and reset produce equivalent negotiations" | Configuration | H (xfail) |
| test_seed_weights_match_reset_weights | F11 "seed and reset use same weight vectors" | Configuration | H (xfail) |
| test_inmemory_repo_satisfies_negotiation_repository_protocol | F12 "InMemoryRepo satisfies protocol" | Interface | M |
| test_inmemory_repo_get_raises_keyerror_for_missing_id | F12 "get() raises KeyError for missing ID" | Interface | M |
| test_inmemory_repo_is_runtime_checkable_against_protocol | F12 "structural subtyping holds" | Interface | M |
| test_get_offers_response_matches_offers_response_model | F13 "GET /offers validates against OffersResponse" | Integration | H |
| test_agree_response_matches_agree_response_model | F13 "POST /agree validates against AgreeResponse" | Integration | H |
| test_secure_response_matches_secure_response_model | F13 "POST /secure validates against SecureResponse" | Integration | H |
| test_improve_response_matches_offers_response_model | F13 "POST /improve validates against OffersResponse" | Integration | H |
| test_end_response_matches_end_response_model | F13 "POST /end validates against EndResponse" | Integration | H |
| test_snapshot_structure_matches_known_seed | F14 "GET /offers structure for known seed" | Regression | H |
| test_snapshot_term_formatting_conventions | F14 "term formatting conventions" | Regression | H |
| test_snapshot_banner_is_nonempty_string | F14 "banner is non-empty string" | Regression | L |

### Risk Census

| Claim | Test Idea | Risk (1-10) | Error Category | In Automation? |
|-------|-----------|-------------|----------------|----------------|
| F11 | Compare TermConfig dicts from server.py seed and routes.py reset | 9 | Configuration | Yes (xfail) |
| F14 | Snapshot GET /offers response structure for known seed | 9 | Regression | Yes |
| F13 | Pydantic model_validate on all 5 route responses | 8 | Integration | Yes |
| F12 | Protocol conformance: save+get roundtrip, KeyError on missing | 7 | Interface | Yes |
| F5 | make_weights auto-normalization | 5 | Computation | Exercised by F2/F3 |
| --- cut line --- | | | | |
| F1-F4 | Factory defaults match demo seed | 4 | Data | Exercised by all tests |
| F6 | Migration does not break existing tests | 3 | Regression | Verified by full suite |

### Verdicts

- **F1** (make_config): NOT YET FALSIFIED -- factory produces dict matching server.py seed values; all existing tests pass after migration.
- **F2** (make_negotiation): NOT YET FALSIFIED -- factory produces PENDING negotiation with round=0, matching server.py seed.
- **F3** (make_active_negotiation): NOT YET FALSIFIED -- factory activates and sets MESO set; all state machine tests pass.
- **F4** (make_meso_set): NOT YET FALSIFIED -- factory produces deterministic MesoSet with correct labels.
- **F5** (make_weights): NOT YET FALSIFIED -- auto-normalization produces valid Weights (sum=1.0).
- **F6** (migration): NOT YET FALSIFIED -- 202 tests pass after replacing local helpers with shared factories.
- **F7** (client fixture): NOT YET FALSIFIED -- conftest client fixture works across test_api_integration.py.
- **F8** (mock_repo fixture): NOT YET FALSIFIED -- fixture returns MagicMock with NegotiationRepository spec.
- **F9** (seeded_client): NOT YET FALSIFIED -- seeds PENDING negotiation via factory.
- **F10** (terminal_client): NOT YET FALSIFIED -- pre-advances to ACCEPTED state.
- **F11** (config drift): **FALSIFIED** -- seed uses TermConfig(opening=11.50, target=12.50, walk_away=14.50) for price; reset uses TermConfig(opening=150.0, target=120.0, walk_away=100.0). These are fundamentally different negotiations. Marked xfail(strict=True).
- **F12** (protocol conformance): NOT YET FALSIFIED -- InMemoryRepo has get/save, roundtrips correctly, raises KeyError on missing ID.
- **F13** (response shapes): NOT YET FALSIFIED -- all 5 route responses validate against their Pydantic models.
- **F14** (snapshot): NOT YET FALSIFIED -- GET /offers response has expected structure, formatting, and metadata.

### Key Finding: Config Drift Bug (F11)

The implicit claim that "reset returns the negotiation to its initial state" is
**FALSIFIED**. Evidence:

| Term | server.py seed | routes.py reset |
|------|---------------|-----------------|
| price.opening | 11.50 | 150.0 |
| price.target | 12.50 | 120.0 |
| price.walk_away | 14.50 | 100.0 |
| payment.weight | 0.25 | 0.2 |
| delivery.weight | 0.20 | 0.2 |
| contract.weight | 0.15 | 0.2 |

This means clicking "Reset" in the frontend produces a completely different
negotiation than the one shown on first load. Handoff to coder for fix.

### Factory Migration Notes (F6)

Key change during migration: the old `_make_negotiation()` in
test_negotiation_state.py set `round=1` for a PENDING negotiation, but server.py
seeds with `round=0`. The factory now uses `round=0` (matching the demo seed),
and the test `test_initial_round_is_one` was renamed to
`test_initial_round_is_zero_before_activation` with assertion updated to 0.
This is not a behavioral change -- the old test was testing its own factory's
default, not the domain invariant. The domain invariant is: activate() sets
round to 1.

### Remaining Blind Spots

1. **F8 mock_repo not yet exercised** -- the fixture exists but no use-case
   unit tests consume it yet (planned for Phase 2).
2. **F9/F10 fixtures not yet consumed** -- seeded_client and terminal_client
   are available but no new tests use them yet. Existing tests define their
   own local fixtures. These will be consumed in Phase 2/3.
3. **Reset endpoint not tested** -- the /reset route has no integration tests.
   Planned for Phase 3.
4. **MESO generator factory** -- test_meso_generator.py still uses its own
   BACKGROUND_CONFIG constant instead of the shared factory. Migration deferred
   as the constant serves as an independent verification of the values.
