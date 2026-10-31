---
id: T05
domain: telecom
category: Customer and charging
title: Charging, billing, and prepaid vs postpaid
slug: charging-billing-and-prepaid-vs-postpaid
order: 5
---

Charging is how usage becomes money. Billing is how money becomes a statement, a tax invoice, and a collection action. They are related and they are not the same system. Prepaid lives or dies on real-time charging. Postpaid can tolerate a rated event that lands tonight, but it cannot tolerate a wrong invoice after a regulator has seen it.

## Concept

**Usage events.** The network emits records: data volume, voice minutes, SMS, roaming, a content purchase. Online charging (OCS) reserves or decrements a balance *during* the session. Offline charging (CDR / CHF) writes an event to be rated later. A mature operator does both. A session that only writes a CDR cannot cut a prepaid user at the exact byte.

**Rating.** A rate plan maps an event to a charge: included bucket, then overage, then a roaming multiplier, then a discount from a promotion. Rating must be deterministic and versioned. The plan that was in force at the start of the call is the plan you rate, not the plan marketing published this afternoon.

**Balance and wallet.** Prepaid is a wallet with reservation: grant 10 MB, use 8, release 2, or top up. Postpaid is a credit limit plus a bill cycle. Convergent charging puts both in one engine so a hybrid plan (pass plus bill) does not need two products. The wallet is a ledger. Treat it like one: idempotent top-ups, an audit trail, no silent repair jobs.

**Billing and invoicing.** Aggregation of rated events, recurring charges, taxes, discounts, and dunning. Invoice presentment, dispute, and adjustment are legal documents in many markets. A "regenerate invoice" button is a controlled financial action, not a cache refresh.

## What breaks in software

If the core cannot reach the charging function, you must choose: fail open (free data, fraud) or fail closed (angry prepaid users). That choice is a product and risk decision. Document it.

Roaming and interconnect add partner settlement. Your retail rate is not the wholesale rate you pay the visited network. Those two numbers live in different contracts. Do not store only one.

Idempotency matters. A retried recharge must not double the wallet. A retried CDR must not double the bill. Use a unique event id from the network, not "insert if it looks new."

## Trade-offs

| Approach | When it wins | Cost / risk |
|---|---|---|
| Real-time OCS for all | Prepaid, fair-use, sponsored data | Session path now depends on charging latency |
| Offline rate-and-bill | Simple postpaid, low fraud | Leakage; you discover abuse at month end |
| One convergent engine | Hybrid plans, one customer view | A billing defect can stall attach if you couple too tightly |

Ask where the balance is stored, what happens when charging is unreachable for 30 seconds, and which id makes a recharge safe to retry. Those three answers are the charging design.
