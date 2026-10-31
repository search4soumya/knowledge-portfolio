---
id: I03
domain: insurance
category: Risk and claims
title: Underwriting and risk selection
slug: underwriting-and-risk-selection
order: 3
---

Underwriting is the decision to accept, modify, or refuse a risk, and on what terms. It is not a credit-card authorization. It can take seconds for a simple auto quote or weeks for a commercial property. The business goal is a book you are willing to pay claims on, not a conversion rate you are willing to show a growth slide.

## Concept

**Appetite.** What the carrier wants to write: geographies, occupancies, limits, prohibited classes. Appetite is a product of capital, reinsurance, and experience. Encode it as rules and referral reasons, not as a tribal document in a shared drive.

**Information.** Applications, photos, inspections, motor records, credit-based insurance scores where lawful, loss runs, IoT, and third-party data. Every source has a cost, a latency, and a consent. A model that requires a data source you cannot pull in the quote path is a model for referrals, not for instant bind.

**Decision.** Clear, refer, or decline. Referrals go to a human with a file and a clock. Conditions (higher deductible, an exclusion, a required alarm) are part of the decision. The decision must be explainable enough for a complaint and a regulator.

**Reinsurance and facultative.** Large or unusual risks may need a reinsurer to say yes before you bind. That is an underwriting dependency, not an accounting entry after the fact.

## Design implications

Straight-through processing is a path, not a religion. Measure the percent that binds without a human, and the loss ratio of that slice separately. If STP is cheaper to sell and worse to pay, you automated the wrong thing.

Keep the underwriting file. Years later a claim will ask "what did we know at bind?" If the third-party score is gone and the application was overwritten, you cannot defend the decision.

Bias and regulated inputs matter. Some jurisdictions restrict how you use credit, gender, or territory. The model pipeline is a compliance surface. Feature stores without a legal review are a future consent order.

## Trade-offs

| Approach | When it wins | Cost / risk |
|---|---|---|
| Rules plus optional model, with referral | Most personal lines | You must maintain the rules |
| Model-only instant bind | High volume, low limit, strong data | Drift, fairness, and a surprise loss ratio |
| Human-only | Complex commercial | Slow; inconsistent; unscalable |

Ask what appetite blocks a bind, what the STP rate is by product, and whether you can reconstruct the file for a policy bound last year. Those answers are underwriting architecture.
