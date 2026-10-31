---
id: H06
domain: healthcare
category: Interop and privacy
title: "Interoperability: HL7, FHIR, and IHE"
slug: interoperability-hl7-fhir-and-ihe
order: 6
---

Healthcare interoperability is the work of moving clinical and administrative meaning between systems that were not designed to agree. HL7 v2, CDA, FHIR, DICOM, and X12 are not competing fashions. They are the dialects already on the wire. A strategy that says "we will only do FHIR" is a wish. A strategy that maps each workflow to the dialect the other party actually speaks is a design.

## Concept

**HL7 v2** is the workhorse of in-hospital messaging: ADT (admit/discharge/transfer), ORM/ORU (orders/results), DFT (charges). It is pipe-delimited, version-skewed, and everywhere. You will parse it. You will not replace it this year.

**CDA and documents.** Discharge summaries and referral packets are often documents, not tidy resources. They are messy and they are how a specialist actually receives history.

**FHIR** is a resource model (Patient, Encounter, Observation, ServiceRequest) with REST, SMART apps, and bulk export. It is the right shape for new APIs, patient access, and many national programs. It is not automatically populated. Someone must map the EHR's chart into those resources and keep the map honest.

**IHE profiles** (XDS, PIX/PDQ, MHD) describe how documents and identities move in a community. They exist because "PUT a FHIR Bundle" does not settle who is the registry, who is the repository, and how a patient is correlated.

**Administrative EDI** (X12 270/271, 837, 835, and their regional cousins) is how eligibility and claims move. That is interoperability too. Do not hide it in a "we'll add billing later" column.

## Design implications

Identity is the first interop problem. An MPI or a PIX manager, plus an enterprise id, plus a rule for duplicates, comes before the resource model. A perfect FHIR Patient with the wrong person is a safety incident.

Subscriptions and eventing (ADT → update the downstream) need at-least-once delivery and a way to rebuild. Hospitals reboot interface engines. Your consumer must catch up.

Versioning is political. You will support v2.3.1 and FHIR R4 at the same time. Hide that behind your own canonical model only if you are willing to fund the canonical model as a product.

## Trade-offs

| Approach | When it wins | Cost / risk |
|---|---|---|
| Speak the partner's dialect at the edge, canonicalize inside | You must connect to real EHRs | Mapping work never ends |
| FHIR-only | Greenfield and regulated patient access | You will still meet v2 in the hospital |
| Point-to-point every interface | Two systems | The nth interface is unmaintainable |

Ask which event makes a downstream system update, how a missed message is replayed, and which identifier is used to match the patient. If the answer is "the interface engine," ask to see its dead-letter queue.
