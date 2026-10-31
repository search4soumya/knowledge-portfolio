---
id: F07
domain: finance
category: Risk and compliance
title: KYC, AML, and financial crime
slug: kyc-aml-and-financial-crime
order: 7
---

Financial crime controls decide whether you are allowed to keep the banking license. KYC is who the customer is. AML is whether their activity looks like laundering or sanctions evasion. Fraud is whether someone is stealing. They overlap in data and they are not the same workflow. A single "risk score" that blocks onboarding and also files a SAR will make a mess of both jobs.

## Concept

**KYC / CDD / EDD.** Identify the person or the company, the beneficial owners, the expected activity, and the source of funds when required. Refresh when risk or regulation says so. Onboarding is a case, not a form submit. The case must store evidence you can show an examiner.

**Screening.** Sanctions, PEP, and adverse media on onboard and on a periodic and event-driven cycle. Name matching is fuzzy and produces false positives. A human disposition is part of the design. Auto-clearing without a rule you can defend is how you fail an exam.

**Transaction monitoring.** Rules and models on payments, logins, and device. Alerts become cases. Cases may become a suspicious activity report. Tipping off the customer is itself an offense in many jurisdictions. The app must not say "your payment is delayed because we suspect you."

**Fraud.** Authorization-time card fraud, APP / authorized push payment scams, account takeover. Speed matters. The control may block or step-up. Liability and customer reimbursement rules are product rules, not only model scores.

## Design implications

Party identity from F01 is the spine. Screening a payment without a resolved party is noise. Changing a customer's name or address must re-screen.

Keep the case file. Models change. Examiners ask what you did on a date. If the alert payload was overwritten, you have no program.

List management (sanctions lists) is an operational feed with versions. A stale list is a control failure. Treat it like a dependency with an SLO.

Do not reuse the marketing CDP as the KYC store. Purpose limitation and access control are different.

## Trade-offs

| Approach | When it wins | Cost / risk |
|---|---|---|
| Separate KYC cases, TM cases, and fraud, sharing party data | A real bank | More queues; clearer exams |
| One score to rule them all | A demo | You will tip off, over-block, or fail KYC |
| Vendor black box, no case system | Never for long | You cannot explain a decision |

Walk an onboarding hit, a payment alert, and a card-fraud block. If they share one status field and one customer message, the crime program is not designed. It is a boolean.
