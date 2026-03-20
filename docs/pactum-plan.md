# Pactum Technical Challenge

## Deadlines

- code submission: 24 March
- code must be in a public repo
- project presentation on jobfair: 27 March, 15 min presentation + 15 min Q&A

## Presentation deliverables

- solution in public repo
- locally running solution for the demo
- presentation slides
- pitch

## Parties

**James (operator):** A procurement manager who configures the AI bot to negotiate on his behalf. He optimizes for MAUT utility (weighted across all four terms, not just price) because he reports savings to his VP every quarter.

**Maria (supplier):** A packaging vendor who negotiates with the bot to get a better deal. She wants to get paid faster because she has equipment loans to cover every month.

The bot tries to find a deal that works for both.

## Scenario

Supplier's contract is expiring and she wants to re-negotiate a new deal. She is a returning supplier who has used the operator's AI negotiation platform before — the interface is familiar. This time the platform offers a new feature: MESO (Multiple Equivalent Simultaneous Offers) negotiations. She hopes MESO will surface better terms on payment speed. Buyer-initiated, bilateral renegotiation — no RFP, no competitive bidding.

## System

Hybrid architecture — rule-based negotiation engine handles offer calculation and scoring (MAUT utility functions), opponent model learns supplier preferences from structured UI actions (click signals, not free text), LLM drives the conversation framing (personalized communication style, configurable via system prompt).

## Metrics

Define one metric for each persona that the system will try to optimize for:

- operator (James): MAUT utility score¹ (weights: price 0.40, payment 0.25, delivery 0.20, contract 0.15)
- supplier (Maria): MAUT utility score¹ (weights: payment 0.35, price 0.30, contract 0.20, delivery 0.15)

## Back-end

- negotiation engine: takes operator config (weights, targets, limits), generates MESO offers — multiple offers with equal utility for James but different term distributions. Evaluates Maria's responses using MAUT utility score.
- state management: track negotiation state (pending, countered, accepted, rejected) across rounds.
- API: endpoints for the front-end — submit offer, get MESO offers, accept/reject, get negotiation state.
- opponent model: dynamic supplier weight vector, initialized at [0.25, 0.25, 0.25, 0.25], updated each round from structured UI actions (Improve/Trade/Accept/Secure). Combined with operator weights to generate MESO offers reflecting both sides' preferences.
- storage: SQLite — operator config, negotiation state, offer history.
- LLM layer: drives conversation with supplier, system prompt configurable communication style, auto-accepts deals within configured limits, uses engine for MESO generation and utility scoring.
- tests: TDD test suite for the negotiation engine.

## Front-end

- supplier UI: click-based guided flow — 3 offer cards per round, each with Accept (close deal), Improve (counter with direction), Secure (mark as fallback). No typing. "Improve" triggers inline trade-off prompt with clickable options. System generates new offers from structured signals.
- operator UI: James configures weights, targets, limits
- MAUT utility indicator: each party sees a progress bar showing how close the current offer is to their ideal (based on their own utility score, not the other party's)

---

¹ **MAUT utility score** — weighted sum of per-term achievement between walk-away and target: `Σ weight_i × (outcome_i - walk_away_i) / (target_i - walk_away_i)`. Produces a single 0–100% number. Based on Multi-Attribute Utility Theory (MAUT), the same linear additive utility function used in GENIUS/ANAC automated negotiation platforms.
