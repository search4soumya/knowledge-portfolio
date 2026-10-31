---
id: T06
domain: telecom
category: Customer and charging
title: Product catalog and order-to-activate
slug: product-catalog-and-order-to-activate
order: 6
---

A telecom product is a commercial offer that must become a live technical service. The catalog is the commercial language. Order management is the factory that translates an offer into work: reserve a number, ship a SIM, create a core subscription, set a charging plan, book a technician, update inventory. Most "digital transformation" programs fail here, not in the app UI.

## Concept

**Commercial catalog versus technical catalog.** The commercial catalog has offers, bundles, prices, and eligibility ("this 5G unlimited is only for postpaid in these cities"). The technical catalog has service specs and resource specs: an APN, a QoS profile, a GPON port, a voicemail box. A product offering maps to one or more service specs. If you let marketing edit the technical spec, you will ship offers the network cannot fulfill.

**Order capture and decompose.** The order is the customer intent. Decomposition explodes it into service orders and resource orders. "Family plan plus a fiber add-on" is not one API call to the core. It is a tree of tasks with dependencies: credit check, number reservation, SIM logistics, provisioning, and billing start date.

**Activation / provisioning.** Southbound adapters talk to the core, IMS, charging, email, and the access vendor. Each adapter must be idempotent. A retry after a timeout is normal. Two SIMs for one order is an incident.

**Fallout.** Tasks fail. Fallout management is a first-class queue, not an email to a hero. Jeopardy management watches SLAs: a fiber order that misses the install window is a different problem from a prepaid eSIM that failed SM-DP+ download.

## Design implications

Do not start billing before the service is usable, unless the contract says so (a delayed start, a backdated corporate order). Do not mark the order Complete because the CRM said Yes while inventory still has no port.

TM Forum-style models (SID, Open APIs) are a shared language, not a religion. Use them where they prevent a second catalog. Ignore the parts that do not match how your factory actually works, and write that down.

The digital channel is an order capture system. It should not own inventory or the core. It should create an order with a correlation id you can follow through every adapter.

## Trade-offs

| Approach | When it wins | Cost / risk |
|---|---|---|
| Explicit decompose-and-activate | Bundles, fiber plus mobile, B2B | Orchestration complexity |
| Channel talks to network directly | One prepaid digital brand | Every new product forks the app |
| One catalog for commercial and technical | Tiny MVNO | Marketing will break provisioning |

In a review, pick one offer and walk the order tree to the last southbound call. If anyone says "the middleware handles it," ask to see the fallout queue and the idempotency key.
