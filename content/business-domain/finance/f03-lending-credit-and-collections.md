---
id: F03
domain: finance
category: Core banking
title: Lending, credit, and collections
slug: lending-credit-and-collections
order: 3
---

A loan is a contract that creates an asset on the bank's book and a schedule of obligations for the customer. Origination decides whether to create it. Servicing keeps it. Collections and recovery handle the broken schedule. Credit risk is the reason the asset may not be worth the number you printed. Software that ships "approve in one tap" without a ledger for the loan account is a marketing site.

## Concept

**Origination.** Application, identity, income, bureau, affordability, collateral, offer, and contract. Decisioning is a regulated model plus policy rules. Adverse action must be explainable. The offer has a rate, a term, a fee, and a cooling-off or right to withdraw in many markets.

**The loan account.** Disbursement posts to the ledger. A repayment schedule (amortization, interest-only, balloon, revolving) is a function you must be able to rebuild after a rate change or a restructuring. Accrued interest, fees, and penalty interest are products with rules, not a late cron.

**Limit and revolving.** Cards and overdrafts are limits, not a single disbursement. Available credit is limit minus utilization minus holds. That is the same hold pattern as F02, with a credit-limit object on top.

**Delinquency and collections.** Days past due, stages, notices, forbearance, charge-off, and recovery. Each stage has a communication rule and an accounting rule. Treating collections as a CRM campaign without posting to the loan will desync the book.

## Design implications

The decision file must be kept (similar to insurance underwriting). Fair-lending and model risk will ask what you knew at approval.

Restructuring and hardship are first-class transactions. They change the schedule and sometimes the IFRS 9 stage. A silent "we paused the debit" in ops is how you lose the portfolio view.

Collateral (a house, a car, a guarantee) is a linked object with valuation and insurance. Unsecured consumer credit is simpler and still needs the loan ledger.

## Trade-offs

| Approach | When it wins | Cost / risk |
|---|---|---|
| Loan account in the core plus a decisioning service | A real book | Slower than a fintech demo |
| Marketplace origination, bank holds the asset | Speed, shared risk | Data rights and who owns collections |
| Approve-only app, spreadsheet servicing | A pilot | You cannot sell or provision the book |

Follow a loan from offer to disbursement to a missed payment to a restructure. If any step leaves the ledger, credit risk will invent a second system of record in a spreadsheet named `final_v7`.
