---
id: F02
domain: finance
category: Core banking
title: Accounts, ledgers, and double-entry
slug: accounts-ledgers-and-double-entry
order: 2
---

The ledger is the product. An account is a named bucket on that ledger with a customer, a currency, a product, and a set of allowed operations. Double-entry is how you stay honest: every posting has a matching set of legs that sum to zero. Systems that keep a running balance in a single column and "fix it" with jobs will eventually pay someone twice or show money that does not exist.

## Concept

**Chart of accounts and customer accounts.** The bank's own GL (cash, settlement, suspense, income) is not the same as a customer's current account, but they meet on every payment. A customer credit is a bank liability increase. Design both, or you will reconcile forever.

**Posting.** A transaction is a set of entries: debit A, credit B, maybe a fee leg, maybe a tax leg. It has a unique id, a value date, a booking date, and a state (pending, posted, reversed). Reversal is a new transaction that offsets, not a delete.

**Balance.** Booked balance, available balance, and hold/reserve are different numbers. A card authorization reduces available without yet posting. If you have one integer called `balance`, you cannot run cards.

**Interest and EOD.** Accrual is a batch or a continuous function of balances and product rules. End-of-day is a cut, not a vibe. After the cut, value-dated backposts are exceptions with a name.

## Design implications

Idempotency keys on every inbound instruction. Payment networks retry. Your own API clients retry. The ledger must say "this instruction already posted" without a second movement.

Concurrency: two legs of a transfer must not both pass an available-balance check that assumed the full amount. Serialize per account or use a reservation.

Multi-currency is not a display flag. It is books per currency plus an FX trade when you convert. "Store everything in USD and multiply" will fail the audit and the customer.

Suspense accounts are a product. When matching fails, money still has to sit somewhere owned. A queue without a GL account is how cash goes missing.

## Trade-offs

| Approach | When it wins | Cost / risk |
|---|---|---|
| Double-entry ledger with holds | Any real deposit or card | More work than a wallet table |
| Single-balance wallet | A closed-loop points scheme | You cannot explain a dispute or a regulator |
| Eventually consistent balances | Never for money | You will pay twice |

Ask how available balance is computed under an open authorization, how a retry is keyed, and which GL the fee lands on. Those three answers are the core. Everything else is a channel.
