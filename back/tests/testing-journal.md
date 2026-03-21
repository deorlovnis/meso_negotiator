# Testing Journal -- MESO Negotiation Engine

## Session: 2026-03-21

### Objective

Build the initial unit test suite (TDD red phase) for the MESO Negotiation Engine backend. Production code does not exist yet. Tests are designed to fail on import and then guide implementation.

### Claims Analyzed

Extracted from core-loop.feature (74 scenarios) and ARCHITECTURE.md:

1. **MAUT utility = 0.0 at walk-away, 1.0 at target** (section 14)
2. **MAUT formula: weighted sum of clamped per-term achievements** (section 14)
3. **Weights must sum to 1.0 and be non-negative** (types.py contract)
4. **Concession curve: round 1 near opening, final round near walk-away** (section 15)
5. **Concession is monotonically decreasing** (section 6)
6. **Boulware shape: concedes less early, more late** (section 6)
7. **Opponent model starts uniform (0.25 each)** (section 13)
8. **Improve shifts correct dimension weight upward** (section 5)
9. **Weights always sum to 1.0 after any update** (section 13)
10. **No weight ever drops below 0.0** (section 13)
11. **Secure sets utility floor without changing weights** (section 4)
12. **Agree reinforces all weights** (section 13)
13. **Diminishing returns on repeated improve** (architecture: delta formula)
14. **MESO returns exactly 3 cards** (section 1)
15. **3 cards have equal operator utility within 0.02** (section 1)
16. **All offers respect walk-away limits** (section 8)
17. **BEST_PRICE has lowest price, FASTEST_PAYMENT has fastest payment** (section 8)
18. **MOST_BALANCED has no extreme on any single term** (section 8)
19. **No two cards identical across all 4 terms** (section 14)
20. **Negotiation starts in Pending state** (section 12)
21. **Valid transitions: Pending->Active, Active->Accepted, Active->No Deal** (section 12)
22. **Accepted and No Deal are terminal** (section 12)
23. **Improve advances round, Secure does not, Agree does not** (sections 6, 16)
24. **Improve unavailable on final round** (section 6)
25. **Secured offer preserved across rounds, not auto-accepted** (sections 4, 7)

### Existing Test Audit

| Error Category | Test Count | Blind Spot? |
|---------------|-----------|-------------|
| Input/output errors | 4 | No -- boundary values, clamping tests |
| Logic errors | 18 | No -- state machine, card labels, transitions |
| Computation errors | 14 | No -- MAUT formula, concession curve, weight math |
| Interface errors | 3 | Partial -- Weights validation, but no API contract tests yet |
| Data errors | 6 | Partial -- secured offer, round counter, but no persistence tests |
| Configuration errors | 0 | Yes -- no tests for invalid configs (missing terms, bad round limits) |
| Integration errors | 0 | Yes -- unit tests only; BDD step defs are stubs pending production code |
| Regression errors | 0 | Yes -- no production code exists yet, so no regressions to guard |

### Tests Written

| Test | Claim Targeted | Error Category | Risk Level |
|------|---------------|----------------|------------|
| `test_maut.TestMautBoundaryValues.test_all_terms_at_walk_away_gives_zero` | MAUT = 0.0 at walk-away | Boundary | H |
| `test_maut.TestMautBoundaryValues.test_all_terms_at_target_gives_one` | MAUT = 1.0 at target | Boundary | H |
| `test_maut.TestMautBoundaryValues.test_values_beyond_target_are_clamped_to_one` | Clamping above target | Computation | H |
| `test_maut.TestMautBoundaryValues.test_values_beyond_walk_away_are_clamped_to_zero` | Clamping below walk-away | Computation | H |
| `test_maut.TestMautConcreteFormula.test_section14_concrete_verification` | Formula correctness | Computation | H |
| `test_maut.TestMautConcreteFormula.test_single_term_at_midpoint_others_at_walk_away` | Per-term isolation | Computation | M |
| `test_maut.TestMautConcreteFormula.test_uniform_weights_equal_contribution` | Uniform weight behavior | Computation | M |
| `test_maut.TestMautWeightValidation.test_weights_not_summing_to_one_raises_error` | Weight sum constraint | Interface | H |
| `test_maut.TestMautWeightValidation.test_negative_weight_raises_error` | Non-negative constraint | Interface | H |
| `test_maut.TestMautWeightValidation.test_zero_weight_is_valid` | Zero weight edge case | Boundary | M |
| `test_maut.TestMautWeightValidation.test_all_weight_on_single_term` | Extreme skew | Computation | M |
| `test_maut.TestMautEdgeCases.test_target_equals_walk_away_single_term` | Division by zero | Computation | H |
| `test_maut.TestMautEdgeCases.test_floating_point_precision_near_boundary` | Float precision | Computation | M |
| `test_concession_curve.TestConcessionCurveBoundaries.test_round_one_near_opening_utility` | Round 1 near opening | Boundary | H |
| `test_concession_curve.TestConcessionCurveBoundaries.test_final_round_near_walkaway_utility` | Final round at walk-away | Boundary | H |
| `test_concession_curve.TestConcessionCurveBoundaries.test_round_zero_gives_opening_utility` | Round 0 boundary | Boundary | M |
| `test_concession_curve.TestConcessionCurveMonotonicity.test_monotonic_decrease_across_all_rounds` | Monotonic decrease | Computation | H |
| `test_concession_curve.TestConcessionCurveMonotonicity.test_boulware_concedes_less_early_more_late` | Boulware shape | Computation | H |
| `test_concession_curve.TestConcessionCurveBetaVariants.test_beta_one_gives_linear_concession` | Beta=1 is linear | Computation | M |
| `test_concession_curve.TestConcessionCurveBetaVariants.test_high_beta_holds_firm_longer` | High beta behavior | Computation | M |
| `test_concession_curve.TestConcessionCurveBetaVariants.test_beta_less_than_one_gives_conceder_curve` | Beta<1 conceder | Computation | L |
| `test_concession_curve.TestConcessionCurveWithNonZeroWalkaway.*` (3 tests) | Non-zero walkaway offset | Computation | M |
| `test_opponent_model.TestOpponentModelInitialization.*` (3 tests) | Uniform init, no floor | Logic | M |
| `test_opponent_model.TestImproveShiftsCorrectDimension.*` (4 tests) | Correct dimension shift | Logic | H |
| `test_opponent_model.TestWeightsAlwaysSumToOne.*` (5 tests) | Sum-to-one invariant | Computation | H |
| `test_opponent_model.TestNoNegativeWeights.*` (4 tests) | Non-negativity invariant | Computation | H |
| `test_opponent_model.TestSecureSetsFloor.*` (3 tests) | Secure floor behavior | Logic | M |
| `test_opponent_model.TestAgreeReinforces.*` (1 test) | Agree reinforcement | Logic | M |
| `test_opponent_model.TestDiminishingReturns.*` (2 tests) | Delta formula | Computation | H |
| `test_meso_generator.TestMesoReturnsThreeCards.*` (2 tests) | 3 cards returned | Logic | H |
| `test_meso_generator.TestEqualOperatorUtility.*` (3 tests) | Equal utility within 0.02 | Computation | H (9/10) |
| `test_meso_generator.TestWalkAwayLimitsRespected.*` (2 tests) | Walk-away compliance | Boundary | H (9/10) |
| `test_meso_generator.TestDistinctTermDistributions.*` (4 tests) | Card differentiation | Logic | H |
| `test_meso_generator.TestMesoWithExtremeInputs.*` (3 tests) | Degenerate inputs | Computation | M |
| `test_negotiation_state.TestInitialState.*` (4 tests) | Initial state correctness | Logic | M |
| `test_negotiation_state.TestValidTransitions.*` (3 tests) | Valid state transitions | Logic | H |
| `test_negotiation_state.TestTerminalStatesRejectActions.*` (7 tests) | Terminal state finality | Logic | H (7/10) |
| `test_negotiation_state.TestInvalidTransitions.*` (4 tests) | Skip-state prevention | Logic | H |
| `test_negotiation_state.TestRoundProgression.*` (7 tests) | Round advancement rules | Logic | H |
| `test_negotiation_state.TestSecuredOfferManagement.*` (3 tests) | Secured offer semantics | Data | M |
| `test_negotiation_state.TestAgreedTermsRecording.*` (1 test) | Agree records terms | Data | M |

### Risk Census

| Claim | Test Idea | Risk (1-10) | Error Category | In Automation? |
|-------|-----------|-------------|----------------|----------------|
| 3 MESO cards have equal operator utility within 0.02 | Generate set, check max utility delta | 9 | Computation | Unit |
| No offer violates walk-away limits | Assert all terms within bounds | 9 | Boundary | Unit |
| Opponent weights never go negative | 4x/10x improve on same dimension | 8 | Computation | Unit |
| Opponent weights always sum to 1.0 | After every update type | 8 | Computation | Unit |
| MAUT = 0.0 at walk-away, 1.0 at target | Direct computation | 7 | Boundary | Unit |
| Accepted/No-Deal states are terminal | Attempt action on terminal | 7 | Logic | Unit |
| Concession follows Boulware curve | Round-over-round comparison | 7 | Computation | Unit |
| Improve advances round, Secure does not | Action type -> round check | 6 | Logic | Unit |
| Only one secured offer at a time | Secure A then B: A replaced | 6 | Data | Unit |
| Secured offer preserved across rounds | Secure round 2, check round 4 | 6 | Data | Unit |
| Opening round deterministic | Same config -> same offers | 5 | Data | Not yet |
| ---- CUT LINE ---- | | | | |
| API response excludes internal fields | Response schema assertion | 5 | Interface | Not yet (API layer) |
| Recommended badge on Most Balanced | UI rendering | 3 | Config | Frontend |
| Page title text | Static string | 2 | Config | Frontend |

### Verdicts

All claims are NOT YET FALSIFIED -- production code does not exist. Tests are written to fail on import (TDD red phase). When production code is implemented, tests will either:
- Pass: claim survives this round of falsification attempts
- Fail: claim is falsified, implementation needs fixing

### Remaining Blind Spots

1. **Configuration errors**: No tests for invalid TermConfig (e.g., target == walk_away for all terms, negative round limits, zero max_rounds)
2. **Integration errors**: BDD step definitions are scaffolded but not executable. Pending production code.
3. **API contract tests**: Not written yet -- requires FastAPI layer. High priority for ISP verification.
4. **Concurrency/idempotency**: Double-click Improve protection (section 11) not testable at unit level.
5. **Property-based testing**: The MESO generator would benefit from hypothesis-style property tests (generate 1000 sets, check all invariants). Deferred to next session.
6. **Concession formula interpretation**: The documented formula with beta > 1 may actually produce Conceder behavior, not Boulware. Test `test_boulware_concedes_less_early_more_late` will reveal this when production code exists. If the test fails, the formula or documentation needs correction.

---

## Session: 2026-03-21 (HTTP Integration Tests)

### Objective

Write HTTP-level integration tests exercising the FastAPI endpoints via TestClient. Fill the "Integration errors" and "API contract" blind spots from the prior session.

### Claims Analyzed

Extracted from routes.py, use cases, and the user-provided spec:

1. **GET /offers returns 3 cards with label, recommended, terms (4 fields), signals (4 fields)**
2. **Exactly one card is recommended (MOST BALANCED)**
3. **Terms are display-formatted strings (not raw numbers)**
4. **is_first_visit is true on first GET, false after**
5. **POST /agree returns status='accepted' and agreed_terms**
6. **POST /secure returns secured_offer with label and terms**
7. **POST /improve returns OffersResponse shape with new cards**
8. **POST /end returns status='no_deal'**
9. **After agree (terminal), all actions return 409**
10. **After end (terminal), all actions return 409**
11. **On final round, actions_available excludes 'improve'**
12. **POST /improve on final round returns error**
13. **POST /secure persists: subsequent GET shows secured_offer**
14. **Invalid card_label returns 422**
15. **Nonexistent negotiation returns error**
16. **Improve advances round; Secure does not**
17. **409 responses have detail.error body**

### Existing Test Audit (post-integration)

| Error Category | Test Count | Blind Spot? |
|---------------|-----------|-------------|
| Input/output errors | 7 (+3 new) | No -- invalid label, missing negotiation |
| Logic errors | 30 (+12 new) | No -- terminal states, round boundary, state machine |
| Computation errors | 14 | No -- unchanged, domain-layer |
| Interface errors | 6 (+3 new) | No -- response shapes, formatted terms |
| Data errors | 10 (+4 new) | No -- is_first_visit, secured_offer persistence |
| Configuration errors | 0 | Yes -- still no invalid config tests |
| Integration errors | 37 (+37 new) | No -- full HTTP contract coverage |
| Regression errors | 0 | N/A |

### Tests Written

| Test | Claim Targeted | Error Category | Risk Level |
|------|---------------|----------------|------------|
| `TestGetOffersStructure::test_get_offers_returns_200_with_three_cards` | 3 cards returned | Integration | H |
| `TestGetOffersStructure::test_each_card_has_required_fields` | Card schema | Integration | H |
| `TestGetOffersStructure::test_card_labels_are_the_three_expected_profiles` | Label values | Integration | M |
| `TestGetOffersStructure::test_exactly_one_card_is_recommended` | Recommended flag | Integration | M |
| `TestGetOffersStructure::test_terms_are_formatted_strings_not_raw_numbers` | Term formatting | Interface | H |
| `TestGetOffersStructure::test_response_includes_banner_and_actions` | Top-level fields | Integration | M |
| `TestGetOffersStructure::test_initial_offers_have_no_secured_offer` | Null secured_offer | Data | M |
| `TestIsFirstVisit::test_first_get_sets_is_first_visit_true` | is_first_visit true | Data | H |
| `TestIsFirstVisit::test_second_get_sets_is_first_visit_false` | is_first_visit false after | Data | H |
| `TestActionResponseShapes::test_agree_returns_status_and_agreed_terms` | Agree response | Integration | H |
| `TestActionResponseShapes::test_secure_returns_secured_offer_with_label_and_terms` | Secure response | Integration | H |
| `TestActionResponseShapes::test_improve_returns_offers_response_shape` | Improve response | Integration | H |
| `TestActionResponseShapes::test_end_returns_no_deal_status` | End response | Integration | H |
| `TestTerminalStateAfterAgree::test_get_offers_after_agree_returns_409` | GET after agree | Logic | H |
| `TestTerminalStateAfterAgree::test_improve_after_agree_returns_409` | Improve after agree | Logic | H |
| `TestTerminalStateAfterAgree::test_secure_after_agree_returns_409` | Secure after agree | Logic | H |
| `TestTerminalStateAfterAgree::test_agree_after_agree_returns_409` | Double agree | Logic | H |
| `TestTerminalStateAfterAgree::test_end_after_agree_returns_409` | End after agree | Logic | M |
| `TestTerminalStateAfterEnd::test_get_offers_after_end_returns_409` | GET after no_deal | Logic | H |
| `TestTerminalStateAfterEnd::test_improve_after_end_returns_409` | Improve after no_deal | Logic | H |
| `TestTerminalStateAfterEnd::test_secure_after_end_returns_409` | Secure after no_deal | Logic | H |
| `TestTerminalStateAfterEnd::test_agree_after_end_returns_409` | Agree after no_deal | Logic | H |
| `TestTerminalStateAfterEnd::test_end_after_end_returns_409` | Double end | Logic | M |
| `TestFullNegotiationFlow::test_multi_round_flow_to_agreement` | End-to-end happy path | Integration | H |
| `TestFinalRoundBehavior::test_final_round_excludes_improve_from_actions` | actions_available | Logic | H |
| `TestFinalRoundBehavior::test_improve_on_final_round_is_rejected` | Improve rejected | Logic | H |
| `TestFinalRoundBehavior::test_improve_on_final_round_returns_409_not_500` | 409 not 500 | Integration | H |
| `TestFinalRoundBehavior::test_reaching_final_round_via_improves` | Round 5 of 5 | Logic | H |
| `TestSecuredOfferPersistence::test_secured_offer_appears_in_subsequent_get` | Persistence | Data | H |
| `TestSecuredOfferPersistence::test_secure_can_be_overwritten` | Overwrite | Data | M |
| `TestInvalidCardLabel::test_agree_with_invalid_label_returns_422` | Validation | Input/output | H |
| `TestInvalidCardLabel::test_improve_with_empty_label_returns_422` | Empty string | Input/output | M |
| `TestInvalidCardLabel::test_secure_with_lowercase_label_returns_422` | Case sensitivity | Input/output | M |
| `TestNonexistentNegotiation::test_get_offers_for_missing_negotiation` | 404/500 on missing | Input/output | H |
| `TestNonexistentNegotiation::test_agree_for_missing_negotiation` | 404/500 on missing | Input/output | H |
| `TestRoundAdvancement::test_improve_changes_the_offers` | Round advances | Logic | M |
| `TestRoundAdvancement::test_secure_does_not_change_cards` | Round unchanged | Logic | M |
| `TestErrorResponseBody::test_409_has_error_detail` | Error body shape | Integration | M |

### Bugs Found (FALSIFIED Claims)

**Bug 1: GET /offers does not enforce terminal state (FALSIFIED)**
- Claim: "After agree/end, GET /offers returns 409"
- Evidence: `GetOffersUseCase.execute()` only checks for `PENDING` state. When state is `ACCEPTED` or `NO_DEAL`, it falls through and returns the last MESO set with 200.
- Location: `back/application/get_offers.py:92` -- needs guard for terminal states.
- Tests: `test_get_offers_after_agree_returns_409` (xfail), `test_get_offers_after_end_returns_409` (xfail)

**Bug 2: Improve on final round returns 500 instead of 409 (FALSIFIED)**
- Claim: "POST /improve on final round returns 409 Conflict"
- Evidence: `NegotiationError("Cannot improve on the final round...")` does not contain "terminal", "accepted", or "no_deal", so `_raise_terminal()` in routes.py re-raises it as an unhandled exception (500).
- Location: `back/routes.py:174` -- `_raise_terminal` needs broader matching or a structural approach (catch all NegotiationError as 409).
- Test: `test_improve_on_final_round_returns_409_not_500` (xfail)

**Bug 3: Nonexistent negotiation returns 500 (unhandled KeyError)**
- Claim: "Requesting a non-existent negotiation returns a client error"
- Evidence: `InMemoryNegotiationRepository.get()` raises `KeyError` which is not caught by routes or use cases, producing 500.
- Location: `back/infrastructure/memory_repo.py:22` or needs a route-level exception handler.
- Tests: `test_get_offers_for_missing_negotiation`, `test_agree_for_missing_negotiation` (assert >= 400, passes as 500)

### Verdicts

| Claim | Verdict |
|-------|---------|
| GET /offers returns 3 cards with correct schema | NOT YET FALSIFIED |
| Exactly one card recommended (MOST BALANCED) | NOT YET FALSIFIED |
| Terms are formatted display strings | NOT YET FALSIFIED |
| is_first_visit true on first GET, false after | NOT YET FALSIFIED |
| POST /agree response shape | NOT YET FALSIFIED |
| POST /secure response shape | NOT YET FALSIFIED |
| POST /improve response shape | NOT YET FALSIFIED |
| POST /end response shape | NOT YET FALSIFIED |
| After agree, all actions return 409 | **FALSIFIED** -- GET /offers returns 200 |
| After end, all actions return 409 | **FALSIFIED** -- GET /offers returns 200 |
| Final round excludes improve from actions | NOT YET FALSIFIED |
| Improve on final round returns 409 | **FALSIFIED** -- returns 500 |
| Secured offer persists across GETs | NOT YET FALSIFIED |
| Invalid card_label returns 422 | NOT YET FALSIFIED |
| Nonexistent negotiation returns client error | **PARTIALLY FALSIFIED** -- returns 500 (server error), not 404 |
| Improve advances round; Secure does not | NOT YET FALSIFIED |
| 409 responses have detail.error body | NOT YET FALSIFIED |

### Remaining Blind Spots

1. **Configuration errors**: Still no tests for invalid configs.
2. **Concurrency**: No tests for double-click protection or concurrent requests.
3. **Missing negotiation**: Should return 404, currently returns 500 -- handoff to coder.
4. **CORS headers**: Not tested (browser-level concern, but could add preflight checks).
5. **Property-based testing**: MESO generator invariants across random inputs.
