---
id: T08
domain: telecom
category: Operations
title: 5G slicing and digital services
slug: 5g-slicing-and-digital-services
order: 8
---

5G is sold as a platform for other people's products: factory automation, video uplink, a game overlay, a private campus network. Under the slogan are three concrete objects: a slice (an isolated service treatment), a set of network exposure APIs, and a commercial construct that can be billed. If any of the three is missing, you have a trial, not a business.

## Concept

**A slice** is a committed treatment of traffic: latency, isolation, throughput, and sometimes a dedicated UPF or radio scheduler behavior. eMBB, URLLC, and mMTC are marketing names for different treatments. A slice is not a VLAN you create in an afternoon. It is a catalog item that consumes radio, core, and transport capacity, and that must be inventoried and assured like a VPN.

**Network exposure.** NEF and operator APIs let an application request quality, location (with consent), or a device trigger. This is a B2B product with authentication, quotas, and an audit log. It is also a privacy and fraud surface. Location for a logistics fleet is not location for an arbitrary app.

**Private and hybrid 5G.** A campus may run a local UPF and a local RAN with the public core, or a standalone private core. The join to IT (identity, firewalls, OT networks) is the real project. The radio is rarely the long pole.

**Digital services** on the consumer side — content, devices, insurance, cloud storage — are BSS products that may never touch a new slice. They still need catalog, charging, and care. Do not staff a "5G platform" team to launch a video bundle.

## What architects get wrong

Slicing without a product owner who can say no will produce fifty slices and no isolation. Isolation has a cost in radio and in operations. Start with a small number of slice types and a clear eligibility rule.

An API that changes QoS must have a charging consequence and an admission check. Otherwise a partner will request premium treatment for every session.

Lawful intercept, roaming, and emergency still apply. A slice for a factory does not get to skip them if the same IMSI can also use the public network.

## Trade-offs

| Approach | When it wins | Cost / risk |
|---|---|---|
| Few well-defined slice types | You can sell, assure, and staff them | Some enterprise RFPs will want a custom slice |
| Unlimited per-customer slices | A lab | Ops and radio scheduling collapse |
| Exposure APIs with a contract and a quota | Partners you can bill | You become an API platform, with abuse and versioning |

In a review, ask which catalog item, which inventory object, which charging event, and which KPI define the slice. If you only have a 3GPP diagram, you are not ready to sell it.
