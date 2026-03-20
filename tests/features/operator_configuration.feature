Feature: Operator Configuration, Monitoring, and Review
  As James Kowalski, Category Manager at RetailCo National,
  I configure the AI negotiation bot to execute my procurement strategy
  across 400+ tail-spend suppliers so that I can deliver quarterly savings
  without individually negotiating each contract.

  Background:
    Given James is logged in as an operator for RetailCo National
    And a supplier cohort "packaging, mid-spend, commodity" exists with 50 suppliers
    And Pacific Corrugated is a member of the "packaging, mid-spend, commodity" cohort

  # ---------------------------------------------------------------------------
  # 1. CONFIGURATION — Targets, limits, weights per supplier cohort
  # ---------------------------------------------------------------------------

  Scenario: Configure term targets, limits, and opening positions for a supplier cohort
    Given the "packaging, mid-spend, commodity" cohort has no configuration
    When James sets the cohort configuration as follows:
      | Term             | Opening | Target | Walk-Away | Direction        | Weight |
      | Price ($/k boxes)| $11.50  | $12.50 | $14.50    | lower is better  | 0.40   |
      | Payment (days)   | 90      | 75     | 30        | higher is better | 0.25   |
      | Delivery (days)  | 7       | 10     | 21        | lower is better  | 0.20   |
      | Contract (months)| 6       | 12     | 24        | lower is better  | 0.15   |
    Then the cohort configuration is saved with all four terms
    And the weights sum to 1.00
    And each term has opening, target, and walk-away values in the configured direction

  Scenario: Reject configuration where weights do not sum to 1.00
    Given the "packaging, mid-spend, commodity" cohort has no configuration
    When James sets weights of price 0.40, payment 0.25, delivery 0.20, contract 0.25
    Then the system rejects the configuration
    And the error message states "Weights must sum to 1.00 (current sum: 1.10)"

  Scenario: Reject configuration where walk-away is more favorable than target
    Given the "packaging, mid-spend, commodity" cohort has no configuration
    When James sets price target to $14.50 and price walk-away to $12.50 with direction "lower is better"
    Then the system rejects the configuration
    And the error message states "Walk-away ($12.50) cannot be more favorable than target ($14.50) for price"

  Scenario: Configure LLM conversation style for a cohort
    Given the "packaging, mid-spend, commodity" cohort is configured with term limits
    When James sets the system prompt to "Professional and collaborative tone. Reference the supplier's history with RetailCo. Emphasize mutual benefit."
    Then the LLM conversation style is saved for the cohort
    And the style is applied to all new negotiations in that cohort

  Scenario: Set round limit for a supplier cohort
    Given the "packaging, mid-spend, commodity" cohort is configured with term limits
    When James sets the round limit to 5
    Then all negotiations in the cohort will present "round N of 5" to suppliers

  # ---------------------------------------------------------------------------
  # 2. CONCESSION STRATEGY — Sequencing which terms to trade first
  # ---------------------------------------------------------------------------

  Scenario: Configure concession sequencing for a cohort
    Given the "packaging, mid-spend, commodity" cohort is configured with term limits
    When James sets the concession sequence as:
      | Priority | Term     | Rule                                      |
      | 1        | Delivery | Offer flexibility first                   |
      | 2        | Contract | Concede before price                      |
      | 3        | Price    | Concede only after delivery and contract   |
      | 4        | Payment  | Last resort concession                    |
    Then the bot will offer delivery flexibility before conceding on price
    And payment terms will only be conceded after delivery, contract, and price options are exhausted

  Scenario: Bot follows concession sequence in early rounds
    Given the "packaging, mid-spend, commodity" cohort has concession sequence delivery > contract > price > payment
    And a negotiation with Pacific Corrugated is in round 1
    When the bot generates a counter-offer in response to a supplier request to improve price
    Then the counter-offer trades delivery time before adjusting price
    And the audit log records "Concession sequence applied: offered delivery flexibility per configured priority 1"

  # ---------------------------------------------------------------------------
  # 3. LAUNCH CAMPAIGN — Deploy negotiation to supplier cohort
  # ---------------------------------------------------------------------------

  Scenario: Launch a negotiation campaign to a configured cohort
    Given the "packaging, mid-spend, commodity" cohort is fully configured
    And the cohort contains 50 suppliers with valid contact records
    When James launches the negotiation campaign
    Then 50 negotiation threads are created, one per supplier
    And each thread is initialized at round 0 with the cohort's opening position
    And the campaign status shows "50 active, 0 complete, 0 escalated"

  Scenario: Block campaign launch when configuration is incomplete
    Given the "packaging, mid-spend, commodity" cohort has weights configured but no walk-away limits
    When James attempts to launch the negotiation campaign
    Then the system blocks the launch
    And the error message states "Walk-away limits are required for all terms before launching"

  Scenario: Block campaign launch when a supplier lacks contact information
    Given the "packaging, mid-spend, commodity" cohort is fully configured
    And 3 of 50 suppliers have no contact email on file
    When James attempts to launch the negotiation campaign
    Then the system blocks the launch
    And the error message lists the 3 suppliers missing contact information

  # ---------------------------------------------------------------------------
  # 4. MONITOR IN-FLIGHT — Dashboard shows active negotiations
  # ---------------------------------------------------------------------------

  Scenario: View campaign dashboard with negotiations at various stages
    Given the "packaging, mid-spend, commodity" campaign is active with 50 negotiations
    And 12 negotiations are in round 1
    And 18 negotiations are in round 2
    And 10 negotiations are in round 3
    And 5 negotiations have reached agreement
    And 3 negotiations are stalled with no supplier response for 48 hours
    And 2 negotiations have been escalated
    When James views the campaign dashboard
    Then the dashboard shows:
      | Status     | Count |
      | Round 1    | 12    |
      | Round 2    | 18    |
      | Round 3    | 10    |
      | Agreed     | 5     |
      | Stalled    | 3     |
      | Escalated  | 2     |
    And the agreement rate displays as "10% (5 of 50)"

  Scenario: Identify a stalled negotiation on the dashboard
    Given a negotiation with Pacific Corrugated is in round 2
    And Pacific Corrugated has not responded for 72 hours
    When James views the campaign dashboard
    Then Pacific Corrugated appears in the "Stalled" list
    And the stall duration shows "72 hours since last supplier action"

  Scenario: View round-by-round progress for a single negotiation
    Given a negotiation with Pacific Corrugated has completed 3 rounds
    When James opens the Pacific Corrugated negotiation detail
    Then the detail view shows each round's offer, supplier action, and resulting terms
    And the current bot utility score is displayed for each round

  # ---------------------------------------------------------------------------
  # 5. OPPONENT MODEL VISIBILITY — Inferred supplier weights across rounds
  # ---------------------------------------------------------------------------

  Scenario: View initial opponent model weights before any supplier interaction
    Given a negotiation with Pacific Corrugated has been created at round 0
    When James views the opponent model for Pacific Corrugated
    Then the inferred supplier weights show:
      | Term     | Weight |
      | Price    | 0.25   |
      | Payment  | 0.25   |
      | Delivery | 0.25   |
      | Contract | 0.25   |
    And a note states "Uniform prior -- no supplier signals received yet"

  Scenario: Opponent model updates after supplier clicks Improve on payment and trades delivery
    Given a negotiation with Pacific Corrugated is in round 1
    And the opponent model weights are price 0.25, payment 0.25, delivery 0.25, contract 0.25
    When Pacific Corrugated clicks "Improve payment" and trades delivery
    Then the updated opponent model shows payment weight increased above 0.25
    And delivery weight decreased below 0.25
    And James can see the weight change from round 0 to round 1

  Scenario: Opponent model after multiple rounds shows convergence on supplier priorities
    Given a negotiation with Pacific Corrugated has completed 3 rounds
    And Pacific Corrugated improved payment in round 1, secured an offer in round 2, and improved price in round 3
    When James views the opponent model for Pacific Corrugated
    Then the inferred supplier weights show payment as the highest-weighted term
    And the weight history displays changes across all 3 rounds
    And James can verify the bot traded payment speed for lower price based on the weight distribution

  Scenario: Opponent model reflects Secure action by setting a utility floor
    Given a negotiation with Pacific Corrugated is in round 2
    And Pacific Corrugated clicks "Secure" on an offer at $13.20, Net 30, 14-day delivery, 12 months
    When James views the opponent model for Pacific Corrugated
    Then the model shows a utility floor corresponding to the secured offer
    And subsequent MESO offers do not go below that utility floor for the supplier

  # ---------------------------------------------------------------------------
  # 6. AUDIT TRAIL — Every bot decision traceable to configured rule
  # ---------------------------------------------------------------------------

  Scenario: Audit log records rule-based decision for a counter-offer
    Given a negotiation with Pacific Corrugated is in round 2
    When the bot generates a counter-offer of $12.80, Net 45, 10-day delivery, 18 months
    Then the audit log for round 2 contains:
      | Field           | Value                                                                    |
      | Decision        | Counter with new MESO set                                               |
      | James utility   | 0.68                                                                     |
      | Target utility  | 0.70 (from concession curve at round 2 of 5)                            |
      | Rule applied    | Supplier counter below target but above walk-away; generate new MESO set |
      | Concession used | Delivery relaxed from 7 to 10 days per concession priority 1             |

  Scenario: Audit log records auto-accept within configured range
    Given a negotiation with Pacific Corrugated is in round 3
    And the auto-accept threshold is a James utility of 0.75 or above
    When Pacific Corrugated's response yields a James utility of 0.78
    Then the bot auto-accepts the deal
    And the audit log records "Auto-accepted: James utility 0.78 exceeds auto-accept threshold 0.75"

  Scenario: Audit log records rejection of offer below walk-away
    Given a negotiation with Pacific Corrugated is in round 1
    When Pacific Corrugated's implied counter has price at $15.00 (above $14.50 walk-away)
    Then the bot rejects the counter
    And the audit log records "Rejected: price $15.00 exceeds walk-away limit $14.50"
    And the bot generates a new MESO set with explanation of the constraint

  Scenario: James reconstructs a full negotiation decision chain for VP review
    Given a negotiation with Pacific Corrugated closed at round 4 with terms $13.10, Net 30, 10-day delivery, 18 months
    When James opens the full audit trail for Pacific Corrugated
    Then every round shows the bot's offer, supplier action, resulting utility, and the rule that governed the decision
    And the final summary states "Accepted Net 30 because supplier offered price improvement to $13.10, which offset payment concession per configured trade-off weights (price 0.40 > payment 0.25)"

  # ---------------------------------------------------------------------------
  # 7. POST-DEAL REVIEW — Per-supplier outcome and aggregate statistics
  # ---------------------------------------------------------------------------

  Scenario: View per-supplier outcome after deal closure
    Given a negotiation with Pacific Corrugated closed with terms $13.10, Net 30, 10-day delivery, 18 months
    And the previous contract was $14.20, Net 60, 14-day delivery, 12 months
    When James views the outcome report for Pacific Corrugated
    Then the report shows:
      | Term     | Previous | Negotiated | Target  | vs Target     |
      | Price    | $14.20   | $13.10     | $12.50  | +$0.60 above  |
      | Payment  | Net 60   | Net 30     | Net 75  | 45 days worse |
      | Delivery | 14 days  | 10 days    | 10 days | at target     |
      | Contract | 12 mo    | 18 mo      | 12 mo   | 6 mo longer   |
    And James's utility score for the deal is 0.72
    And the opponent model final weights show payment 0.38, price 0.31, contract 0.18, delivery 0.13

  Scenario: View aggregate campaign statistics after 50 negotiations complete
    Given the "packaging, mid-spend, commodity" campaign has completed with 50 negotiations
    And 34 negotiations reached agreement
    And 8 negotiations ended with no deal
    And 5 negotiations were escalated to James
    And 3 negotiations stalled with no supplier response
    When James views the campaign summary
    Then the summary shows:
      | Metric                  | Value                |
      | Agreement rate          | 68% (34 of 50)       |
      | Average savings rate    | 3.2%                 |
      | Average rounds to close | 3.8                  |
      | Average James utility   | 0.71                 |
      | Escalation rate         | 10% (5 of 50)        |
      | Stall rate              | 6% (3 of 50)         |

  Scenario: Term-by-term comparison across the campaign
    Given the "packaging, mid-spend, commodity" campaign has 34 completed agreements
    When James views the term-by-term campaign analysis
    Then the analysis shows average outcome vs. target for each term across all 34 deals
    And terms where average outcome exceeded the walk-away but missed the target are flagged
    And the report identifies which terms were most frequently conceded

  # ---------------------------------------------------------------------------
  # 8. EXCEPTION HANDLING — Supplier escalation surfaces to James
  # ---------------------------------------------------------------------------

  Scenario: Supplier requests human contact during negotiation
    Given a negotiation with Pacific Corrugated is in round 3
    When Pacific Corrugated requests to speak with a human representative
    Then the negotiation is paused
    And an escalation is created for James with the full negotiation history
    And the dashboard shows Pacific Corrugated as "Escalated -- supplier requested human contact"

  Scenario: Negotiation reaches round limit without agreement
    Given a negotiation with Pacific Corrugated is in round 5 of 5
    And no agreement has been reached
    When the bot presents the final offer at the best remaining terms within James's constraints
    And Pacific Corrugated does not accept
    Then the negotiation state changes to "no deal"
    And the outcome is logged with the reason "Round limit reached, final offer rejected"
    And James is notified that Pacific Corrugated ended without agreement

  Scenario: Supplier raises an out-of-scope request
    Given a negotiation with Pacific Corrugated is in round 2
    When Pacific Corrugated's action implies a term outside the four configured terms
    Then the LLM layer acknowledges the request
    And the negotiation is flagged for James as "Out-of-scope request: exclusivity arrangement"
    And the bot continues the negotiation on the four configured terms

  Scenario: Supplier goes silent for longer than the configured timeout
    Given a negotiation with Pacific Corrugated is in round 2
    And the configured inactivity timeout is 72 hours
    When Pacific Corrugated has not responded for 72 hours
    Then the negotiation state changes to "stalled"
    And James receives a notification listing Pacific Corrugated as stalled
    And the dashboard shows the stall duration

  # ---------------------------------------------------------------------------
  # 9. GUARD RAILS — Bot never crosses walk-away limits
  # ---------------------------------------------------------------------------

  Scenario: Bot rejects a counter-offer that violates any single walk-away limit
    Given the walk-away limits are price $14.50, payment Net 30, delivery 21 days, contract 24 months
    And a negotiation with Pacific Corrugated is in round 2
    When Pacific Corrugated's implied counter includes payment at Net 15 (below walk-away of Net 30)
    Then the bot does not accept the counter
    And the bot generates a new MESO set that respects all walk-away limits
    And the audit log records "Blocked: payment Net 15 violates walk-away limit Net 30"

  Scenario: Bot never generates an offer beyond walk-away limits even at final round
    Given the walk-away limits are price $14.50, payment Net 30, delivery 21 days, contract 24 months
    And a negotiation with Pacific Corrugated is in round 5 of 5
    When the bot generates the final offer
    Then no term in the final offer exceeds the configured walk-away limit
    And the audit log confirms "Final offer generated within all walk-away constraints"

  Scenario: Deviation from configured limits is flagged immediately
    Given a negotiation with Pacific Corrugated is in round 3
    When the bot's calculated offer includes a term value that would cross a walk-away limit due to rounding
    Then the offer is blocked before being sent to the supplier
    And an alert is created for James stating "Offer blocked: delivery 22 days exceeds walk-away limit 21 days"
    And the bot recalculates the MESO set within valid bounds

  Scenario: Guard rail holds even when opponent model strongly signals supplier preference
    Given the walk-away limits are price $14.50, payment Net 30, delivery 21 days, contract 24 months
    And the opponent model infers Pacific Corrugated's payment weight at 0.45
    And a negotiation with Pacific Corrugated is in round 4
    When the bot generates a MESO set informed by the opponent model
    Then no offer includes payment terms below Net 30
    And the bot trades other terms (delivery, contract) to accommodate the supplier's payment preference
    And the audit log records "Opponent model payment weight 0.45 accommodated within walk-away constraints"
