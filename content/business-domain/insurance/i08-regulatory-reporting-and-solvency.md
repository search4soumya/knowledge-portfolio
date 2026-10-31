---
id: I08
domain: insurance
category: Distribution and capital
title: Regulatory reporting and solvency
slug: regulatory-reporting-and-solvency
order: 8
---

Insurers report because they promise to pay in the future. Statutory statements, solvency ratios, conduct reports, and complaint logs are not "compliance extras." They are why the firm is allowed to exist. An architecture that cannot produce a trial balance by product and state will fail the close, and then fail a product launch you thought was an app release.

## Concept

**Statutory versus GAAP / IFRS.** Books differ. Statutory accounting is conservative and local. Management IFRS or GAAP is another lens. You will need mappings, not one ledger that pretends they are the same. Unearned premium, DAC, and reserve triangles show up differently.

**Solvency.** Risk-based capital, Solvency II-style capital, or a local cousin. The inputs are the book, the reserves, the assets, and the reinsurance. Garbage in policy and claims systems becomes a capital number you cannot defend.

**Conduct and market reports.** Complaints, cancellations, declinatures, claims cycle times, and in some markets gender or race analyses. These require operational data with stable codes. A free-text status will not file.

**Privacy and cross-border.** Data residency for policyholders, and restrictions on moving claims documents, belong in the same conversation as solvency. A global SaaS default region can be an unauthorized transfer.

## Design implications

Chart of accounts and product codes must be first-class. Every bind, endorsement, premium, and claim payment should post or be postable. A "we'll journal it monthly from a dump" process is how the close takes three weeks.

Keep a frozen reporting calendar. Restating last quarter because someone fixed a status mapping is a governance event. Version the mappings.

Complaints and conduct need the same party model as distribution and claims. A complaint that cannot find the policy is a second incident.

## Trade-offs

| Approach | When it wins | Cost / risk |
|---|---|---|
| Event-sourced operational data plus a reporting ledger | A carrier that closes on time | Up-front discipline |
| Reconstruct reports from app databases at quarter end | A seed-stage MGA | The first real audit |
| Separate shadow books per country | Local legal entities | No group view; two truths |

Ask which event posts unearned premium, how a reserve change hits solvency, and how a complaint is tied to a policy. If engineering has never seen the statutory mapping, the next product will ship without a place to live on the statement.
