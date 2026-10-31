---
id: H07
domain: healthcare
category: Interop and privacy
title: Privacy, consent, and HIPAA-style controls
slug: privacy-consent-and-hipaa-style-controls
order: 7
---

Health data is both intimate and economically valuable. Privacy rules (HIPAA in the US, and similar regimes elsewhere) are not a footer on a marketing site. They are constraints on who may see a record, for what purpose, and how you prove it later. Consent is more specific than "the user clicked Agree." Break-the-glass, minors, sensitive diagnoses, and research each have different rules.

## Concept

**Minimum necessary and purpose.** Access is justified by a role and a job: treating clinician, billing clerk, researcher, support engineer. A shared "admin" role that can export the chart is a finding, not a convenience. Purpose of use (treatment, payment, operations, research) belongs on the audit event, not only in a policy PDF.

**Consent and authorization.** A patient may allow an HIE to share, refuse a particular provider, or permit a caregiver. Those directives must be evaluated at query time. A FHIR consent resource you never enforce is decoration. Some data (behavioral health, HIV, substance use in some jurisdictions) is extra-protected. Your resource server must know that.

**Break-the-glass.** Emergency access that bypasses a restriction must be loud: reason, notification, later review. Silent bypass is not emergency access. It is a hole.

**Accounting of disclosures and access logs.** You will be asked who viewed a celebrity chart. If your audit log cannot answer by patient, user, time, and purpose, you do not have an audit log. You have application logs.

**De-identification and research.** Removing names is not enough. Quasi-identifiers re-identify. If you run analytics, decide whether you are in a covered entity, a BA agreement, or a de-identified dataset with a published method.

## Design implications

AuthN is not AuthZ. SMART on FHIR and OAuth get a token into the app. The EHR or your API must still enforce patient compartment and category restrictions. Tokens that can read "any Patient" because the developer was in a hurry will become your incident.

BAAs and subprocessors are architecture. Every log vendor, every support laptop, every training environment with copied charts is in scope. Production-like data in a lower environment is a choice you must be able to defend.

Retention and deletion are in tension with the legal medical record. "GDPR erase me" may lose to a retention statute. Encode that conflict as policy, not as a weekend delete job.

## Trade-offs

| Approach | When it wins | Cost / risk |
|---|---|---|
| Role plus patient compartment plus audit | Any real clinical system | Slower features; you will fight "just give me access" |
| Open chart for anyone at the hospital | Never | Snooping and fines |
| De-identified warehouse by default | Analytics | Clinical care cannot use it; re-id risk remains |

In a review, pick a sensitive result and ask who can see it, who is told when someone unexpected sees it, and how long that fact is kept. If those answers live only in legal, engineering will ship the hole.
