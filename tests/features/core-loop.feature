Feature: Core Negotiation Loop — Supplier MESO Interaction
  As Maria Chen, Sales & Account Manager at Pacific Corrugated Solutions,
  I want to review, compare, and act on multiple offer cards each round
  So that I can secure contract terms that improve my cash flow
  without lengthy back-and-forth or free-text negotiation.

  The UI presents 3 labeled MESO offer cards per round. Each card emphasizes
  a different term strength (Best Price, Most Balanced, Fastest Payment).
  All 3 cards carry equal MAUT utility for the operator but differ in term
  distribution. The supplier interacts exclusively through clicks: Agree,
  Secure as fallback, or Improve terms. No utility scores, round counters,
  or trade-off prompts appear on the supplier-facing UI.

  Background:
    Given James has configured the "packaging, mid-spend, commodity" cohort:
      | Term             | Opening | Target | Walk-Away | Weight |
      | Price ($/k boxes)| $11.50  | $12.50 | $14.50    | 0.40   |
      | Payment (days)   | Net 90  | Net 75 | Net 30    | 0.25   |
      | Delivery (days)  | 7       | 10     | 14        | 0.20   |
      | Contract (months)| 6       | 12     | 24        | 0.15   |
    And the round limit is 5
    And Maria Chen of Pacific Corrugated Solutions has an expiring contract at $14.20/k, Net 60, 14-day delivery, 12-month contract

  # ---------------------------------------------------------------------------
  # 1. OFFER PRESENTATION — 3 labeled MESO cards with a Recommended badge
  # ---------------------------------------------------------------------------

  Scenario: Maria sees 3 labeled offer cards on the review screen
    When the engine presents the current round's offers to Maria
    Then she sees a banner stating "OFFERS UPDATED BASED ON YOUR PREFERENCES"
    And she sees exactly 3 offer cards displayed side by side
    And the cards are labeled "BEST PRICE", "MOST BALANCED", and "FASTEST PAYMENT"
    And the "MOST BALANCED" card displays a "Recommended" badge

  Scenario: Each offer card shows all 4 negotiation terms
    When the engine presents offers to Maria
    Then each card displays a value for price per unit, delivery time, payment terms, and contract length
    And no card is missing any of the 4 terms

  Scenario: Offer cards show concrete term values from the engine
    When the engine presents the opening round offers to Maria
    Then the cards show values such as:
      | Card             | Price   | Delivery | Payment | Contract  |
      | BEST PRICE       | $120.00 | 10 days  | Net 60  | 12 months |
      | MOST BALANCED    | $115.00 | 14 days  | Net 45  | 24 months |
      | FASTEST PAYMENT  | $110.00 | 14 days  | Net 30  | 12 months |
    And no two cards have identical values across all 4 terms

  Scenario: Cards highlight favorable terms with visual indicators
    When the engine presents offers to Maria
    Then terms that are strong relative to the card's label show a green checkmark
    And the "BEST PRICE" card shows a checkmark on the price term
    And the "FASTEST PAYMENT" card shows a checkmark on the payment term

  Scenario: All 3 offer cards carry equal operator utility
    When the engine generates a MESO set for any round
    Then the MAUT utility score for James is equal across all 3 cards within a tolerance of 0.02
    And this utility score is not displayed to Maria

  # ---------------------------------------------------------------------------
  # 2. ACTIONS PER CARD — Agree, Secure as fallback, Improve terms
  # ---------------------------------------------------------------------------

  Scenario: Each card presents exactly 3 actions
    When the engine presents offers to Maria
    Then each card has a green "Agree" button
    And each card has a "Secure as fallback" button
    And each card has an "Improve terms" link
    And no free-text input field appears anywhere on the screen

  # ---------------------------------------------------------------------------
  # 3. AGREE — Accept deal and close negotiation
  # ---------------------------------------------------------------------------

  Scenario: Maria agrees to the Most Balanced offer
    Given Maria is viewing the current round's 3 offer cards
    And the "MOST BALANCED" card shows $115.00, 14 days delivery, Net 45, 24 months
    When Maria clicks "Agree" on the "MOST BALANCED" card
    Then the negotiation state changes to "Accepted"
    And the final agreed terms are $115.00 price, 14-day delivery, Net 45 payment, 24-month contract
    And Maria sees a deal summary confirming the accepted terms

  Scenario: Maria agrees on the first round without further negotiation
    Given Maria is viewing the opening round offers
    When Maria clicks "Agree" on any card
    Then the deal closes with that card's terms
    And the negotiation ends after a single round

  Scenario: Agree is available on every round including the final round
    Given the negotiation has reached round 5 of 5
    When the engine presents the final round's offers
    Then each card still shows the "Agree" button
    And Maria can close the deal by clicking "Agree" on any card

  # ---------------------------------------------------------------------------
  # 4. SECURE AS FALLBACK — Mark a card as reservation value
  # ---------------------------------------------------------------------------

  Scenario: Maria secures an offer and the negotiation continues
    Given Maria is viewing round 2 offers
    And the "FASTEST PAYMENT" card shows $110.00, 14 days delivery, Net 30, 12 months
    When Maria clicks "Secure as fallback" on the "FASTEST PAYMENT" card
    Then the card is visually marked as her secured fallback
    And the negotiation does not end
    And Maria can still click "Improve terms" on any card to continue negotiating

  Scenario: Only one offer can be secured at a time
    Given Maria previously secured the "FASTEST PAYMENT" card in round 2
    And she is now viewing round 3 offers
    When Maria clicks "Secure as fallback" on the "MOST BALANCED" card
    Then the "MOST BALANCED" card is marked as her new secured fallback
    And the previously secured offer is no longer marked

  Scenario: Secured offer is preserved across rounds
    Given Maria secured an offer showing $110.00, Net 30, 14 days, 12 months in round 2
    And the negotiation is now in round 4
    Then the secured offer terms remain recorded at $110.00, Net 30, 14 days, 12 months
    And the secured offer is available as an option on the final round

  Scenario: Securing updates the opponent model utility floor
    Given the opponent model has no utility floor set
    When Maria clicks "Secure as fallback" on a card with operator utility 0.68
    Then the engine records a supplier utility floor based on the secured offer
    And subsequent MESO offers account for the secured terms as an acceptable threshold

  # ---------------------------------------------------------------------------
  # 5. IMPROVE TERMS — Signal preference and trigger new MESO generation
  # ---------------------------------------------------------------------------

  Scenario: Maria clicks Improve on the Best Price card
    Given Maria is viewing round 1 offers
    And the "BEST PRICE" card shows $120.00, 10 days delivery, Net 60, 12 months
    When Maria clicks "Improve terms" on the "BEST PRICE" card
    Then the engine generates a new set of 3 MESO offer cards
    And Maria sees the updated offers with the banner "OFFERS UPDATED BASED ON YOUR PREFERENCES"
    And no trade-off selection prompt appears between the click and the new offers

  Scenario: Improve shifts the next round's offers toward the card's strength
    Given Maria is viewing round 1 offers where the "FASTEST PAYMENT" card shows Net 30
    When Maria clicks "Improve terms" on the "FASTEST PAYMENT" card
    Then the round 2 offers show payment terms that are faster or equal to the round 1 average
    And at least one round 2 card offers payment terms at Net 30 or faster

  Scenario: Improve updates the opponent model weights
    Given the opponent model weights are price 0.25, payment 0.25, delivery 0.25, contract 0.25
    When Maria clicks "Improve terms" on the "FASTEST PAYMENT" card
    Then the opponent model increases the payment weight above 0.25
    And the opponent model decreases one or more other term weights to compensate
    And the weights still sum to 1.00

  Scenario: Consecutive Improve signals on the same dimension compound the shift
    Given Maria clicked "Improve terms" on the "FASTEST PAYMENT" card in round 1
    And the round 2 offers already shifted toward faster payment
    When Maria clicks "Improve terms" on the card with the fastest payment in round 2
    Then the round 3 offers shift further toward faster payment
    And the payment terms in round 3 are faster or equal to those in round 2

  Scenario: Improve signals on different dimensions across rounds balance the offers
    Given Maria clicked "Improve terms" on the "FASTEST PAYMENT" card in round 1
    When Maria clicks "Improve terms" on the "BEST PRICE" card in round 2
    Then the round 3 offers attempt to improve both payment and price
    And the opponent model shows elevated weights for both payment and price

  # ---------------------------------------------------------------------------
  # 6. ROUND PROGRESSION — Diminishing concessions, no visible round counter
  # ---------------------------------------------------------------------------

  Scenario: Each Improve action advances the negotiation by one round
    Given the negotiation is at round 1
    When Maria clicks "Improve terms" on any card
    Then the engine internally advances to round 2
    And a new set of 3 offer cards is generated
    And no round counter is displayed to Maria

  Scenario: Maria cannot return to previous round offers after clicking Improve
    Given Maria is viewing round 2 offers
    And she has not secured any offer
    When Maria clicks "Improve terms" on any card
    Then the round 2 offers are replaced by the round 3 offers
    And the round 2 offers are no longer accessible
    And there is no back button, undo, or navigation to previous rounds
    And if Maria wanted to keep a round 2 offer she should have secured it first

  Scenario: Offers concede less in later rounds than in earlier rounds
    Given Maria clicks "Improve terms" in rounds 1, 2, 3, and 4
    Then the magnitude of term improvement from round 1 to round 2 is larger than from round 3 to round 4
    And the concession rate follows the Boulware curve with diminishing concessions

  Scenario: The final round removes the Improve action
    Given the negotiation has reached round 5 of 5
    When the engine presents the final round's offers
    Then the "Improve terms" link is not available on any card
    And each card shows only "Agree" and "Secure as fallback"
    And Maria sees a message indicating these are the final offers

  Scenario: Maria can still Agree or Secure on the final round
    Given the negotiation is at round 5 of 5
    And Maria has a secured offer from round 3
    When the engine presents the final round's offers
    Then Maria can click "Agree" on any of the 3 final cards
    And Maria can click "Agree" to accept her previously secured offer
    And if Maria takes no action, the negotiation ends as "No Deal"

  # ---------------------------------------------------------------------------
  # 7. NO-DEAL OUTCOME — Negotiation ends without agreement
  # ---------------------------------------------------------------------------

  Scenario: Maria reaches the final round and does not agree
    Given the negotiation has reached round 5 of 5
    And Maria has no secured offer
    When Maria does not click "Agree" on any card
    Then the negotiation state changes to "No Deal"
    And the negotiation history is preserved for future renegotiation

  Scenario: Maria has a secured offer but chooses not to accept on the final round
    Given the negotiation has reached round 5 of 5
    And Maria has a secured offer at $110.00, Net 30, 14 days, 12 months
    When Maria does not click "Agree" on any card or on the secured offer
    Then the negotiation state changes to "No Deal"
    And the secured offer is not automatically accepted

  # ---------------------------------------------------------------------------
  # 8. MESO GENERATION CONSTRAINTS — Equal utility, within walk-away limits
  # ---------------------------------------------------------------------------

  Scenario: No generated offer violates the operator's walk-away limits
    When the engine generates offers for any round
    Then no offer includes a price above $14.50/k boxes
    And no offer includes payment terms faster than Net 30
    And no offer includes delivery time longer than 14 days
    And no offer includes a contract longer than 24 months

  Scenario: MESO cards differ in term distribution despite equal operator utility
    When the engine generates 3 MESO cards for round 2
    Then the "BEST PRICE" card has the lowest price among the 3 cards
    And the "FASTEST PAYMENT" card has the fastest payment terms among the 3 cards
    And the "MOST BALANCED" card does not have the most extreme value on any single term

  Scenario: Offers in later rounds are more favorable to Maria than opening offers
    Given Maria clicked "Improve terms" in round 1
    When the engine generates round 2 offers
    Then the average price across round 2 cards is equal to or higher than round 1
    And the average payment speed across round 2 cards is equal to or faster than round 1
    And at least one term has moved in Maria's favor

  # ---------------------------------------------------------------------------
  # 9. OPERATOR CONFIGURATION — Weights, targets, and limits feed the engine
  # ---------------------------------------------------------------------------

  Scenario: Operator weights determine how MAUT utility is calculated
    Given James configured weights of price 0.40, payment 0.25, delivery 0.20, contract 0.15
    When the engine evaluates an offer at $13.00, Net 45, 10 days, 18 months
    Then the MAUT utility is calculated as the weighted sum of per-term achievement between walk-away and target
    And price contributes 0.40 of the utility, payment 0.25, delivery 0.20, contract 0.15

  Scenario: Operator changes weights and the MESO distribution shifts
    Given James changes the weights to price 0.30, payment 0.30, delivery 0.20, contract 0.20
    When the engine generates a new MESO set
    Then the offers allocate more value to payment terms than under the original 0.25 payment weight
    And the "MOST BALANCED" card reflects the updated weight balance

  # ---------------------------------------------------------------------------
  # 10. ELEMENTS NOT PRESENT ON THE SUPPLIER UI
  # ---------------------------------------------------------------------------

  Scenario: No utility score or progress bar is shown to Maria
    When the engine presents offers to Maria on any round
    Then no MAUT utility score is displayed on the screen
    And no progress bar or percentage indicator appears
    And utility scoring remains an internal engine calculation only

  Scenario: No round counter is shown to Maria
    When the engine presents offers to Maria on any round
    Then no text such as "Round 2 of 5" appears on the screen
    And the round limit remains an internal engine parameter

  Scenario: No trade-off selection prompt appears after clicking Improve
    Given Maria is viewing round 1 offers
    When Maria clicks "Improve terms" on any card
    Then no prompt asking "what would you like to trade?" appears
    And no selection of terms to give up is presented
    And the engine directly generates new offers based on the card's strength signal

  Scenario: No free-text input or chat interface is available to Maria
    When Maria views any round of the negotiation
    Then no text input field, text area, or chat interface is displayed
    And Maria's only interaction options are Agree, Secure as fallback, and Improve terms

  Scenario: Operator utility scores are never exposed in the supplier API response
    When the engine generates offers and sends them to Maria's UI
    Then the API response to the supplier frontend does not include the MAUT utility field
    And the supplier UI does not render any numeric score

  Scenario: The round number is tracked internally but not exposed to Maria
    Given the negotiation is at round 3
    When the engine presents round 3 offers to Maria
    Then the internal state records round 3
    And the API response to the supplier frontend does not include the round number
    And no text referencing "round", "step", or a numeric progress indicator appears

  # ---------------------------------------------------------------------------
  # 11. UI STATES — Loading, error, first-time, and resume
  # ---------------------------------------------------------------------------

  Scenario: Maria sees a loading state while the engine generates new offers
    Given Maria is viewing round 1 offers
    When Maria clicks "Improve terms" on the "FASTEST PAYMENT" card
    Then the current offer cards transition to a loading state with skeleton placeholders
    And a message reads "Generating new offers based on your preferences..."
    And the loading state resolves to display 3 new offer cards

  Scenario: Maria sees a loading state while the deal is being finalized
    Given Maria is viewing round 3 offers
    When Maria clicks "Agree" on the "MOST BALANCED" card
    Then the button changes to a disabled state indicating processing
    And a brief undo option appears reading "Deal accepted. Undo?"
    And after the undo window expires, the deal summary screen appears

  Scenario: Maria clicks Agree and uses the undo window
    Given Maria is viewing round 2 offers
    When Maria clicks "Agree" on the "FASTEST PAYMENT" card
    Then she sees a confirmation bar with an "Undo" option
    When Maria clicks "Undo" within the undo window
    Then the agreement is cancelled
    And Maria returns to viewing the round 2 offers with all 3 actions available

  Scenario: Engine fails to generate new offers after Improve
    Given Maria is viewing round 2 offers
    When Maria clicks "Improve terms" on any card
    And the engine encounters an error during MESO generation
    Then the current round 2 offers remain visible and unchanged
    And an error banner appears indicating offers could not be generated
    And the "Improve terms" link remains clickable to retry

  Scenario: Network drops during Agree
    Given Maria is viewing round 4 offers
    When Maria clicks "Agree" on the "BEST PRICE" card
    And the network connection is lost before the server confirms
    Then Maria sees an error message indicating the agreement could not be confirmed
    And the "Agree" button returns to its original clickable state
    And the offer terms are preserved exactly as displayed

  Scenario: Maria sees the MESO card format for the first time
    Given Maria has never interacted with MESO offers on this platform
    When the engine presents the opening round's offers
    Then a brief introductory banner appears explaining the multiple-offer format
    And the banner is dismissible
    And the 3 offer cards are displayed below the banner

  Scenario: Offers have not yet loaded when Maria opens the negotiation link
    Given Maria clicks the renegotiation link from her notification
    When the offer screen begins loading
    Then she sees the page header "Review your negotiated offers" immediately
    And 3 skeleton card placeholders appear in the card positions
    And the skeleton cards resolve to actual offers as data loads

  Scenario: Maria closes the browser mid-negotiation and returns
    Given Maria was viewing round 3 offers and had secured a fallback in round 2
    When Maria closes her browser and reopens the negotiation link later
    Then she sees the round 3 offers exactly as they were when she left
    And her secured fallback from round 2 is still marked and accessible
    And she can continue the negotiation from round 3

  Scenario: Maria returns to a negotiation that has already been completed
    Given Maria agreed to the "MOST BALANCED" card in a previous session
    When Maria opens the negotiation link again
    Then she sees the deal summary screen with the accepted terms
    And the offer cards are no longer interactive

  Scenario: Maria double-clicks Improve terms rapidly
    Given Maria is viewing round 1 offers
    When Maria clicks "Improve terms" on the "BEST PRICE" card twice in rapid succession
    Then only one round advance occurs
    And the second click is ignored while the engine is generating

  # ---------------------------------------------------------------------------
  # 12. NEGOTIATION LIFECYCLE — State transitions
  # ---------------------------------------------------------------------------

  Scenario: Negotiation begins in pending state before Maria opens it
    Given James has configured the cohort and initiated renegotiation for Maria
    When Maria has not yet opened the negotiation link
    Then the negotiation state is "Pending"

  Scenario: Negotiation moves to active when Maria views the first offers
    Given the negotiation state is "Pending"
    When Maria opens the negotiation and views the opening round offers
    Then the negotiation state changes to "Active"

  Scenario: Accepted state is terminal — no further actions are possible
    Given Maria clicked "Agree" on a card and the state is "Accepted"
    When an attempt is made to submit any action on the negotiation
    Then the action is rejected
    And the negotiation remains in "Accepted" state

  Scenario: No-Deal state is terminal — no further actions are possible
    Given the negotiation reached the final round and ended as "No Deal"
    When an attempt is made to submit any action on the negotiation
    Then the action is rejected
    And the negotiation remains in "No Deal" state

  # ---------------------------------------------------------------------------
  # 13. OPPONENT MODEL — Initialization and accept reinforcement
  # ---------------------------------------------------------------------------

  Scenario: Opponent model weights are initialized uniformly
    Given a new negotiation is started for Maria
    When the engine prepares the first round
    Then the opponent model weights are price 0.25, payment 0.25, delivery 0.25, contract 0.25

  Scenario: Agree reinforces all weights in the opponent model
    Given the opponent model weights are price 0.20, payment 0.35, delivery 0.25, contract 0.20
    When Maria clicks "Agree" on a card
    Then the opponent model records the final weights with all dimensions reinforced
    And the reinforced weights are available for future renegotiations with Maria

  Scenario: Engine combines operator and opponent weights when generating MESO
    Given James's operator weights are price 0.40, payment 0.25, delivery 0.20, contract 0.15
    And the opponent model weights are price 0.20, payment 0.40, delivery 0.25, contract 0.15
    When the engine generates a MESO set
    Then the offers reflect both James's price priority and Maria's payment priority
    And the MESO distribution differs from what either weight vector alone would produce

  Scenario: Opponent model weight never becomes negative after repeated Improve
    Given the opponent model weights are price 0.25, payment 0.25, delivery 0.25, contract 0.25
    When Maria clicks "Improve terms" on the "FASTEST PAYMENT" card in rounds 1, 2, 3, and 4
    Then the payment weight increases each round
    And no weight for any term drops below 0.00
    And all weights still sum to 1.00

  # ---------------------------------------------------------------------------
  # 14. MAUT COMPUTATION — Formula verification and boundaries
  # ---------------------------------------------------------------------------

  Scenario: MAUT utility is 0.0 when all terms are at walk-away values
    Given James configured targets and walk-away limits:
      | Term     | Target | Walk-Away |
      | Price    | $12.50 | $14.50    |
      | Payment  | Net 75 | Net 30    |
      | Delivery | 10     | 14        |
      | Contract | 12     | 24        |
    When the engine evaluates an offer at $14.50, Net 30, 14 days, 24 months
    Then the MAUT utility for James is 0.00

  Scenario: MAUT utility is 1.0 when all terms are at target values
    Given James configured targets and walk-away limits:
      | Term     | Target | Walk-Away |
      | Price    | $12.50 | $14.50    |
      | Payment  | Net 75 | Net 30    |
      | Delivery | 10     | 14        |
      | Contract | 12     | 24        |
    When the engine evaluates an offer at $12.50, Net 75, 10 days, 12 months
    Then the MAUT utility for James is 1.00

  Scenario: MAUT utility calculation with concrete numeric verification
    Given James configured weights of price 0.40, payment 0.25, delivery 0.20, contract 0.15
    And targets of $12.50, Net 75, 10 days, 12 months
    And walk-away limits of $14.50, Net 30, 14 days, 24 months
    When the engine evaluates an offer at $13.50, Net 45, 12 days, 18 months
    Then the per-term achievement for price is ($13.50 - $14.50) / ($12.50 - $14.50) = 0.50
    And the per-term achievement for payment is (45 - 30) / (75 - 30) = 0.333
    And the per-term achievement for delivery is (12 - 14) / (10 - 14) = 0.50
    And the per-term achievement for contract is (18 - 24) / (12 - 24) = 0.50
    And the MAUT utility is 0.40 * 0.50 + 0.25 * 0.333 + 0.20 * 0.50 + 0.15 * 0.50 = 0.458

  Scenario: An offer at exactly the walk-away boundary is valid
    When the engine generates offers
    Then an offer with price exactly $14.50 is within the valid range
    And an offer with payment terms exactly Net 30 is within the valid range
    And an offer with delivery time exactly 14 days is within the valid range
    And an offer with contract length exactly 24 months is within the valid range

  Scenario: No two MESO cards in a round have identical terms across all 4 dimensions
    When the engine generates 3 MESO cards for any round
    Then no pair of cards has the same price AND the same payment AND the same delivery AND the same contract length

  Scenario: Opening round uses the configured opening values
    Given James has configured opening values of $11.50, Net 90, 7 days, 6 months
    When the engine generates the opening round offers
    Then the offer terms start from the opening values
    And the opening round is deterministic with no opponent model influence

  Scenario: Operator weights must sum to 1.0
    Given James configured weights of price 0.40, payment 0.25, delivery 0.20, contract 0.15
    Then the operator weights sum to exactly 1.00

  # ---------------------------------------------------------------------------
  # 15. CONCESSION CURVE — Boulware strategy verification
  # ---------------------------------------------------------------------------

  Scenario: Concession curve at round 1 produces utility near opening
    Given the round limit is 5 and beta is greater than 1
    When the engine calculates target utility for round 1
    Then the target utility is close to the opening utility value

  Scenario: Concession curve at the final round produces utility near walk-away
    Given the round limit is 5 and beta is greater than 1
    When the engine calculates target utility for round 5
    Then the target utility is close to the walk-away utility value

  # ---------------------------------------------------------------------------
  # 16. ROUND PROGRESSION — Additional edge cases
  # ---------------------------------------------------------------------------

  Scenario: Secure alone does not advance the round
    Given the negotiation is at round 2
    When Maria clicks "Secure as fallback" on a card without clicking "Improve terms"
    Then the negotiation remains at round 2
    And the same 3 offer cards are still displayed
    And Maria can still click "Improve terms" to advance to round 3

  Scenario: Agree closes the negotiation without advancing the round
    Given the negotiation is at round 2
    When Maria clicks "Agree" on a card
    Then the negotiation does not advance to round 3
    And the negotiation state changes to "Accepted"

  Scenario: Maria can Secure one card and Improve another in the same round
    Given Maria is viewing round 2 offers
    When Maria clicks "Secure as fallback" on the "MOST BALANCED" card
    And Maria clicks "Improve terms" on the "BEST PRICE" card
    Then the "MOST BALANCED" card terms are recorded as Maria's secured fallback
    And the engine generates a new set of 3 MESO offer cards for round 3
    And the secured offer from round 2 is preserved

  Scenario: Improve on round R-1 produces the final round
    Given the round limit is 5
    And the negotiation is at round 4
    When Maria clicks "Improve terms" on any card
    Then the engine advances to round 5
    And round 5 offers do not include the "Improve terms" link
    And Maria sees a message indicating these are the final offers

  Scenario: Maria secures every round but never agrees
    Given the round limit is 5
    And Maria clicks "Secure as fallback" on a card in rounds 1 through 4
    And Maria clicks "Improve terms" on a different card in rounds 1 through 4
    When the negotiation reaches round 5
    Then Maria has exactly one secured offer (the most recently secured)
    And if Maria does not click "Agree" on any card, the negotiation state changes to "No Deal"
    And the secured offer is not automatically accepted

  Scenario: Agreeing on round 1 closes the deal with no opponent model history
    Given Maria is viewing the opening round offers
    And the opponent model weights are price 0.25, payment 0.25, delivery 0.25, contract 0.25
    When Maria clicks "Agree" on the "BEST PRICE" card
    Then the negotiation state changes to "Accepted"
    And the deal closes with the "BEST PRICE" card's terms
    And the opponent model records the Agree signal reinforcing all weights

  Scenario: Agreed terms exactly match the card values displayed to Maria
    Given Maria is viewing round 3 offers
    And the "FASTEST PAYMENT" card shows $112.50, 14 days delivery, Net 30, 18 months
    When Maria clicks "Agree" on the "FASTEST PAYMENT" card
    Then the final agreed terms are exactly $112.50 price, 14-day delivery, Net 30 payment, 18-month contract
    And no rounding or adjustment is applied between display and storage

  Scenario: No-deal when Maria exhausts all rounds without securing or agreeing
    Given the round limit is 5
    And Maria clicked "Improve terms" in rounds 1 through 4 without securing any offer
    When the negotiation reaches round 5
    And Maria does not click "Agree" on any card
    Then the negotiation state changes to "No Deal"
    And no secured offer exists to fall back to
    And the negotiation history records all 5 rounds of offers

  # ---------------------------------------------------------------------------
  # 17. UI PRESENTATION — Page structure and action hierarchy
  # ---------------------------------------------------------------------------

  Scenario: Page title reads "Review your negotiated offers"
    When the engine presents offers to Maria
    Then the page displays the heading "Review your negotiated offers"

  Scenario: Improve terms is styled as a text link, not a button
    When the engine presents offers to Maria
    Then "Agree" is rendered as a prominent green button
    And "Secure as fallback" is rendered as a secondary outlined button
    And "Improve terms" is rendered as a text link below the buttons

  Scenario: Maria has not secured any offer and clicks Improve on the penultimate round
    Given Maria is viewing round 4 of 5 offers
    And she has not secured any offer
    When Maria clicks "Improve terms" on any card
    Then a nudge appears suggesting Maria consider securing an offer as a fallback
    And Maria can proceed with Improve or choose to Secure first
