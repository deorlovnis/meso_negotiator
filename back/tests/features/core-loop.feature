Feature: Full Loop
  As Maria Chen, Sales & Account Manager at Pacific Corrugated Solutions,
  I want to review, compare, and act on multiple offer cards each round
  So that I can secure contract terms that improve my cash flow
  without lengthy back-and-forth or free-text negotiation.

  The engine presents 3 labeled MESO offer cards per round. Each card
  emphasizes a different term strength (Best Price, Most Balanced, Fastest
  Payment). All 3 cards carry equal MAUT utility for the operator but differ
  in term distribution. The supplier interacts through Agree, Secure as
  fallback (max 3), or a 2-step Improve terms flow. Both Secure and Improve
  advance the round. No utility scores or round counters are shown to the
  supplier.

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
  # 1. OFFER PRESENTATION -- 3 labeled cards, Recommended badge, equal utility
  # ---------------------------------------------------------------------------

  Scenario: Maria sees 3 labeled offer cards each round
    When the engine presents the current round's offers to Maria
    Then she sees exactly 3 offer cards labeled "BEST PRICE", "MOST BALANCED", and "FASTEST PAYMENT"
    And the "MOST BALANCED" card displays a "Recommended" badge
    And each card displays a value for price, delivery, payment, and contract length

  Scenario: All 3 offer cards carry equal operator utility
    When the engine generates a MESO set for any round
    Then the MAUT utility score for James is equal across all 3 cards within a tolerance of 0.02
    And this utility score is not exposed to Maria

  # ---------------------------------------------------------------------------
  # 2. ACTIONS PER CARD -- Agree, Secure, 2-step Improve, no free-text
  # ---------------------------------------------------------------------------

  Scenario: Each card presents exactly 3 actions and no free-text input
    When the engine presents offers to Maria
    Then each card offers "Agree", "Secure as fallback", and "Improve terms"
    And no free-text input field is available anywhere

  # ---------------------------------------------------------------------------
  # 3. AGREE -- Closes deal from card or Compare table, terminal state
  # ---------------------------------------------------------------------------

  Scenario: Maria agrees to an offer from a card
    Given Maria is viewing the current round's 3 offer cards
    And the "MOST BALANCED" card shows $115.00, 14 days delivery, Net 45, 24 months
    When Maria clicks "Agree" on the "MOST BALANCED" card
    Then the negotiation state changes to "Accepted"
    And the final agreed terms are $115.00 price, 14-day delivery, Net 45 payment, 24-month contract
    And Maria sees a "Deal Closed" confirmation

  Scenario: Maria agrees to a secured offer from the Compare Offers table
    Given Maria has secured 2 offers across previous rounds
    And she opens the Compare Offers table
    When Maria clicks "Agree" on the offer ranked first by Bot Rank
    Then the negotiation state changes to "Accepted"
    And the final agreed terms match the selected secured offer exactly

  Scenario: Accepted state is terminal
    Given Maria clicked "Agree" and the state is "Accepted"
    When an attempt is made to submit any further action on the negotiation
    Then the action is rejected
    And the negotiation remains in "Accepted" state

  # ---------------------------------------------------------------------------
  # 4. SECURE (v2) -- Max 3, advances round, Compare Offers table
  # ---------------------------------------------------------------------------

  Scenario: Securing an offer stores it and advances the round
    Given Maria is viewing round 2 offers
    And the "FASTEST PAYMENT" card shows $110.00, 14 days delivery, Net 30, 12 months
    When Maria clicks "Secure as fallback" on the "FASTEST PAYMENT" card
    Then the offer terms $110.00, Net 30, 14 days, 12 months are added to her secured offers
    And the engine advances to round 3
    And a new set of 3 MESO offer cards is generated

  Scenario: Maria can secure up to 3 offers across rounds
    Given Maria has secured 2 offers in previous rounds
    When Maria clicks "Secure as fallback" on a card in the current round
    Then the offer is added as her 3rd secured offer
    And the secured offers count is 3
    And the "Secure as fallback" action is disabled on all cards for subsequent rounds

  Scenario: Securing a 4th offer is rejected when 3 are already secured
    Given Maria has secured 3 offers
    When Maria attempts to click "Secure as fallback" on a card
    Then the action is rejected
    And the secured offers count remains 3

  Scenario: Compare Offers table shows secured offers ranked by Bot Rank
    Given Maria has secured 3 offers across rounds 1, 2, and 3
    When Maria opens the Compare Offers table
    Then she sees all 3 secured offers sorted by Bot Rank
    And each entry shows price, delivery, payment, and contract length

  Scenario: Secured offers are preserved across all subsequent rounds
    Given Maria secured an offer showing $110.00, Net 30, 14 days, 12 months in round 2
    And the negotiation is now in round 4
    Then the secured offer terms remain recorded at $110.00, Net 30, 14 days, 12 months

  # ---------------------------------------------------------------------------
  # 5. IMPROVE (v2) -- 2-step: select term + trade-off, generates new MESO set
  # ---------------------------------------------------------------------------

  Scenario: Maria improves a specific term by trading a specific other term
    Given Maria is viewing round 1 offers
    And the round 1 "MOST BALANCED" card shows payment Net 45 and delivery 7 days
    When Maria selects "Improve" on the payment term and selects delivery as the trade-off
    Then the engine receives signal_improve(improve_term=payment, trade_term=delivery)
    And a new set of 3 MESO offer cards is generated
    And the engine advances to round 2
    And the round 2 payment terms are faster (lower days) than round 1
    And the round 2 delivery terms are slower (higher days) than round 1

  Scenario: Improving price by trading contract makes price cheaper and contract longer
    Given Maria is viewing round 1 offers
    When Maria selects "Improve" on the price term and selects contract as the trade-off
    Then the engine advances to round 2
    And the round 2 price values are lower (cheaper) than round 1
    And the round 2 contract values are higher (longer) than round 1

  Scenario: Maria improves a term with "Balance other terms" (no specific trade-off)
    Given Maria is viewing round 1 offers
    When Maria selects "Improve" on the payment term and selects "Balance other terms"
    Then the engine receives signal_improve(improve_term=payment, trade_term=None)
    And a new set of 3 MESO offer cards is generated
    And the engine advances to round 2
    And the round 2 payment terms are faster (lower days) than round 1
    And no single other term absorbs the entire cost — the worsening is spread across price, delivery, and contract

  Scenario: Consecutive Improve signals on the same term compound the shift
    Given Maria improved the payment term by trading delivery in round 1
    And the round 2 offers shifted toward faster payment with slower delivery
    When Maria selects "Improve" on the payment term by trading delivery again in round 2
    Then the round 3 offers shift further toward faster payment
    And the payment terms in round 3 are faster or equal to those in round 2
    And the delivery terms in round 3 are slower or equal to those in round 2

  # ---------------------------------------------------------------------------
  # 6. ROUND PROGRESSION -- Both Secure and Improve advance, final round limits
  # ---------------------------------------------------------------------------

  Scenario: Improve advances the round by 1
    Given the negotiation is at round 1
    When Maria selects "Improve" on any term
    Then the engine advances to round 2
    And a new set of 3 offer cards is generated

  Scenario: Secure advances the round by 1
    Given the negotiation is at round 1
    When Maria clicks "Secure as fallback" on any card
    Then the engine advances to round 2
    And a new set of 3 offer cards is generated

  Scenario: Agree does not advance the round
    Given the negotiation is at round 2
    When Maria clicks "Agree" on a card
    Then the negotiation state changes to "Accepted"
    And the round does not advance to round 3

  Scenario: Final round removes Improve and Secure actions
    Given the negotiation has reached round 5 of 5
    When the engine presents the final round's offers
    Then "Improve terms" is not available on any card
    And "Secure as fallback" is not available on any card
    And each card shows only "Agree"

  Scenario: Offers concede less in later rounds than earlier rounds
    Given Maria clicks "Improve terms" in rounds 1, 2, 3, and 4
    Then the magnitude of term improvement from round 1 to round 2 is larger than from round 3 to round 4

  # ---------------------------------------------------------------------------
  # 7. NO-DEAL -- Terminal, secured offers NOT auto-accepted
  # ---------------------------------------------------------------------------

  Scenario: No-deal when Maria does not agree on the final round
    Given the negotiation has reached round 5 of 5
    And Maria has no secured offers
    When Maria does not click "Agree" on any card
    Then the negotiation state changes to "No Deal"

  Scenario: Secured offers are not auto-accepted on no-deal
    Given the negotiation has reached round 5 of 5
    And Maria has 2 secured offers
    When Maria does not click "Agree" on any card or secured offer
    Then the negotiation state changes to "No Deal"
    And the secured offers are not automatically accepted

  Scenario: No-Deal state is terminal
    Given the negotiation ended as "No Deal"
    When an attempt is made to submit any action on the negotiation
    Then the action is rejected
    And the negotiation remains in "No Deal" state

  # ---------------------------------------------------------------------------
  # 8. MESO CONSTRAINTS -- Walk-away limits, equal utility, different distributions
  # ---------------------------------------------------------------------------

  Scenario: No generated offer violates the operator's walk-away limits
    When the engine generates offers for any round
    Then no offer includes a price above $14.50/k boxes
    And no offer includes payment terms faster than Net 30
    And no offer includes delivery time longer than 14 days
    And no offer includes a contract longer than 24 months

  Scenario: MESO cards differ in term distribution despite equal operator utility
    When the engine generates 3 MESO cards for any round
    Then the "BEST PRICE" card has the lowest price among the 3 cards
    And the "FASTEST PAYMENT" card has the fastest payment terms among the 3 cards
    And the "MOST BALANCED" card does not have the most extreme value on any single term
    And no two cards have identical values across all 4 terms

  # ---------------------------------------------------------------------------
  # 9. OPPONENT MODEL -- Uniform init, explicit term-based updates, weight constraints
  # ---------------------------------------------------------------------------

  Scenario: Opponent model weights are initialized uniformly
    Given a new negotiation is started for Maria
    When the engine prepares the first round
    Then the opponent model weights are price 0.25, payment 0.25, delivery 0.25, contract 0.25

  Scenario: Improve with a specific trade-off updates weights explicitly
    Given the opponent model weights are price 0.25, payment 0.25, delivery 0.25, contract 0.25
    When Maria selects "Improve" on payment and selects delivery as the trade-off
    Then the opponent model increases the payment weight above 0.25
    And the opponent model decreases the delivery weight below 0.25
    And the other weights (price, contract) remain at 0.25
    And all weights sum to 1.00
    And the MESO generator uses the higher payment weight to produce offers with
      faster payment terms, at the cost of slower delivery — because the traded
      term (delivery) loses weight, the engine concedes less on delivery to fund
      the improvement on payment

  Scenario: Improve with "Balance other terms" distributes the decrease
    Given the opponent model weights are price 0.25, payment 0.25, delivery 0.25, contract 0.25
    When Maria selects "Improve" on payment and selects "Balance other terms"
    Then the opponent model increases the payment weight above 0.25
    And the decrease is distributed across price, delivery, and contract
    And all weights sum to 1.00
    And the resulting offers improve payment, with the cost spread so no single
      other term worsens dramatically

  Scenario: Opponent model weights never become negative after repeated Improve
    Given the opponent model weights are price 0.25, payment 0.25, delivery 0.25, contract 0.25
    When Maria selects "Improve" on payment with delivery as trade-off in rounds 1, 2, 3, and 4
    Then the payment weight increases each round
    And no weight for any term drops below 0.00
    And all weights sum to 1.00

  # ---------------------------------------------------------------------------
  # 10. MAUT -- Formula verification, boundary values
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
