---
id: F08
domain: finance
category: Risk and compliance
title: Regulatory capital and operational risk
slug: regulatory-capital-and-operational-risk
order: 8
---

Banks hold capital because assets default, markets move, and operations fail. Regulatory capital is the number a supervisor will accept. Operational risk is the loss from broken processes, people, systems, and external events — including the outage your architecture just made possible. Product teams meet this when a launch is blocked for RWA, or when an incident becomes a loss event that must be booked.

## Concept

**Credit, market, and operational risk.** Credit: the loan may not pay (F03). Market: the position moves (F06). Operational: you paid twice, a vendor failed, a model was wrong, a flood hit the office. Each has a measurement and a capital treatment. Your systems produce the inputs whether you designed them to or not.

**RWA and limits.** Risk-weighted assets turn exposures into a capital demand. Desk and product limits stop a good quarter from becoming an existential one. A new instant-credit product is a limit conversation before it is a sprint.

**Operational risk events.** An outage with customer loss, a processing error, a fraud not stopped, a fine. These are booked losses with a taxonomy. Incident tools that never hand off to a loss database keep the firm blind.

**Model risk.** Credit scores, AML models, and pricing models are models. They need inventory, validation, and monitoring. Shipping a new default model from a notebook into origination is a model-risk event.

## Design implications

Every product should declare the exposures it creates: credit (a balance), market (a position), operational (a process that can fail with a money impact). If the team cannot fill that in, risk will fill it in for them — slowly.

Reconciliation breaks (F02, F04, F06) are operational risk. Design for suspense aging and for a clock that escalates. A silent break is a future loss event.

Change management and access control are capital-relevant in a boring way. A deploy that posts twice is not only an SRE story.

Data lineage for regulatory reports (COREP, local cousins) is an architecture deliverable. If RWA is a spreadsheet fed by a hero, the next product will not fit the report.

## Trade-offs

| Approach | When it wins | Cost / risk |
|---|---|---|
| Product limits plus loss events plus model inventory | A licensed bank | Slower launches, fewer surprises |
| "Risk will review later" | A prototype | Later is a halt |
| Capital as a finance-only warehouse | Never for new products | You will launch something you cannot hold |

Ask what exposure a feature creates, which limit it consumes, and how a processing error becomes a booked loss. If engineering has never seen those objects, the architecture is unfinished — even if the app is beautiful.
