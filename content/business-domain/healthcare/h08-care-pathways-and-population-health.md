---
id: H08
domain: healthcare
category: Clinical
title: Care pathways and population health
slug: care-pathways-and-population-health
order: 8
---

A single encounter is necessary and not sufficient. Pathways and population programs try to manage a condition or a cohort over time: diabetes, discharge follow-up, childhood immunization, a value-based contract. The business shift is from "we documented the visit" to "we are accountable for an outcome and a cost." That shift changes the data you must keep and the workflows you must close.

## Concept

**A pathway or protocol** is a planned sequence: after discharge, call in 48 hours, reconcile meds, see the PCP in seven days. It has enrollments, tasks, owners, and exit criteria. It is a workflow product. If you implement it as a dashboard with no task owner, nothing happens.

**Registries and cohorts.** A population is a query that becomes a list you are willing to act on: members with heart failure and no follow-up, kids overdue for a vaccine. The query is only as good as the identity match and the recency of claims plus clinical data. Stale claims make a confident, wrong list.

**Quality measures and risk.** HEDIS-like measures, readmission rates, and risk scores are how payers and health systems settle value-based contracts. They are computed artifacts with a spec and a measurement year. Treating them as a BI chart you tweak in Looker will lose you the contract.

**Care management.** Nurses and coordinators work queues, outreach, and barriers (transport, language, housing). The system must record attempts, not only outcomes. A closed-loop referral (sent, booked, attended) is more valuable than another risk score.

## Design implications

You need both clinical and claims data, and you will not have both completely. Design for missingness. A pathway that requires a perfect FHIR feed will not run in the first year.

Attribution — which clinician or group owns this patient for this contract — is a political dataset. Put it in a table with effective dates. Do not infer it from the last visit alone.

Outreach channels (SMS, call, portal) are healthcare communications. They inherit consent and urgency rules. A bulk text about a diagnosis is a privacy incident.

## Trade-offs

| Approach | When it wins | Cost / risk |
|---|---|---|
| Task-based pathways with owners | You can move a metric | Staffing; bad tasks create alert fatigue |
| Score-only population dashboards | Exec reporting | No action, no outcome |
| One vendor "population platform" | A health system already standardized | Data rights and lock-in |

Ask who is accountable for the next task on a high-risk patient, what data that task needs, and how you know the task was done. If the architecture is only a warehouse, you have analytics. You do not have a population program.
