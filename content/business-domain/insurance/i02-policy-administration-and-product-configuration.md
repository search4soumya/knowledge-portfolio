---
id: I02
domain: insurance
category: Product and policy
title: Policy administration and product configuration
slug: policy-administration-and-product-configuration
order: 2
---

Policy administration (PAS) is the system of record for the contract. Product configuration is how you define what can be sold without a core rewrite: coverages, questions, rating hooks, forms, and rules. Carriers that cannot configure a new endorsement without a six-month project will lose to someone who can — unless that someone cannot produce a legal form or a statutory report.

## Concept

**Product definition.** A product is a tree of coverages and options, each with eligibility, rating inputs, forms, and underwriting rules. Version it. A policy issued on version 12 of "Homeowners 2024" must keep version 12 for its life, even when version 13 ships. Mid-term endorsements may move versions under a defined rule, not by accident.

**Quote, bind, issue.** Quote is a priced offer. Bind is the moment risk transfers (sometimes with a binder before full issue). Issue produces the policy record, the forms, the bill plan, and the downstream notices. Idempotency at bind is money: two binds is two contracts or a broken sequence number.

**Lifecycle.** Endorsements, renewals, cancellations (flat, pro-rata, short-rate), reinstatements, and out-of-sequence endorsements. Out-of-sequence is the hard one: a change effective last month arrives after a later change. PAS that cannot replay effective-dated transactions will corrupt the contract.

**Forms and correspondence.** The policy jacket, declarations, and state-specific notices are part of the product. Generating the wrong form is a compliance miss. Store what you sent, not only a template id.

## Design implications

Effective dating is the core pattern. Every fact on the policy has a start and an end. As-of queries ("what did we cover on the date of loss?") are the claim system's first question.

Do not let the digital channel own the product model. Let it *call* the product model. Two catalogs — one in the app, one in PAS — will disagree on the first weekend promotion.

Billing may be a separate system (see rating and finance). The policy still owns the bill plan and the cancellation for non-pay. The handshake is a contract: PAS says cancel; billing says the money arrived late; someone must win with an audit trail.

## Trade-offs

| Approach | When it wins | Cost / risk |
|---|---|---|
| Configurable PAS plus versioned products | A carrier that will still exist in ten years | Up-front modeling skill |
| Hard-coded products in the app | One product, one state | The second state is a rewrite |
| Spreadsheet rating next to a thin PAS | An MGA experiment | You cannot reconstruct the issued contract |

Walk a bind, a mid-term endorsement, a renewal, and an out-of-sequence change. If any of those is "we'll handle it in the database," the PAS is not designed.
