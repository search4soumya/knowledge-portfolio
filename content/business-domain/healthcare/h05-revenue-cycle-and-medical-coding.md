---
id: H05
domain: healthcare
category: Administrative
title: Revenue cycle and medical coding
slug: revenue-cycle-and-medical-coding
order: 5
---

For a provider, revenue cycle is the path from a scheduled visit to cash in the bank. Coding is the translation of clinical work into the language payers will pay. Architects who skip this path build beautiful encounter apps that never get the hospital paid, and then wonder why the CIO will not take the next meeting.

## Concept

**Front of the cycle.** Scheduling, registration, insurance capture, eligibility, estimates, and prior auth. Bad data here becomes a denial later. Patient identity and coverage at registration are financial controls, not clerical niceties.

**Charge capture.** Every billable thing must become a charge: a visit level, a procedure, a supply, a facility fee. Charges come from the EHR, from departmental systems, and from late addenda. A missing charge is leakage. A duplicate charge is a compliance event.

**Coding.** ICD diagnoses, CPT/HCPCS procedures, and in hospitals DRG grouping. Coders (human or assisted) read the documentation and apply rules. The clinical note is the evidence. If the note does not support the code, that is a compliance risk, not a clever optimization.

**Billing, denial, and collections.** Claims go out. Denials come back. Work queues appeal or correct. Patient balances are collected under a different set of rules and tone. Cash posting from remittances closes the loop. Days in A/R is the KPI leadership actually watches.

## Design implications

Do not let a new clinical app create charges unless coding and compliance have a gate. "Automatic coding from the note" is a model with an error rate; someone must own the misses.

Estimates and price transparency are becoming product requirements. They need the same contract and benefit data as adjudication, which the provider does not fully own. Be honest about approximation.

Write-offs, charity care, and bundling rules are ledger events. They need the same discipline as a payment: who approved, which claim, which period.

## Trade-offs

| Approach | When it wins | Cost / risk |
|---|---|---|
| EHR plus a dedicated RCM suite | Health systems | Integration and vendor politics |
| Niche RCM for one specialty | A focused clinic | Hard to expand to inpatient |
| Code everything in the startup | A demo | Audits and denials will find you |

Follow one elective procedure from scheduling to a posted remittance, including a denial and a corrected claim. If your architecture diagram ends at "encounter closed," you have designed half of the provider business.
