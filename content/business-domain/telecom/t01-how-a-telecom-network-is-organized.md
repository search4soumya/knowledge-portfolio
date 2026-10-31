---
id: T01
domain: telecom
category: Network
title: How a telecom network is organized
slug: how-a-telecom-network-is-organized
order: 1
---

A telecom operator is not one product. It is a factory that sells connectivity: a radio or wire that reaches a person, a core that decides whether that person may use the network, a set of business systems that turn usage into a bill, and an operations stack that keeps the factory running. If you treat "the telco" as a single backend, you will put charging next to radio configuration and wonder why every change needs six approvals.

The useful first cut is four planes.

## Concept

**Access** is how the subscriber attaches: radio (2G through 5G), fiber, cable, or Wi-Fi offload. Access owns spectrum, towers, last-mile fiber, and the physical ports in a central office. It is capital-heavy and geographically local. A design that assumes you can "just add a region" the way a web app adds a cloud region is already wrong.

**The packet and voice core** is the control and user-plane fabric after attach. It authenticates the subscriber, assigns an IP, applies policy, and hands traffic to the internet or to an IMS voice path. In 4G this is EPC. In 5G it is a service-based core. The core is where session state lives, and session state is why a telco outage feels different from a website outage: dropping the session drops the phone.

**BSS** (Business Support Systems) is the commercial face: product catalog, order capture, CRM, charging, billing, collections. BSS answers "what did we sell, to whom, and what do we charge?" It is closer to a retailer plus a bank than to a network.

**OSS** (Operations Support Systems) is the factory floor: inventory of every port and circuit, fault and performance, workforce, and the activation that turns an order into a live service. OSS answers "does the network actually have this, and is it healthy?"

A fifth plane, **digital and partners**, sits on top: apps, content, MVNO wholesale, and enterprise APIs. It is not a replacement for the four planes. It is a new sales channel that still settles into BSS and still consumes capacity from access and core.

## What an architect should keep separate

Identity in the core (IMSI, SUPI, authentication vectors) is not the CRM customer id. A billable account in BSS is not a SIM. A service instance in inventory is not a product offering. Those four objects get joined constantly, and every messy integration in a telco is a join that was never named.

Traffic that must stay on the user plane (a voice bearer, a 5G PDU session) should not be tromboned through a BSS application "so we have one platform." Charging may need a real-time event; it does not need to be in the packet path.

## Trade-offs

| Approach | When it wins | Cost / risk |
|---|---|---|
| Keep BSS, OSS, core, and access as separate systems of record | You can change a price without touching radio; you can upgrade the core without rewriting CRM | You must design the joins and the activation flow |
| One "digital stack" that owns catalog, network, and charging | Greenfield MVNO with a thin leased network | The first regulated product or prepaid balance will force a split |
| Copy a hyperscaler region model onto the RAN | Never | Radio does not fail or scale like a container |

In a review, ask which plane owns the object you are changing. If the answer is "all of them," you do not yet have a design. You have a program.
