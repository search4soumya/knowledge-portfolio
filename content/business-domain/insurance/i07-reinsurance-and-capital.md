---
id: I07
domain: insurance
category: Distribution and capital
title: Reinsurance and capital
slug: reinsurance-and-capital
order: 7
---

Reinsurance is insurance for insurers. Capital is what remains when you subtract liabilities from assets, under rules a regulator will argue about. Together they decide how much risk you can write. Software teams meet this when a product cannot launch because treaty capacity is full, or when a catastrophe model says last week's growth consumed the year.

## Concept

**Treaty versus facultative.** A treaty covers a class of business automatically (for example, 40 percent of every homeowner policy in a region). Facultative is a one-off for a large risk. Treaties have inuring rules, exclusions, and bordereaux — the reports you send the reinsurer. If you cannot produce a bordereau, you cannot collect.

**Proportional and excess of loss.** Proportional shares premium and loss. Excess of loss pays when a loss or an event exceeds a retention. Event definition (what is one occurrence, what is one hours clause) is a data problem as much as a legal one. Your claim and policy systems must tag losses so a cat event can be assembled.

**Ceded premium and recoverables.** Ceding is a ledger: you owe premium to the reinsurer; they owe you recoveries. Those balances age. A recoverable you cannot document is not capital.

**Capital and appetite.** Rating agencies and regulators look at capital versus risk. Growing a new slice of the book consumes capital even if the app is cheap to run. Product launch is a capital allocation, not only an engineering milestone.

## Design implications

Attach reinsurance rules as close to bind and to claim as you can. A warehouse-only view is too late for facultative referral and too late for event aggregation during a storm.

Catastrophe events need a grouping key and a per-risk limit rollup. Geospatial data on the policy (a location that is actually the risk location) is not optional decoration for a property book.

Do not bury ceded amounts as a journal nobody can query by policy. You will need policy-level ceded for some contracts and for disputes.

## Trade-offs

| Approach | When it wins | Cost / risk |
|---|---|---|
| Policy and claim tags that feed a reinsurance system | A carrier with real treaties | Extra fields at bind and FNOL |
| Year-end spreadsheet | A tiny book | You will miss recoveries and surprise the CRO |
| Fronting without data rights | An MGA that wants speed | The paper carrier will eventually demand the bordereau |

Ask how a bound policy is ceded, how a cat event is assembled from claims, and who can see recoverables aging. If the answer is "actuarial has a model," ask whether operations can run the treaty without that one person.
