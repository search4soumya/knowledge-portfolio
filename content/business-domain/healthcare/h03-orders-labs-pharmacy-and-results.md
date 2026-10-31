---
id: H03
domain: healthcare
category: Clinical
title: Orders, labs, pharmacy, and results
slug: orders-labs-pharmacy-and-results
order: 3
---

Care is a set of orders that leave the EHR and results that must come back. Labs, imaging, pharmacies, and referral targets are separate organizations with their own systems. The business problem is not "send an API." It is a reliable loop with specimen identity, medical necessity, and a human who is responsible if the result is never seen.

## Concept

**The order.** Who ordered what, for which patient, with which indication, under which encounter. An order has a status machine: ordered, collected, in process, resulted, cancelled, rejected. Cancelling after the specimen is in the courier is a different event from never drawing the blood.

**Specimens and studies.** A lab order is not complete without a specimen id. An imaging order is not complete without a study and a report. Mixing the accession number, the order id, and the patient id is how results attach to the wrong person.

**Pharmacy.** Inpatient pharmacy verifies and dispenses against the eMAR. Outpatient pharmacy receives an e-prescription, may ask for a prior authorization, and dispenses. Medication history and formulary checks sit on this path. A "meds module" that only stores a string of drug names is not a pharmacy integration.

**Results and inbox.** A numeric CBC, a pathology narrative, and a radiology impression have different urgency and different viewers. Critical values require a read-back. The product risk is the unread result, not the missing microservice.

## How systems actually move this

HL7 v2 ORM/ORU still carries a huge share of orders and results. FHIR ServiceRequest and DiagnosticReport are the modern shape, often as a facade. Imaging uses DICOM and a PACS/VNA; the report may travel separately from the pixels. Design for both the message and the delayed correction (a preliminary, then a final, then an addendum).

Idempotency is patient safety. A duplicate order can mean a duplicate contrast dose. A duplicate result can look like a trend that is not real. Use the placer and filler order numbers; do not key on "name plus time."

## Trade-offs

| Approach | When it wins | Cost / risk |
|---|---|---|
| EHR-managed interfaces to each ancillary | One inbox, one chart | Every new lab is a project |
| A shared utility / HIE for results | A region with a working network | Consent and incomplete coverage |
| App-to-lab direct | A focused diagnostic product | You now own matching, billing, and critical values |

In a review, follow one CBC from click to inbox, including a cancelled draw and an amended result. If those two exceptions are "phase two," the loop is not designed.
