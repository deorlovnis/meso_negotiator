# Procurement Deal Flow — Both Sides

## Overview

Maria's contract is expiring. She's used the platform before. James initiates renegotiation. New this time: MESO offers with click-based interaction and a dynamic opponent model that learns Maria's preferences from her actions.

```
                    James (operator)                          Maria (supplier)
                    ────────────────                          ────────────────

  CONTRACT LIFE    [  running on old terms for 3 years  ]    [  same old terms, nobody calls  ]
                            │                                           │
  TRIGGER          "Time to renegotiate 400 suppliers"       (doesn't know yet)
                            │                                           │
  PREPARATION      Sets targets, limits, weights per         (doesn't know yet)
                   cohort in the system
                            │                                           │
  FIRST CONTACT    Bot sends renegotiation invite             Gets notification — "contract is up"
                            │                                           │
  OPENING          Bot presents first offer                   Compares to previous terms:
                   (James's configured anchor)                "Are they squeezing me or is there room?"
                            │                                           │
  ROUNDS 1-R       Evaluates counters, generates              Counters, accepts, or walks.
                   MESO with diminishing concessions.         Picks from 2-3 options per round.
                   Maria sees "round N of R".                 Knows the deadline upfront.
                            │                                           │
  CLOSE            Round R: final offer (best terms           Accepts final offer or disengages.
                   the engine can give). No escalation.
                            │                                           │
  POST-DEAL        Reviews outcome vs. targets                New contract terms, adjusts planning
```

## Phases

### 1. Preparation

James sets one config for Maria's cohort ("packaging, mid-spend, commodity"):

| | Opening | Target | Walk-away |
|---|---|---|---|
| Price | $11.50 | $12.50 | $14.50 |
| Payment | Net 90 | Net 75 | Net 30 |
| Delivery | 7 days | 10 days | 14 days |
| Contract | 6 months | 12 months | 24 months |

Weights: price 0.40, payment 0.25, delivery 0.20, contract 0.15.

Maria's mental config (unknown to the engine): "I need Net 30, I'll give on delivery, price below $12 is a dealbreaker."

**Engine implication:** Maria's preferences must be *inferred* from her responses. This is why MESO exists.

### 2. Opening (round 0)

Bot serves James's configured opening. Deterministic — no engine logic yet.

Maria compares to her previous contract ($14.20/Net 60). She knows the platform but hasn't seen MESO before — presenting multiple offers is a new interaction pattern that may raise questions ("why three options now?").

### 3. Negotiation rounds

```
Maria clicks → Opponent model updates → Engine generates → New MESO set

CLICK:     Accept (close deal) | Improve term + trade term | Secure (mark fallback)
UPDATE:    Improve → w_term ↑ | Trade → w_term ↓ | Accept → reinforce all | Secure → set floor
GENERATE:  Combine operator weights + opponent model → target utility from concession curve → 2-3 MESO offers
```

Four mechanisms make this work:

- **Hard round limit (R)** — configurable, recommended 5–8 rounds. Maria sees "round N of R" in each response. Transparent deadline encourages early preference revelation (Moore, 2004). Round R is a final offer — no escalation to operator.
- **Diminishing concessions (Boulware)** — target utility drops each round: `target(r) = walk_away + (opening - walk_away) × (1 - r/R)^β` where β > 1. Concedes slowly in early rounds, faster near the deadline.
- **MESO as preference extraction** — equal-utility offers with different term distributions. Maria's click actions (Improve/Trade/Secure) reveal what she values through structured signals, not free text.
- **Trade-off exploitation** — James weights price (0.40), Maria weights payment (0.35). The bot trades payment speed (cheap for James) for lower price (cheap for Maria). Both gain utility.
- **Opponent model** — supplier weight vector initialized at [0.25, 0.25, 0.25, 0.25], updated each round from click actions. Combined with James's fixed weights to generate offers reflecting both sides. Eliminates LLM interpretation from the preference-learning loop.

### 4. Failure modes

**Hard constraint violation.** Maria asks $15.00 (above $14.50 walk-away). Engine rejects with explanation, counters with MESO. Normal in rounds 1-2.

**Silence.** Maria submits one counter, then disappears. Could mean: CFO approval needed, busy, shopping the offer. Engine needs a timeout state — silence ≠ rejection.

**Out-of-scope request.** "Can we split delivery?" or "What about exclusivity?" Outside the four terms. LLM layer redirects or escalates.

**Round limit reached.** Final round presents the best terms the engine can give within James's constraints. If Maria rejects, negotiation ends. No escalation to operator.

**Walk-away.** "Renew at current terms or we find a new buyer." Valid outcome. Engine reports which constraints were incompatible.

### 5. Demo scenario

| Round | Bot | Maria's Action | Opponent Model Learns |
|-------|-----|----------------|----------------------|
| 0 | Opens: $11.50, Net 90, 7-day, 6-mo | — | Nothing (weights: 0.25 each) |
| 1 | 3 MESO offers | Clicks "Improve payment" on Offer A, trades delivery | w_payment ↑, w_delivery ↓ |
| 2 | 3 new MESO offers (shifted toward faster payment) | Clicks "Secure" on Offer B ($13.20/Net 30/14-day/12-mo) | Utility floor set at Offer B |
| 3 | 3 offers optimized around Net 30 anchor | Clicks "Improve price" on Offer A, trades contract | w_price ↑, w_contract ↓ |
| 4 | $13.10/Net 30/10-day/18-mo | Clicks "Accept" | Deal closed. All weights reinforced. |

Result: both sides ahead of status quo ($14.20/Net 60). James got lower price, Maria got Net 30. The bot traded payment speed for price.

**Realism note:** Walmart pilot showed 1.5% average savings on tail spend; 3% after expansion (HBR). This demo shows 7.7% — plausible for an individual deal with complementary priorities, but not the average.

### 6. Post-deal

James sees: "Pacific Corrugated: closed round 4, utility 0.72, price improved 7.7%, payment conceded Net 60→30. Opponent model: supplier weighted payment (0.38) > price (0.31) > contract (0.18) > delivery (0.13)." Every decision traces to the rule that produced it.

## What the scenario simplifies away

Because Maria is a returning supplier on a familiar platform:

- **Engagement gap** — 64% of Walmart pilot suppliers reached agreement; 36% didn't (breakdown between "ignored" and "engaged but no deal" is unknown). Maria's familiarity eliminates this. (HBR)
- **Trust barrier** — 75% of Walmart suppliers preferred the chatbot; 83% found it easy to use (PYMNTS). Maria knows the platform but MESO is new to her — partial trust, not full trust.
- **Supplier-initiated triggers** — In reality, suppliers also initiate renegotiations (especially price increase claims — Roland Berger notes these are "persistent and elevated" since 2021). Our scenario is buyer-initiated.

## ANAC vs. this scenario

In ANAC, both sides are bots maximizing hidden utility functions. Here, one side is human:

1. Maria may reject a better deal because the bot's tone annoyed her
2. Language quality and presentation are part of the negotiation
3. The engine must be explainable in real-time

## Benchmarks for the presentation

| Metric | Walmart pilot | At scale | Our demo |
|--------|--------------|----------|----------|
| Agreement rate | 64% (89 suppliers, Canada) | 68% (US/Chile/South Africa) | 1 deal (happy path) |
| Average savings | 1.5% | 3% | 7.7% (individual deal) |
| Cycle time | 11 days avg | — | 4 rounds |
| Bot preference | — | 75% prefer bot | Assumed (returning supplier) |
| Payment terms | Extended to 35 days avg | — | Net 60 → Net 30 (conceded) |
| Scale | 89 suppliers | 2,000 at once | 1 supplier |

All Walmart data from HBR (2022) and PYMNTS (2023).

## Sources

- [How Walmart Automated Supplier Negotiations](https://hbr.org/2022/11/how-walmart-automated-supplier-negotiations) — HBR, 2022. Primary source: 64% pilot agreement, 68% at scale, 1.5%→3% savings, 89 suppliers, 11-day cycle, 35-day payment terms.
- [Walmart Finds 75% of Vendors Prefer Negotiating With Chatbot](https://www.pymnts.com/news/artificial-intelligence/2023/walmart-finds-75-percent-vendors-prefer-negotiating-with-chatbot/) — PYMNTS, 2023. 75% bot preference, 83% ease of use, 68% deal closure, 2000 suppliers.
- [Pactum's AI in Contract Negotiations: Walmart and Maersk](https://store.hbr.org/product/pactum-s-ai-in-contract-negotiations-walmart-and-maersk/TB0756) — HBS Case Study TB0756.
- [Brave new procurement deals](https://www.sciencedirect.com/science/article/pii/S1478409225000214) — Journal of Purchasing and Supply Management, 2025.
- [Managing supplier claims for price increases](https://www.rolandberger.com/en/Insights/Publications/Managing-supplier-claims-for-price-increases-in-the-procurement-process.html) — Roland Berger. Supplier-initiated renegotiation trends.
- [Understanding Agentic AI in Procurement](https://pactum.com/understanding-agentic-ai-in-procurement-how-autonomous-ai-has-been-transforming-supplier-deals/) — Pactum, 2025.
