---
id: H01
domain: healthcare
category: Clinical
title: How a health system is organized
slug: how-a-health-system-is-organized
order: 1
---

Healthcare looks like one industry from a distance and three businesses up close: **providers** who deliver care, **payers** who finance it, and **patients** (members, consumers) who move between them. Vendors, pharmacies, labs, employers, and regulators sit on the edges. If you design "a healthcare app" without saying which of these you are, you will steal requirements from all of them and satisfy none.

## Concept

**The provider** is a hospital, clinic, physician group, or virtual practice. Its system of record for care is the EHR and the ancillary systems around it (lab, radiology, pharmacy). Its system of record for money is the revenue cycle. A provider cares about the encounter: who was seen, what was done, what must be documented, what can be billed.

**The payer** is an insurer, a national health service, or a self-funded employer plan administered by someone else. Its system of record is the membership and the benefit. It cares about eligibility, medical necessity, claims, and risk. It does not run the operating theatre. It does decide whether a claim is paid.

**The patient** is a person with a clinical history, a set of consents, and usually several identifiers. They are a member to the payer and a patient to each provider. Those are different contracts. A portal that pretends they are one login across every hospital is making a network and a consent claim, not a UI claim.

**Clearinghouses, HIEs, and networks** move transactions and documents between the parties. They are not optional middleware you can replace with a weekend webhook. They exist because no two EHRs and no two payers speak the same dialect, and because a claim is a financial instrument.

## What to keep separate

Clinical truth (the problem list, the meds, the notes) is not billing truth (the coded claim). Eligibility is not an appointment. A National Provider Identifier is not a user account. Employer groups, families, and dependents make membership a graph, not a user table.

When a product says "we sit between payer and provider," name the transaction: eligibility, claim, prior auth, clinical document, payment advice. Each has a standard, a failure mode, and a reconciliation job.

## Trade-offs

| Approach | When it wins | Cost / risk |
|---|---|---|
| Pick one side (provider *or* payer) and go deep | You can name the system of record | You will still need the other side's transactions |
| Build a horizontal "health OS" | You have a network and a legal basis | Identity, consent, and liability explode |
| Treat the patient portal as the EHR | Consumer wellness, not regulated care | Clinicians will not trust it; regulators may not either |

In a review, draw the money and the clinical event as two paths. If they meet only in a slide titled "platform," you do not yet know who is liable when the data is wrong.
