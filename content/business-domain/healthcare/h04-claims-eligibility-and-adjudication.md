---
id: H04
domain: healthcare
category: Administrative
title: Claims, eligibility, and adjudication
slug: claims-eligibility-and-adjudication
order: 4
---

On the payer side, the claim is the financial event that says "pay for this care." Before the claim comes eligibility and often prior authorization. After the claim comes adjudication: allowed amount, member liability, denial, or a request for more information. These transactions are standardized for a reason. Inventing a prettier JSON that does not map to them will isolate you from every clearinghouse and every provider billing office.

## Concept

**Eligibility.** Is this person a member on this date, under this plan, for this service? The answer can be yes with a copay, yes with a deductible remaining, or no. Real-time eligibility is a query, not a cache of last month's roster. A roster (834-style enrollment) is how membership is maintained. Both exist.

**Prior authorization.** Some services need permission before they are delivered. Auth is a clinical plus contractual workflow: guidelines, attachments, a clock, and an appeal. Treating it as a boolean flag in the EHR is how you get care delayed and a claim denied.

**The claim.** A professional or institutional claim lists the patient, the provider, the diagnoses, the procedures or revenue codes, the dates, and the charges. It is a legal request for money. It has a unique claim id, a frequency (original, replacement, void), and a submission path through a clearinghouse.

**Adjudication.** The payer applies benefits, contracts, medical policy, coordination of benefits, and fraud edits. The output is an explanation: paid, denied, pended. The remittance (835-style) tells the provider how to post the payment. Member-facing EOBs are a different presentment of the same decision.

## Design implications

Idempotency and replacements matter. Providers resubmit. A replacement is not a second claim for the same money unless you designed it that way. Store the payer claim control number and the provider's claim id.

Adjudication is not a single rules engine you rewrite each year. It is a pipeline: member match, provider contract, benefit, medical policy, pricing, accumulators (deductible and out-of-pocket). Accumulators are a concurrency problem: two claims in one day must not both think the deductible is unused.

Eligibility at the point of care is an SLA. If it is wrong, the clinic collects the wrong amount and someone eats the difference.

## Trade-offs

| Approach | When it wins | Cost / risk |
|---|---|---|
| Standards-based transactions plus a clearinghouse | Any real payer or provider | Ugly messages; you must learn the standard |
| Proprietary APIs only | A closed network you own | You cannot meet providers where they bill |
| Nightly batch eligibility | Tiny closed panel | Point-of-care will be wrong |

Ask which accumulator is the system of record, how a replacement claim is keyed, and what the clinic sees when eligibility is stale. Those three are the claims design.
