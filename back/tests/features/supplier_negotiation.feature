Feature: Supplier MESO Negotiation
  As Maria Chen, Sales & Account Manager at Pacific Corrugated Solutions,
  I want to negotiate my expiring contract through a click-based MESO interface
  So that I can secure better payment terms without lengthy back-and-forth.

  Current contract: $14.20/k boxes, Net 60, 14-day delivery, 12-month rolling.
  Maria's priority: payment terms (0.35) > price (0.30) > contract (0.20) > delivery (0.15).
  Interaction model: 3 offer cards per round, each with Accept / Improve / Secure actions.

  Background:
    Given Maria Chen of Pacific Corrugated Solutions has an expiring contract
    And her current terms are $14.20/k boxes, Net 60 payment, 14-day delivery, 12-month contract
    And the operator has configured a negotiation with 5 rounds
    And the operator weights are price 0.40, payment 0.25, delivery 0.20, contract 0.15

  # ---------------------------------------------------------------------------
  # 1. Opening Round
  # ---------------------------------------------------------------------------

  Scenario: Maria sees three MESO offer cards on arrival
    When Maria opens the negotiation link
    Then she sees a greeting that references Pacific Corrugated Solutions by name
    And she sees a greeting that references her expiring contract terms
    And she sees 3 offer cards displayed simultaneously
    And each card shows all 4 terms: price per thousand, payment terms, delivery days, and contract length
    And each card shows how each term differs from her current contract as a delta
    And she sees a round indicator showing "Round 1 of 5"
    And each card has exactly 3 action buttons: Accept, Improve, and Secure

  Scenario: All three opening offers show equal buyer utility but different term mixes
    When Maria opens the negotiation link
    Then the 3 offer cards each display a different combination of terms
    And no two cards have identical values on all 4 terms
    And each card displays a MAUT utility progress bar showing how close the offer is to Maria's ideal

  # ---------------------------------------------------------------------------
  # 2. Accept Flow
  # ---------------------------------------------------------------------------

  Scenario: Maria accepts an offer and sees a confirmation step before the deal closes
    Given Maria is on Round 2 of the negotiation
    And she sees 3 offer cards
    When she clicks "Accept" on the card showing $13.10/k, Net 30, 10-day delivery, 18-month contract
    Then she sees a confirmation prompt displaying the full terms she is about to accept
    And the confirmation prompt shows deltas from her original contract for each term
    And the prompt has two options: "Confirm Deal" and "Go Back"

  Scenario: Maria confirms acceptance and the deal closes
    Given Maria has clicked "Accept" on an offer and sees the confirmation prompt
    When she clicks "Confirm Deal"
    Then the negotiation state changes to "Accepted"
    And she sees a deal summary with the final agreed terms
    And she sees her final MAUT utility score as a percentage
    And she does not see any further action buttons for negotiation

  Scenario: Maria cancels acceptance and returns to the current round
    Given Maria has clicked "Accept" on an offer and sees the confirmation prompt
    When she clicks "Go Back"
    Then the confirmation prompt closes
    And she sees the same 3 offer cards with all actions still available

  # ---------------------------------------------------------------------------
  # 3. Improve Flow
  # ---------------------------------------------------------------------------

  Scenario: Maria clicks Improve on a term and sees trade-off options
    Given Maria is on Round 1 of the negotiation
    And she sees an offer card with Net 60 payment terms
    When she clicks "Improve" on the payment terms of that card
    Then she sees an inline prompt: "To improve payment terms, what would you trade?"
    And the prompt shows clickable options for the other 3 terms: price, delivery, and contract length
    And no free-text input field is displayed

  Scenario: Maria selects a trade-off and receives new offers
    Given Maria has clicked "Improve" on payment terms
    And she sees the trade-off prompt with options for price, delivery, and contract length
    When she clicks "delivery" as the term to trade
    Then the system shows a brief loading state indicating offers are being generated
    And the round advances to Round 2 of 5
    And she sees 3 new offer cards
    And the new cards show improved payment terms compared to the previous round
    And the new cards show longer or equal delivery times compared to the previous round

  Scenario: Maria dismisses the trade-off prompt without selecting
    Given Maria has clicked "Improve" on a term and sees the trade-off prompt
    When she clicks outside the prompt or clicks a close button
    Then the trade-off prompt closes
    And the offer cards remain unchanged
    And the round does not advance

  # ---------------------------------------------------------------------------
  # 4. Secure Flow
  # ---------------------------------------------------------------------------

  Scenario: Maria secures an offer as a fallback and continues negotiating
    Given Maria is on Round 2 of the negotiation
    And she sees an offer card showing $13.20/k, Net 30, 14-day delivery, 12-month contract
    When she clicks "Secure" on that card
    Then the card is visually marked as her secured fallback
    And she sees a label such as "Your secured offer" on the marked card
    And the other 2 offer cards remain available with all 3 actions
    And she can still click "Improve" on any card to continue negotiating

  Scenario: Maria secures a new offer replacing a previously secured one
    Given Maria has already secured an offer in a previous round
    When she clicks "Secure" on a different offer card in a later round
    Then the new card is marked as her secured fallback
    And the previously secured offer is no longer marked
    And only one offer is marked as secured at any time

  Scenario: Maria's secured offer is available at the final round
    Given Maria has secured an offer showing $13.20/k, Net 30, 14-day delivery, 12-month contract
    And the negotiation reaches Round 5 of 5
    Then her secured offer is displayed alongside the final round offers
    And the secured offer still shows the terms from when it was secured

  # ---------------------------------------------------------------------------
  # 5. Multi-Round Progression
  # ---------------------------------------------------------------------------

  Scenario: Offers shift toward faster payment after Maria signals payment preference
    Given Maria is on Round 1
    When she clicks "Improve" on payment terms and trades delivery
    And the system generates Round 2 offers
    Then at least 2 of the 3 new offer cards show faster payment terms than Round 1
    And the delivery times in the new offers are equal to or longer than Round 1

  Scenario: Offers shift toward lower price after Maria signals price preference
    Given Maria improved payment in Round 1 and traded delivery
    And she is now on Round 2
    When she clicks "Improve" on price and trades contract length
    And the system generates Round 3 offers
    Then the Round 3 offers show lower prices than Round 2
    And the Round 3 offers show longer or equal contract lengths than Round 2
    And the Round 3 offers maintain the payment term improvements from Round 2

  Scenario: Successive rounds show diminishing concessions
    Given Maria has been negotiating for 4 rounds, each time clicking "Improve" on price
    When the system generates Round 5 offers
    Then the price improvement from Round 4 to Round 5 is smaller than the improvement from Round 1 to Round 2

  # ---------------------------------------------------------------------------
  # 6. Trust Signals
  # ---------------------------------------------------------------------------

  Scenario: First response references Maria's specific company and terms
    When Maria opens the negotiation link
    Then the greeting text contains "Pacific Corrugated"
    And the greeting text references specific current terms: "$14.20" and "Net 60"
    And the greeting does not contain generic phrases such as "I understand your concerns"
    And the greeting does not contain "Let me help you with that"

  Scenario: Offer cards show deltas from current contract
    When Maria sees the opening offer cards
    Then each card shows a delta indicator for each term compared to her current contract
    And terms that are better for Maria are visually distinguished from terms that are worse
    And the deltas use concrete values, not vague descriptions

  Scenario: Bot response after Improve references the specific action Maria took
    Given Maria is on Round 1
    When she clicks "Improve" on payment terms and trades delivery
    Then the Round 2 response text references her specific action
    And the response mentions payment terms and delivery by name
    And the response does not repeat the same text it used in Round 1

  Scenario: Loading state signals real computation, not instant scripted response
    Given Maria has just submitted an Improve action with a trade-off selection
    When the system is generating new offers
    Then she sees a visible processing state such as "Reviewing your terms..."
    And the processing state lasts at least 2 seconds
    And the processing state is replaced by the new offer cards when ready

  # ---------------------------------------------------------------------------
  # 7. Round Limit
  # ---------------------------------------------------------------------------

  Scenario: Maria sees the round counter on every round
    Given Maria is on Round 3 of a 5-round negotiation
    Then she sees "Round 3 of 5" displayed prominently on the screen

  Scenario: Final round presents a last offer with no further negotiation
    Given Maria is on Round 5 of 5
    Then she sees a message indicating this is the final round
    And she sees offer cards representing the best terms the system can provide
    And the "Improve" action is not available on the final round cards
    And each card has only "Accept" as an action
    And if Maria has a secured offer, it is also displayed as an option to accept

  Scenario: Maria accepts the final round offer
    Given Maria is on Round 5 of 5
    When she clicks "Accept" on the final offer
    Then she sees the same confirmation prompt as a normal acceptance
    And upon confirming, the deal closes with the final terms

  Scenario: Maria rejects all final round offers
    Given Maria is on Round 5 of 5
    And she has no secured offer
    When she does not click "Accept" on any card and clicks "End Negotiation"
    Then the negotiation state changes to "No Deal"
    And she sees a summary showing that no agreement was reached
    And the summary preserves the history of terms discussed

  Scenario: Maria falls back to her secured offer on the final round
    Given Maria is on Round 5 of 5
    And she has a secured offer showing $13.20/k, Net 30, 14-day delivery, 12-month contract
    When she clicks "Accept" on her secured offer
    Then she sees the confirmation prompt with the secured offer terms
    And upon confirming, the deal closes at $13.20/k, Net 30, 14-day delivery, 12-month contract

  # ---------------------------------------------------------------------------
  # 8. Edge Cases -- Five UI States (Hurff)
  # ---------------------------------------------------------------------------

  # -- Ideal State --

  Scenario: Ideal state - full negotiation with 3 cards and all actions available
    Given Maria is on any round between 1 and 4
    Then she sees exactly 3 offer cards
    And each card shows all 4 terms with values
    And each card has Accept, Improve, and Secure actions
    And she sees the round counter
    And she sees her MAUT utility progress indicator

  # -- Empty State --

  Scenario: Empty state - Maria opens a negotiation link before offers are configured
    Given the operator has not yet configured negotiation terms for Maria
    When Maria opens the negotiation link
    Then she sees a message explaining that the negotiation is not yet ready
    And the message provides context such as "Your contract renegotiation is being prepared"
    And she does not see any offer cards or action buttons
    And she sees a way to return later or be notified when ready

  Scenario: Empty state - no secured offer exists when referenced
    Given Maria has not secured any offer during the negotiation
    And she is on Round 5 of 5
    Then the secured offer area is not displayed
    And no empty placeholder or broken layout appears where a secured offer would be

  # -- Error State --

  Scenario: Error state - network failure during offer generation
    Given Maria has clicked "Improve" on a term and selected a trade-off
    When the system fails to generate new offers due to a network error
    Then she sees an error message explaining that offers could not be loaded
    And the message is written in plain language, not a technical error code
    And she sees a "Try Again" button to retry the action
    And her previous offer cards remain visible as a fallback
    And the round does not advance

  Scenario: Error state - session expires during negotiation
    Given Maria has been inactive on the negotiation page for an extended period
    When she attempts an action after her session has expired
    Then she sees a message explaining that her session has timed out
    And she sees an option to resume the negotiation from where she left off
    And her progress and any secured offer are preserved

  Scenario: Error state - Maria clicks Accept but server fails to record the deal
    Given Maria has clicked "Accept" and then "Confirm Deal"
    When the server fails to record the acceptance
    Then she sees an error message such as "We could not finalize your deal. Your terms are saved."
    And she sees a "Try Again" button
    And the system does not show a false confirmation of a completed deal

  # -- Partial State --

  Scenario: Partial state - only 2 of 3 offers generated successfully
    Given the system attempted to generate 3 MESO offers for a round
    When only 2 offers were generated within the timeout period
    Then Maria sees 2 offer cards instead of 3
    And all actions are available on the 2 displayed cards
    And a subtle note indicates that fewer options are available this round
    And the negotiation continues normally

  Scenario: Partial state - one term is missing from an offer card
    Given the system generated an offer where one term could not be calculated
    When Maria sees the offer card
    Then the card displays the 3 available terms
    And the missing term shows a placeholder such as "Calculating..."
    And the Accept action is disabled on that card until all terms are present
    And Improve and Secure remain available for the visible terms

  # -- Loading State --

  Scenario: Loading state - initial page load shows skeleton cards
    When Maria opens the negotiation link
    Then she sees 3 skeleton card placeholders while offers are loading
    And the skeleton cards indicate where terms and actions will appear
    And the greeting area shows a loading indicator
    And no interactive actions are available until loading completes

  Scenario: Loading state - new round offers are being generated
    Given Maria has submitted an Improve action with a trade-off
    When the system is generating the next round of offers
    Then the previous offer cards fade or dim to indicate they are stale
    And she sees a processing indicator with text such as "Reviewing your terms..."
    And action buttons are disabled during the loading state
    And the loading state resolves to 3 new offer cards or an error state
