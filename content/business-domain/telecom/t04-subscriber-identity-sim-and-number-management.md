---
id: T04
domain: telecom
category: Customer and charging
title: Subscriber identity, SIM, and number management
slug: subscriber-identity-sim-and-number-management
order: 4
---

Telecom identity is a stack of identifiers that look interchangeable in a slide and are not interchangeable in a database. Mixing them is the most common data-quality failure in a BSS/OSS program. A person, a billing account, a subscription, a SIM, a device, and a phone number are six objects. They join in many-to-many ways: a family account, a multi-SIM watch, a number that ports away while the SIM stays, a SIM that is recycled onto a new number.

## Concept

**IMSI / SUPI** is the subscriber identity the core authenticates. It lives on the SIM (or eSIM profile) and in the HSS/UDM. You do not print it on a bill. You do not use it as a CRM primary key. You treat it as a secret-adjacent network credential.

**ICCID** identifies the physical or electronic SIM card / profile. Logistics cares about ICCID: warehouse, activation, eSIM download. The core cares about IMSI. A swap is "this ICCID now carries this IMSI" or "this device now downloads a new profile."

**MSISDN** is the phone number. It is a routing address on the numbering plan, subject to portability. Customers think the number *is* the identity. The network knows it is a mapping that can move to another IMSI tomorrow. Number inventory, port-in, port-out, and golden-number reservation are their own product.

**Account and party.** BSS has a customer (person or organization), one or more billing accounts, and one or more subscriptions (the commercial product instances). A subscription is what you sell. A SIM is what you put in a device so the core will accept attach.

**eSIM and remote provisioning.** The SM-DP+ and SM-DS let you download a profile without a plastic card. That makes activation look like software. It does not remove the need for profile inventory, confirmation codes, and a rule for what happens when a device is lost.

## How the joins fail

Retail wants to search by number. Care wants to search by name. Network wants IMSI. Finance wants account. If your "customer 360" flattens these into one table, portability and multi-SIM will corrupt history. Keep a graph or a set of typed links. Record the time a number left an IMSI. Recycled numbers must not inherit the previous holder's content or call records.

Device identity (IMEI) is a seventh object. It matters for blocklists, financing, and warranty. It is not the subscriber.

## Trade-offs

| Approach | When it wins | Cost / risk |
|---|---|---|
| Typed identities with explicit links | Portability, multi-SIM, B2B | More tables; every API must say which id it means |
| One "subscriber id" for everything | A demo | Port-out, eSIM swap, and family plans break reporting |
| Let the core own the customer | Never | The core does not know credit, KYC, or a bill |

When you design an API, name the identifier in the path. `/subscribers/{msisdn}` is a different resource from `/sims/{iccid}` and `/accounts/{accountId}`. If you cannot say which one a token may access, you do not have an identity model. You have a search box.
