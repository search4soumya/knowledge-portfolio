---
id: F04
domain: finance
category: Payments
title: Payment rails and settlement
slug: payment-rails-and-settlement
order: 4
---

A payment is an instruction to move value between accounts that may live at different institutions. The rail is the network that carries the instruction and the settlement is when the money becomes irrevocable between banks. Instant to the customer is not the same as settled between banks. Architects who collapse those two times will write balances they cannot fund.

## Concept

**Instruction versus settlement.** The customer sees "sent." The bank has a claim on another bank or on a central bank account. ACH/NACHA-style batch, Faster Payments / RTP / UPI-style real time, wires (SWIFT, Fedwire, TARGET), and internal book transfers are different rails with different irrevocability and cutoffs.

**Clearing and settlement.** Clearing is matching and netting. Settlement is the movement on the settlement institution's books. Deferred net settlement can hide a large daylight exposure. Real-time gross settlement removes that exposure and costs liquidity.

**Scheme rules.** Each rail has message formats, return codes, windows for recall, and liability for fraud. Your state machine must match the scheme, not a generic "pending/success/fail." A return on day two is a first-class event, not an error log.

**Liquidity.** To settle, you need funds or credit at the correspondent or the central bank. Treasury cares about the position. A popular instant-pay product can drain the settlement account. That is a product limit, not only a scale limit.

## Design implications

Map every outbound payment to a scheme message and a ledger posting. Inbound payments need posting plus a reconciliation to the settlement file. Unmatched inbound sits in suspense (F02).

Idempotency is end to end: your instruction id, the scheme id, and the end-to-end id the customer sees. Store all three.

Sanctions and AML screening sit on the instruction *before* you release to the rail when the rules say so. After release, you have a recall problem, not a block problem.

## Trade-offs

| Approach | When it wins | Cost / risk |
|---|---|---|
| One orchestration layer, many rails | A bank that must offer choice | You must not invent a generic status |
| Single rail | A focused product | You will still need returns and reconciliation |
| Pretend internal transfer equals scheme instant | Demo | You cannot pay someone at another bank |

Draw one outbound instant payment and one inbound batch credit, including a return and a reconciliation break. If settlement cash is not on the diagram, the design is a messenger, not a payment system.
