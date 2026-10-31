---
id: I04
domain: insurance
category: Risk and claims
title: Rating, pricing, and actuarial feedback
slug: rating-pricing-and-actuarial-feedback
order: 4
---

Rating is the function that turns risk characteristics into a premium. Pricing is the business decision about that function: what you must charge to meet a loss ratio and a growth target, after expenses, reinsurance, and regulation. Actuarial feedback is how the book teaches the function. If rating is a spreadsheet emailed to engineering, you do not have a pricing system. You have a hope.

## Concept

**Rate plan.** Tables, factors, and algorithms: base rate × relativity for territory, amount, claims history, credit where allowed, discounts. Versioned and filed. In many markets you cannot change a rate without a filing. "We A/B tested a 10 percent discount" can be illegal.

**Rating at quote and at issue.** The premium on the issued policy must be reproducible from the issued characteristics and the rate version. If a later batch job "fixes" premiums, you have a trust problem with customers and with the regulator.

**Usage-based and on-demand.** Telematics, trip-based, and parametric products add a telemetry pipeline and a different rating moment. The rating function still needs a version and an audit. The new failure mode is missing or disputed telemetry.

**Indications and actuals.** Actuaries compare expected loss to actual loss by segment. That loop needs a clean join from policy to premium to claim, with earned premium (not written) as the denominator. Your warehouse model is part of the pricing system.

## Design implications

Treat the rater as a deterministic service: same inputs and version, same premium, no hidden time-of-day dependency. Log the inputs. When a customer asks why the renewal went up, you will need that log.

Separate rating from underwriting rules and from billing. A payment plan (monthly versus annual) changes the customer's cash, not the technical premium, except where fees and installment loads are themselves rated.

Do not let a growth team own a shadow discount in the channel. Every discount is either in the filed rate plan or it is a leak.

## Trade-offs

| Approach | When it wins | Cost / risk |
|---|---|---|
| Versioned rater as a service | Any regulated product | Discipline; slower "experiments" |
| Spreadsheet plus manual load | A pilot | Irreproducible premiums |
| Continuous unfiled discounting | Never, in a filed market | Fines and a book you cannot explain |

Ask how you reproduce last March's premium, how a filing becomes production, and how earned premium is computed for a mid-term endorsement. If those are three teams with three numbers, pricing will fight the book.
