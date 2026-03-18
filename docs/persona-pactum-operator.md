# User Persona: Enterprise Procurement Operator Deploying AI Negotiation

---

## Identity

**Name:** James Kowalski
**Role:** Category Manager, Indirect Procurement — RetailCo National (fictional retailer)
**Company:** Large-format national retail chain (~$18B revenue, 800+ stores)
**Type:** The operator who buys Pactum's product and configures it to run. One procurement professional responsible for 400+ tail-spend suppliers he will never have bandwidth to negotiate with individually.

> "I have 400 suppliers I haven't touched in 18 months. If this bot actually holds the line on our targets and doesn't just give everything away to keep suppliers happy, it pays for itself in week one."

---

## Background

James has been in indirect procurement for 11 years — consumables, packaging, operational supplies, facility services. He manages the "Routine" and "Leverage" quadrants of the Kraljic matrix: the long tail where volume is modest per supplier but aggregate savings potential is real and admin cost is high.

He is technically proficient but not an engineer. He has configured supplier portals in Ariba and Coupa. He understands procurement strategy deeply — minimum acceptable terms, target terms, supplier segmentation, BATNA. He can read a negotiation log. He knows what a concession rate looks like.

He has a VP he reports to. That VP will ask: "What did we save last quarter? Which suppliers are at risk?" James needs to be able to answer those questions with data the system produces.

---

## Context

- RetailCo works with 2,000+ tail-spend suppliers across indirect categories
- James's direct coverage: ~400 packaging and operational supplies vendors
- Average contract value in his portfolio: $800K–$6M/year per supplier
- Estimated uncaptured savings from stale tail-spend contracts: 3–5% annually (~$4–8M across his book)
- Current state: 60% of his suppliers are on unchanged terms from 3+ years ago. Nobody has called them.
- He piloted Pactum on a 50-supplier cohort 6 months ago — payment terms improved on 38 of 50, average savings 3.2%. He's now rolling out to the full 400.
- The current packaging contract terms (supplier side): $14.20/k boxes, Net 60 payment, 14-day delivery, 12-month rolling — exactly what Pacific Corrugated has been sitting on

---

## What He Cares About

### His four highest-priority outcomes:

| Outcome | Why It Matters |
|---------|----------------|
| **Aggregate savings rate** | His quarterly business review asks for a number. Not "the bot works." A number. 3% across 400 suppliers is career-defining. |
| **Bot executes strategy, not its own judgment** | If the system accepts terms outside his configured limits, he's on the hook. Every exception needs a paper trail he can show his VP. |
| **Supplier satisfaction stays above threshold** | Unhappy suppliers deliver late, cut quality, deprioritize RetailCo orders. The point isn't to squeeze — it's to optimize. He knows the difference. |
| **Time back to him** | The whole point of the tool is that he doesn't have to spend 20 hours a week in negotiation email threads with 400 suppliers. If configuring the bot takes more time than just doing the negotiations, the ROI collapses. |

---

## His Configuration Workflow

James's interaction with the system is NOT the negotiation itself — it's the setup, monitoring, and review layer. His workflow:

1. **Segment suppliers** — Tier suppliers into negotiation cohorts by spend volume, category, and strategic risk. High-volume suppliers get tighter limits; commodity tail-spend gets more aggressive targets.

2. **Set terms and limits per cohort** — For each negotiated term (price, payment, delivery, contract length): set the opening position, target, and walk-away limit. The bot must not cross the walk-away, ever.

3. **Set concession weights** — Tell the bot which terms he's willing to trade and at what rate. "I'll give on delivery time before price. Payment terms are last resort." This is his procurement strategy, translated into config.

4. **Launch the cohort** — Deploy the negotiation campaign to 50–200 suppliers simultaneously. Each supplier gets their own thread; the bot runs them in parallel.

5. **Monitor in-flight** — Dashboard view of active negotiations: how many are in round 1, 2, 3, how many have reached agreement, how many are stuck, which are at risk of stalling.

6. **Review outcomes** — Post-campaign: per-supplier outcome, aggregate statistics, term-by-term comparison vs. target. Flag any anomalies — did the bot give away something it shouldn't have?

7. **Handle exceptions** — A small percentage of suppliers will push back hard, escalate, or request human contact. The system surfaces these for James to handle manually.

---

## Trust Concerns (Operator Trust Formation Sequence)

Unlike Maria (who fears incompetence), James fears **loss of control**. His trust sequence:

### Stage 1 — "Can I actually configure this to my strategy?"

James needs to see that the configuration system is expressive enough to encode his real procurement strategy. Not a fixed template with a few sliders — but genuine term-level weights, limits, and cohort segmentation. If the config is too coarse, the bot will either be too aggressive (damaging supplier relationships) or too soft (leaving savings on the table).

**Trust signal:** He can configure targets, limits, and concession weights per term per cohort — and the UI makes it clear what the bot will and won't do.

### Stage 2 — "Does the bot actually follow the config?"

He needs proof the system doesn't improvise. If he sets a walk-away of Net 30 on payment terms and the bot agrees to Net 45, that's a policy violation, not a negotiation win. Every deviation must be surfaced and explained.

**Trust signal:** Audit log showing every decision with the rule that drove it. Zero unexplained deviations from configured limits.

### Stage 3 — "Can I explain any outcome to my VP?"

For any supplier negotiation, James must be able to reconstruct: what the bot offered, why, what the supplier countered, why the bot accepted or rejected, and what rule governed each decision.

**Trust signal:** Per-negotiation decision log in plain English. "Accepted Net 45 because supplier offered 7-day delivery improvement, which offset payment terms concession per configured trade-off weights."

### Stage 4 — "Are the aggregate results better than doing nothing?"

After 50–100 negotiations, is the actual savings rate meeting his forecast? Are suppliers completing the process (high completion = they found value too)? Is any category performing worse than baseline?

**Trust signal:** Campaign-level analytics: savings rate, agreement rate, average rounds to close, term-by-term outcomes vs. target, supplier satisfaction scores.

---

## Pain Points

| Pain Point | Evidence |
|---|---|
| **Bandwidth wall** | 400 suppliers, 20 working hours/week on indirect procurement, 3 competing priorities. Individual negotiation is mathematically impossible. |
| **Stale contracts** | 60% of his book is on unchanged terms. He knows money is sitting there. He just can't reach it without scale. |
| **No visibility into what the bot does** | The core anxiety: "If I can't see what happened, I can't defend it. And if I can't defend it, I don't use it." |
| **Supplier relationship risk** | Procurement automation horror stories. He's heard about bots that carpet-bomb suppliers with aggressive first offers, blow up relationships, get escalated to the CPO. He will not be that story. |
| **Configuration friction** | Every tool he's set up in procurement required 3 weeks of IT, 2 workshops with a consultant, and a configuration guide he'll never read again. He needs to configure 400 suppliers before the end of Q2. |
| **Exception handling overhead** | If 10% of suppliers escalate to him manually, that's 40 conversations — right back to where he started. He needs the system to handle more than it hands off. |

---

## What Makes This Persona Right for the Challenge

### 1. He is Pactum's actual customer

Pactum doesn't sell to Maria. It sells to James. The people who write checks for Pactum licenses are category managers and procurement directors at Walmart, Maersk, and Honeywell — the James Kowalskis of the world. Demonstrating understanding of his needs signals real product depth.

### 2. His concerns expose the full system architecture

Maria's trust concerns shape the supplier-facing UI. James's trust concerns shape the operator configuration layer, audit log, and analytics dashboard. A submission that addresses both sides shows the candidate understands Pactum's product as a **two-sided system**, not just a chatbot.

### 3. Configurability is the hardest product problem

Building a negotiation bot that works for one supplier is a demo. Building one whose behavior can be precisely configured for 400 supplier cohorts with different strategies is a product. James's configuration workflow forces that distinction into the open.

### 4. The auditability requirement is non-trivial

"Why did you accept those terms?" must have an answer the system produces automatically, in language a VP can read, traceable to the rule that was configured. This is a real system design challenge — not just a UI challenge.

### 5. It frames the MESO output correctly

Maria sees the bot's offers as the product. James sees the aggregate outcome distribution as the product. Both are right. The system must serve both simultaneously without compromising either.

---

## Strategic Recommendation for the Team

The Pactum challenge brief asks for a **supplier-facing negotiation UI**. That is the primary deliverable. But a submission that only addresses the supplier side leaves the most important signal on the table.

Pactum's actual differentiator is not the negotiation chat. It is that the chat produces **governed, configurable, auditable outcomes at scale** — outcomes an enterprise procurement manager can stand behind in front of their VP.

**Recommended approach:** Build the supplier UI as the primary demo surface. But in the submission, include mockups or a design section that addresses:

- The operator configuration screen: how James sets targets, limits, and weights per cohort
- The in-flight monitoring dashboard: campaign health, agreement rate, stuck negotiations
- The per-negotiation audit log: decision-by-decision trace in plain language
- A one-screen outcome report showing aggregate campaign results

This does not require building those screens — a set of described mockups in the submission write-up is sufficient. The evaluator's reaction will be: "This candidate understands our whole product, not just the demo scenario." That is the signal that separates a strong submission from a winner.

---

## Operator Configuration Schema (Counter-Party to Maria)

The configuration James would set for the Pacific Corrugated corrugated packaging cohort:

| Term | Opening | Target | Walk-Away | Direction | Weight |
|------|---------|--------|-----------|-----------|--------|
| Price ($/k boxes) | $11.50 | $12.50 | $14.50 | Lower is better | 0.40 |
| Payment terms (days) | 90 | 75 | 30 | Higher is better (pay later) | 0.25 |
| Delivery time (days) | 7 | 10 | 21 | Lower is better | 0.20 |
| Contract length (months) | 6 | 12 | 24 | Lower is better (flexibility) | 0.15 |

**Concession sequencing rule (set by James):** Offer delivery time flexibility first. Move on contract length before price. Payment terms are last concession. Never concede on walk-away terms — block and escalate.

**Escalation trigger:** If agreement not reached in 5 rounds, or if supplier requests human contact, surface to James for manual handling.

**Note on asymmetry:** James has configured the bot to weight price highest (0.40). Maria weights payment terms highest (0.35). This means the zone of possible agreement exists — the bot can trade payment speed for a lower unit price, and both parties come out ahead of their status quo. That trade-off is what the bot should surface, and what the supplier UI should make visible to Maria.

---

## Dual Trust Architecture

The system must build trust on two fronts simultaneously — and these cannot conflict:

| Front | Who | Fear | What Builds Trust |
|-------|-----|------|-------------------|
| **Supplier trust** | Maria | Bot is incompetent, process is theater | Genuine concessions, transparent trade-offs, plain language, respect for her constraints |
| **Operator trust** | James | Bot is uncontrollable, deviates from strategy | Strict limit enforcement, full audit trail, explainable decisions, aggregate analytics |

**The tension:** What builds Maria's trust (the bot shows flexibility, moves on her priorities) can trigger James's fear (the bot is giving things away). The resolution is that the bot's flexibility is **configured** by James — when the bot offers Maria better payment terms in exchange for lower price, it's executing James's trade-off weights, not improvising. Both parties' trust is built by the same underlying fact: the system behaves deterministically according to explicit rules.

This dual-trust architecture is Pactum's core product thesis, and demonstrating awareness of it in the submission is the highest-value signal a candidate can send.

---

## Research Sources

Sources supporting the operator persona's context and behavior model:

- **Pactum enterprise customers and metrics:** Walmart pilot (64-68% agreement rate, 90% supplier satisfaction, ~11-day turnaround), Maersk, Honeywell, Novartis, Tetra Pak, Otto Group, Linde, Henkel, Coupang. Series C: $54M (June 2025), $100M+ total, 50+ enterprise customers, 489% spend growth.
- **Tail-spend economics:** 50% of suppliers, 5% of spend, up to 70% of admin costs. 5-20% savings opportunity (Deloitte). Routine and Leverage Kraljic quadrants are Pactum's primary targets.
- **Procurement automation governance:** Enterprise procurement requires audit trails, policy enforcement, and VP-level explainability. Configuration fidelity is a procurement control requirement, not a UX preference.
- **Category manager role:** Responsible for supplier segmentation, term strategy, and savings delivery against quarterly targets. Time is the binding constraint, not willingness to negotiate.

### Source Links
- [Pactum AI Contract Negotiations — Thunderbird/ASU Case Study](https://thunderbird.asu.edu/thought-leadership/journals-case-series/case-series-listing/pactums-ai-contract-negotiations)
- [Negotiating With A Chatbot: Walmart — Talking Logistics](https://talkinglogistics.com/2023/05/01/negotiating-with-a-chatbot-a-walmart-procurement-case-study/)
- [Pactum $54M Series C — ITKeyMedia](https://itkey.media/pactum-secures-usd-54m-of-series-c-funding-to-expand-ai-procurement-platform/)
- [Tail Spend Management — Sievo](https://sievo.com/blog/what-is-tail-spend)
- [Kraljic Matrix — CIPS](https://www.cips.org/intelligence-hub/supplier-relationship-management/kraljic-matrix)
- [How AI Is Reshaping Supplier Negotiations — HBR](https://hbr.org/2025/07/how-ai-is-reshaping-supplier-negotiations)
- [Brave New Procurement Deals — ScienceDirect](https://www.sciencedirect.com/science/article/pii/S1478409225000214)
