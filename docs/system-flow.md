# Deal Flow — MESO Negotiation

Buyer-initiated, bilateral renegotiation with MESO (Multiple Equivalent Simultaneous Offers).

## 1. Configuration (James, before negotiation)

- Sets per-term: target (ideal) ←→ walk-away (limit)
- Sets weights: price 0.40 | payment 0.25 | delivery 0.20 | contract 0.15

## 2. Opening (Engine → Maria)

Engine generates opening MESO set and serves it via API. React UI renders 3 offer cards. All offers have equal MAUT utility for James but different term mixes.

Example:

|          | Offer A    | Offer B    | Offer C    |
|----------|------------|------------|------------|
| Price    | $48/unit   | $50/unit   | $51/unit   |
| Payment  | Net 60     | Net 30     | Net 15     |
| Delivery | 5 days     | 7 days     | 10 days    |
| Contract | 24 months  | 18 months  | 12 months  |
| James    | 72%        | 72%        | 72%        |
| Maria    | 55%        | 68%        | 61%        |

## 3. Response (Maria picks one of three actions per card)

- **Agree** → close deal, go to step 5. Opponent model reinforces all attribute weights.
- **Improve terms** → signals preference for that card's strength dimension. Opponent model: strength dimension weight ↑, other weights ↓. Engine generates new MESO set directly — no trade-off prompt. → go to step 4
- **Secure as fallback** → marks offer as reservation value. Opponent model: records acceptable utility threshold. Negotiation continues — Maria can still Improve other cards.

Maria's actions are structured clicks, not free text. Every action maps deterministically to an opponent model update.

## 4. Negotiation Loop (repeats until deal, walk-away, or round limit)

Hard round limit R (configurable, recommended 5–8). Maria sees "round N of R" — transparent deadline.

Concession strategy: diminishing concessions (Boulware). Target utility per round: `target(r) = walk_away + (opening - walk_away) × (1 - r/R)^β` where β > 1.

Opponent model: The engine maintains a supplier weight vector, initialized at [0.25, 0.25, 0.25, 0.25]. Each round, Maria's click actions update the weights (Improve → strength dimension weight ↑, others ↓; Agree → reinforce all; Secure → set utility floor). The engine combines operator weights (fixed, set by James) with inferred supplier weights to generate MESO offers that reflect both sides' preferences.

Engine evaluates each round:

- **Maria clicks Agree** → deal closes, go to step 5
- **Maria clicks Improve** → Engine generates new MESO set, adjusting toward the card's strength dimension. API serves updated offers to React UI. → back to step 3
- **Maria clicks Secure** → Engine records utility floor. Maria can still Improve or Agree. → back to step 3
- **Round R reached** → Final offers at best remaining terms. "Improve terms" removed from UI. Agree or no deal.

## 5. Outcome

**Deal reached:**
- Final terms saved to offer history
- Both parties see final MAUT scores on their utility indicators
- State → accepted

**No deal:**
- State → rejected
- History preserved for future renegotiation

## System Diagram

```
                    ┌─────────────────────────────────┐
                    │   operator config                │
                    │   (weights, targets, limits)     │
                    └───────────────┬─────────────────┘
                                    │
                                    ▼
                    ┌─────────────────────────────────┐
                    │   utility model + constraints    │
                    └───────────────┬─────────────────┘
                                    │
                ┌───────────────────┼──────────────────┐
                │                   ▼                  │
                │   ┌─────────────────────────────┐    │
                │   │  candidate offer generator   │    │
                │   │  (operator config +           │    │
                │   │   opponent model weights)     │    │
                │   └──────────────┬──────────────┘    │
                │                  ▼                   │
                │   ┌─────────────────────────────┐    │
                │   │  offer evaluator             │    │
                │   │  (MAUT utility + policy)     │    │
                │   └──────────────┬──────────────┘    │
                │                  ▼                   │
                │   ┌─────────────────────────────┐    │
                │   │  MESO selector               │    │
                │   │  (pick top 3 equivalent)     │    │
                │   └──────────────┬──────────────┘    │
                │                  │                   │
                │          NEGOTIATION ENGINE          │
                └──────────────────┼───────────────────┘
                                   │
                        ┌──────────┴──────────┐
                        │   REST API           │
                        │   (JSON offer cards) │
                        └──────────┬──────────┘
                                   │
                                   ▼
                ┌──────────────────────────────────┐
                │  React card UI                    │
                │  3 cards: Best Price /             │
                │  Most Balanced / Fastest Payment   │
                └──────────────┬───────────────────┘
                               │
                ┌──────────────────────────────┐
                │  supplier clicks:             │
                │  Agree / Improve / Secure     │
                └──────────────┬───────────────┘
                               │
                               ▼
                ┌──────────────────────────────────┐
                │  opponent model update            │
                │  (click action → weight update)   │
                │  Improve → w_strength ↑, others ↓ │
                │  Agree   → reinforce all          │
                │  Secure  → set utility floor      │
                └──────────────┬───────────────────┘
                               │
                               ▼
  ┌──────────────────────────────────────────────────────────┐
  │  response evaluator (MAUT utility + strategy rules)      │
  │                                                          │
  │  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐ │
  │  │ Agree          │  │ Improve       │  │ round R       │ │
  │  │ (close deal)   │  │ (new MESO)    │  │ (final offer) │ │
  │  └──────┬─────────┘  └───────┬───────┘  └──────┬────────┘ │
  └─────────┼────────────────────┼──────────────────┼─────────┘
            │                    │                  │
            ▼                    │                  ▼
     ┌────────────┐              │          ┌──────────────┐
     │  ACCEPTED  │              │          │ FINAL OFFERS │
     └────────────┘              │          │ agree or     │
                                 │          │ no deal      │
                        ┌────────┘          └──────────────┘
                        │
                        │  ▲ loop: rounds 1..R
                        │  │ (diminishing concessions,
                        │  │  offer history,
                        │  │  preference signal)
                        ▼  │
              ┌─────────────────────────────┐
              │  candidate offer generator   │
              │  (informed by opponent model │
              │   weights + operator config) │
              └──────────────────────────────┘
```

## Sources

- [Multi-attribute utility - Wikipedia](https://en.wikipedia.org/wiki/Multi-attribute_utility) — MAUT theory underlying the utility scoring model.
- [MAUT in Decision Analysis - Springer](https://link.springer.com/chapter/10.1007/978-1-4939-3094-4_8) — formal treatment of multi-attribute utility functions.
- [GENIUS: An Integrated Environment for Supporting the Design of Generic Automated Negotiators](https://eprints.soton.ac.uk/373208/1/Genius_20-_20An_20Integrated_20Environment_20for_20Supporting_20the_20Design_20of_20Generic_20Automated_20Negotiators.pdf) — negotiation platform using linear additive utility (same as our MAUT scoring).
- [Automated Negotiating Agents Competition (ANAC)](https://ii.tudelft.nl/nego/node/7) — competition rules, round/deadline protocols, agent evaluation by average utility.
- [Scoring a Deal: Valuing Outcomes in Multi-Issue Negotiations - Columbia](https://www.columbia.edu/~ms4992/negotiations/Scoring%20a%20Deal.pdf) — weighted utility scoring for multi-issue negotiation.
- [Concession Strategy Adjustment in Automated Negotiation - Springer](https://link.springer.com/chapter/10.1007/978-981-99-0561-4_8) — concession strategies, convergence at 6–8 rounds.
- [Multi-Issue Negotiation with Deadlines - arXiv](https://arxiv.org/pdf/1110.2765) — deadline effects on bilateral negotiation outcomes.
- [A Negotiator's Backup Plan: Optimal Concessions with a Reservation Value - arXiv](https://arxiv.org/html/2404.19361) — optimal concession curves and Boulware strategy.
- [Why Negotiators Should Reveal Their Deadlines - Moore (2004)](https://www.researchgate.net/publication/229564717_Why_Negotiators_Should_Reveal_Their_Deadlines_Disclosing_Weaknesses_Can_Make_You_Stronger) — transparent deadlines improve outcomes.
- [The Unexpected Benefits of Final Deadlines in Negotiation - Moore (2004)](https://www.sciencedirect.com/science/article/abs/pii/S0022103603000908) — moderate deadlines improve negotiation efficiency.
- [Bargaining Under Time Pressure from Deadlines - Cambridge](https://www.cambridge.org/core/journals/experimental-economics/article/bargaining-under-time-pressure-from-deadlines/F388EC46629F094DDB48A96AE00F8DCC) — concession rate increases near deadline.
