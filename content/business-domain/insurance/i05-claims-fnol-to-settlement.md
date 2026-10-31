---
id: I05
domain: insurance
category: Risk and claims
title: "Claims: FNOL to settlement"
slug: claims-fnol-to-settlement
order: 5
---

A claim is the moment the promise is tested. First notice of loss (FNOL) starts a file. Settlement, denial, or recovery ends it. In between sit coverage verification, investigation, reserves, payment, fraud, and often litigation. Claims is an operational system with a financial core. Chat UX does not replace a reserve that is wrong by an order of magnitude.

## Concept

**FNOL.** Who, what, when, where, which policy. The first job is to match a policy that was in force on the date of loss (I02). The second is to capture enough to assign a handler and set an initial reserve. Incomplete FNOL is normal. The file must be able to grow without losing the first story.

**Coverage and liability.** Is this loss in the wording? Who is liable? That can be straight-through for a smashed window or a multi-year argument for a casualty claim. Coverage decisions should be recorded as decisions, not as a status string a developer invented.

**Reserves.** Indemnity and expense reserves change as you learn. They feed solvency and reinsurance. Unauthorized reserve changes are a control failure. A model that suggests a reserve is useful; a model that silently overwrites the handler's number is not.

**Payment and recovery.** Pay the insured, a vendor, a third party. Recover from salvage, subrogation, or a coinsurer. Payments are ledger events with payee verification. Duplicate payments are a classic claims leak.

**Fraud and SIU.** Referral to a special unit is a parallel path, not a tag that freezes the whole file forever without a rule. Document why you referred.

## Design implications

The claims system must read the policy as of the date of loss, including endorsements. A cache of "current policy" will pay or deny wrongly after a mid-term change.

Documents and photos are the work. Object storage plus a file that care and counsel can trust matters more than a new kanban skin. Retention follows legal holds.

Customer status ("we received your photos") is a projection. The system of record is the claim file. Do not let the app invent a happier state than the file.

## Trade-offs

| Approach | When it wins | Cost / risk |
|---|---|---|
| File-centric claims with reserve controls | Any real book | Heavier than a ticket tool |
| Straight-through for small, simple claims | High volume, low severity | Leakage if coverage is assumed |
| One status for customer and handler | Never | You will lie to one of them |

Follow a claim from FNOL through a reserve change, a partial payment, and a subrogation recovery. If any of those is outside the system of record, the financial close will invent a second claims system.
