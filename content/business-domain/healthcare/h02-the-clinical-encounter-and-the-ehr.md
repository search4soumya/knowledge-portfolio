---
id: H02
domain: healthcare
category: Clinical
title: The clinical encounter and the EHR
slug: the-clinical-encounter-and-the-ehr
order: 2
---

The encounter is the atomic business event of provider care: a visit, an admission, a telehealth session, an emergency stay. The EHR is the system of record for what happened in that encounter and for the longitudinal chart around it. Almost every other healthcare product is either writing into this record, reading it, or billing from it.

## Concept

**Chart versus encounter.** The chart is the person over time: problems, allergies, medications, history, documents. The encounter is a bounded episode with a time, a location, a responsible clinician, and a reason. Orders, notes, and charges hang off the encounter. Analytics that ignore encounter context will mix an ED asthma visit with a scheduled review.

**Documentation.** Notes, problem lists, and flowsheets are simultaneously clinical communication, legal record, and billing evidence. That is why "just a text box" fails. Templates, voice, and ambient scribes are UX. The constraint is who attested what, when, and whether it can be amended with an audit trail.

**Orders and results.** The clinician's intent (order a CBC, a CT, a consult) leaves the EHR and comes back as a result. The loop can take minutes or days. The EHR must show pending versus final, and it must not lose a critical result in an inbox nobody owns.

**Medication.** Prescribing, reconciling, and administering are three different acts. Closed-loop medication in a hospital (order, pharmacy verify, scan at bedside) is a safety system. An outpatient e-prescription is a different network (in the US, often via a network like Surescripts).

## Design implications

Do not replicate the chart in your app "for convenience" unless you have a reconciliation story. Two problem lists will diverge in a week. Prefer write-back to the EHR or a document the EHR will file.

Identity at the EHR is the medical record number plus enterprise MPI. Your consumer login is not that. Matching "same person, two clinics" is a master-patient-index problem with false merges that can harm someone.

Availability and audit are clinical safety properties. A chart that is down during a code, or a chart that cannot say who viewed an HIV result, is not an ordinary SaaS outage.

## Trade-offs

| Approach | When it wins | Cost / risk |
|---|---|---|
| EHR as system of record, others as edge apps | Hospitals, regulated documentation | Vendor APIs are slow and political |
| Best-of-breed with a thin chart | A specialty clinic | Reconciliation and downtime multiply |
| Shadow chart in the startup database | A demo | Harm, liability, and a migration you will lose |

Ask who attests the note, where a critical result is owned, and what happens when the EHR is unreachable for an hour. Those answers are the encounter design.
